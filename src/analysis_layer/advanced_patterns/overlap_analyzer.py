"""
Overlap Analyzer Module
------------------
Analyze overlapping communication patterns.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from ...logger import get_logger
from ..statistical_utils import get_cached_result, cache_result

logger = get_logger("overlap_analyzer")

class OverlapAnalyzer:
    """Analyzer for overlapping communication patterns."""

    def __init__(self):
        """Initialize the overlap analyzer."""
        self.last_error = None

    def analyze_overlaps(self, df: pd.DataFrame, 
                        time_window_minutes: float = 5.0) -> Dict[str, Any]:
        """Analyze overlapping communications within a time window.

        Args:
            df: DataFrame containing phone records
            time_window_minutes: Time window in minutes to consider communications as overlapping

        Returns:
            Dictionary of overlap analysis results
        """
        if df is None or df.empty:
            error = "Cannot analyze overlaps with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframe
            cache_key = f"overlaps_{hash(str(df.shape))}_{time_window_minutes}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Ensure timestamp is datetime
            if 'timestamp' not in df.columns:
                error = "DataFrame missing timestamp column"
                self.last_error = error
                logger.error(error)
                return {"error": error}
                
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Check if phone_number column exists
            if 'phone_number' not in df.columns:
                error = "DataFrame missing phone_number column"
                self.last_error = error
                logger.error(error)
                return {"error": error}
            
            # Detect contact overlaps
            contact_overlaps = self._detect_contact_overlaps(df, time_window_minutes)
            
            # Detect group conversations
            group_conversations = self._detect_group_conversations(df, time_window_minutes)
            
            # Detect rapid switching
            rapid_switching = self._detect_rapid_switching(df, time_window_minutes)
            
            # Combine results
            results = {
                "contact_overlaps": contact_overlaps,
                "group_conversations": group_conversations,
                "rapid_switching": rapid_switching
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error analyzing overlaps: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _detect_contact_overlaps(self, df: pd.DataFrame, 
                               time_window_minutes: float) -> List[Dict[str, Any]]:
        """Detect overlapping communications with different contacts.

        Args:
            df: DataFrame containing phone records
            time_window_minutes: Time window in minutes to consider communications as overlapping

        Returns:
            List of detected contact overlaps
        """
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Initialize list of overlaps
        overlaps = []
        
        # Convert time window to timedelta
        time_window = timedelta(minutes=time_window_minutes)
        
        # Iterate through messages
        for i in range(len(df_sorted) - 1):
            current_msg = df_sorted.iloc[i]
            current_time = current_msg['timestamp']
            current_contact = current_msg['phone_number']
            
            # Look for overlapping messages with different contacts
            for j in range(i + 1, len(df_sorted)):
                next_msg = df_sorted.iloc[j]
                next_time = next_msg['timestamp']
                next_contact = next_msg['phone_number']
                
                # Check if within time window
                time_diff = (next_time - current_time).total_seconds() / 60  # in minutes
                
                if time_diff <= time_window_minutes:
                    # Check if different contact
                    if next_contact != current_contact:
                        # Create overlap record
                        overlap = {
                            "start_time": current_time,
                            "end_time": next_time,
                            "duration_minutes": time_diff,
                            "contacts": [current_contact, next_contact],
                            "description": f"Overlap between {current_contact} and {next_contact} ({time_diff:.1f} minutes)"
                        }
                        
                        # Add message types if available
                        if 'message_type' in current_msg and 'message_type' in next_msg:
                            overlap["message_types"] = [current_msg['message_type'], next_msg['message_type']]
                        
                        overlaps.append(overlap)
                else:
                    # No more overlaps for this message
                    break
        
        # Remove duplicates (same contact pairs)
        unique_overlaps = []
        seen_pairs = set()
        
        for overlap in overlaps:
            # Sort contacts to ensure consistent ordering
            sorted_contacts = tuple(sorted(overlap["contacts"]))
            
            if sorted_contacts not in seen_pairs:
                seen_pairs.add(sorted_contacts)
                unique_overlaps.append(overlap)
        
        return unique_overlaps

    def _detect_group_conversations(self, df: pd.DataFrame, 
                                  time_window_minutes: float) -> List[Dict[str, Any]]:
        """Detect potential group conversations involving multiple contacts.

        Args:
            df: DataFrame containing phone records
            time_window_minutes: Time window in minutes to consider as part of the same conversation

        Returns:
            List of detected group conversations
        """
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Initialize list of conversations
        conversations = []
        
        # Convert time window to timedelta
        time_window = timedelta(minutes=time_window_minutes)
        
        # Initialize current conversation
        current_conversation = None
        
        # Iterate through messages
        for i, (_, msg) in enumerate(df_sorted.iterrows()):
            current_time = msg['timestamp']
            current_contact = msg['phone_number']
            
            if current_conversation is None:
                # Start a new conversation
                current_conversation = {
                    "start_time": current_time,
                    "end_time": current_time,
                    "contacts": {current_contact},
                    "messages": [{"time": current_time, "contact": current_contact}]
                }
            else:
                # Check if this message is part of the current conversation
                time_diff = (current_time - current_conversation["end_time"]).total_seconds() / 60
                
                if time_diff <= time_window_minutes:
                    # Add to current conversation
                    current_conversation["end_time"] = current_time
                    current_conversation["contacts"].add(current_contact)
                    current_conversation["messages"].append({"time": current_time, "contact": current_contact})
                else:
                    # End current conversation if it has multiple contacts
                    if len(current_conversation["contacts"]) >= 3:
                        duration = (current_conversation["end_time"] - current_conversation["start_time"]).total_seconds() / 60
                        
                        group_conv = {
                            "start_time": current_conversation["start_time"],
                            "end_time": current_conversation["end_time"],
                            "duration_minutes": duration,
                            "contacts": list(current_conversation["contacts"]),
                            "message_count": len(current_conversation["messages"]),
                            "description": f"Group conversation with {len(current_conversation['contacts'])} contacts over {duration:.1f} minutes"
                        }
                        
                        conversations.append(group_conv)
                    
                    # Start a new conversation
                    current_conversation = {
                        "start_time": current_time,
                        "end_time": current_time,
                        "contacts": {current_contact},
                        "messages": [{"time": current_time, "contact": current_contact}]
                    }
        
        # Check the last conversation
        if current_conversation and len(current_conversation["contacts"]) >= 3:
            duration = (current_conversation["end_time"] - current_conversation["start_time"]).total_seconds() / 60
            
            group_conv = {
                "start_time": current_conversation["start_time"],
                "end_time": current_conversation["end_time"],
                "duration_minutes": duration,
                "contacts": list(current_conversation["contacts"]),
                "message_count": len(current_conversation["messages"]),
                "description": f"Group conversation with {len(current_conversation['contacts'])} contacts over {duration:.1f} minutes"
            }
            
            conversations.append(group_conv)
        
        return conversations

    def _detect_rapid_switching(self, df: pd.DataFrame, 
                              time_window_minutes: float) -> List[Dict[str, Any]]:
        """Detect rapid switching between contacts.

        Args:
            df: DataFrame containing phone records
            time_window_minutes: Time window in minutes to consider as rapid switching

        Returns:
            List of detected rapid switching instances
        """
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Initialize list of rapid switching instances
        rapid_switches = []
        
        # Need at least 3 messages to detect switching
        if len(df_sorted) < 3:
            return rapid_switches
        
        # Initialize current sequence
        current_sequence = {
            "start_time": df_sorted.iloc[0]['timestamp'],
            "end_time": df_sorted.iloc[0]['timestamp'],
            "contacts": [df_sorted.iloc[0]['phone_number']],
            "messages": [{"time": df_sorted.iloc[0]['timestamp'], "contact": df_sorted.iloc[0]['phone_number']}]
        }
        
        # Iterate through messages
        for i in range(1, len(df_sorted)):
            current_msg = df_sorted.iloc[i]
            current_time = current_msg['timestamp']
            current_contact = current_msg['phone_number']
            
            # Check if this message is within the time window of the sequence
            time_diff = (current_time - current_sequence["end_time"]).total_seconds() / 60
            
            if time_diff <= time_window_minutes:
                # Add to current sequence
                current_sequence["end_time"] = current_time
                current_sequence["contacts"].append(current_contact)
                current_sequence["messages"].append({"time": current_time, "contact": current_contact})
            else:
                # Check if the sequence shows rapid switching
                if self._is_rapid_switching(current_sequence):
                    duration = (current_sequence["end_time"] - current_sequence["start_time"]).total_seconds() / 60
                    unique_contacts = len(set(current_sequence["contacts"]))
                    
                    switch = {
                        "start_time": current_sequence["start_time"],
                        "end_time": current_sequence["end_time"],
                        "duration_minutes": duration,
                        "message_count": len(current_sequence["messages"]),
                        "unique_contacts": unique_contacts,
                        "contacts": list(set(current_sequence["contacts"])),
                        "description": f"Rapid switching between {unique_contacts} contacts over {duration:.1f} minutes"
                    }
                    
                    rapid_switches.append(switch)
                
                # Start a new sequence
                current_sequence = {
                    "start_time": current_time,
                    "end_time": current_time,
                    "contacts": [current_contact],
                    "messages": [{"time": current_time, "contact": current_contact}]
                }
        
        # Check the last sequence
        if self._is_rapid_switching(current_sequence):
            duration = (current_sequence["end_time"] - current_sequence["start_time"]).total_seconds() / 60
            unique_contacts = len(set(current_sequence["contacts"]))
            
            switch = {
                "start_time": current_sequence["start_time"],
                "end_time": current_sequence["end_time"],
                "duration_minutes": duration,
                "message_count": len(current_sequence["messages"]),
                "unique_contacts": unique_contacts,
                "contacts": list(set(current_sequence["contacts"])),
                "description": f"Rapid switching between {unique_contacts} contacts over {duration:.1f} minutes"
            }
            
            rapid_switches.append(switch)
        
        return rapid_switches

    def _is_rapid_switching(self, sequence: Dict[str, Any]) -> bool:
        """Determine if a sequence shows rapid switching between contacts.

        Args:
            sequence: Dictionary containing sequence information

        Returns:
            True if the sequence shows rapid switching, False otherwise
        """
        # Need at least 3 messages
        if len(sequence["messages"]) < 3:
            return False
        
        # Need at least 2 unique contacts
        unique_contacts = set(sequence["contacts"])
        if len(unique_contacts) < 2:
            return False
        
        # Check for alternating pattern
        alternating_count = 0
        for i in range(1, len(sequence["contacts"])):
            if sequence["contacts"][i] != sequence["contacts"][i-1]:
                alternating_count += 1
        
        # Calculate percentage of alternating messages
        alternating_percentage = (alternating_count / (len(sequence["contacts"]) - 1)) * 100
        
        # Consider rapid switching if at least 50% of messages alternate between contacts
        return alternating_percentage >= 50

    def analyze_contact_clusters(self, df: pd.DataFrame, 
                               time_window_minutes: float = 30.0) -> Dict[str, Any]:
        """Analyze clusters of contacts that are frequently contacted together.

        Args:
            df: DataFrame containing phone records
            time_window_minutes: Time window in minutes to consider contacts as being contacted together

        Returns:
            Dictionary of contact cluster analysis
        """
        if df is None or df.empty:
            error = "Cannot analyze contact clusters with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframe
            cache_key = f"contact_clusters_{hash(str(df.shape))}_{time_window_minutes}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Ensure timestamp is datetime
            if 'timestamp' not in df.columns or 'phone_number' not in df.columns:
                error = "DataFrame missing required columns"
                self.last_error = error
                logger.error(error)
                return {"error": error}
                
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Sort by timestamp
            df_sorted = df.sort_values('timestamp')
            
            # Find contact pairs that occur within the time window
            contact_pairs = defaultdict(int)
            
            # Iterate through messages
            for i in range(len(df_sorted) - 1):
                current_msg = df_sorted.iloc[i]
                current_time = current_msg['timestamp']
                current_contact = current_msg['phone_number']
                
                # Look for messages within the time window
                for j in range(i + 1, len(df_sorted)):
                    next_msg = df_sorted.iloc[j]
                    next_time = next_msg['timestamp']
                    next_contact = next_msg['phone_number']
                    
                    # Check if within time window
                    time_diff = (next_time - current_time).total_seconds() / 60
                    
                    if time_diff <= time_window_minutes:
                        # Skip if same contact
                        if next_contact != current_contact:
                            # Create sorted pair to avoid duplicates
                            pair = tuple(sorted([current_contact, next_contact]))
                            contact_pairs[pair] += 1
                    else:
                        # No more messages within time window
                        break
            
            # Convert to list of pairs with counts
            pair_list = [{"contacts": list(pair), "count": count} for pair, count in contact_pairs.items()]
            
            # Sort by count (descending)
            pair_list.sort(key=lambda x: x["count"], reverse=True)
            
            # Find contact clusters (groups of contacts frequently contacted together)
            clusters = self._find_contact_clusters(pair_list)
            
            # Analyze cluster characteristics
            cluster_analysis = []
            for i, cluster in enumerate(clusters):
                # Calculate cluster metrics
                contacts = cluster["contacts"]
                
                # Filter messages involving cluster contacts
                cluster_msgs = df_sorted[df_sorted['phone_number'].isin(contacts)]
                
                if not cluster_msgs.empty:
                    # Calculate time distribution
                    hour_counts = cluster_msgs['timestamp'].dt.hour.value_counts().sort_index().to_dict()
                    day_counts = cluster_msgs['timestamp'].dt.day_name().value_counts().to_dict()
                    
                    # Calculate message type distribution if available
                    type_distribution = {}
                    if 'message_type' in cluster_msgs.columns:
                        type_distribution = cluster_msgs['message_type'].value_counts().to_dict()
                    
                    cluster_analysis.append({
                        "cluster_id": i + 1,
                        "contacts": contacts,
                        "size": len(contacts),
                        "message_count": len(cluster_msgs),
                        "hour_distribution": hour_counts,
                        "day_distribution": day_counts,
                        "type_distribution": type_distribution,
                        "description": f"Cluster of {len(contacts)} contacts with {len(cluster_msgs)} messages"
                    })
            
            # Combine results
            results = {
                "contact_pairs": pair_list[:10],  # Top 10 pairs
                "contact_clusters": clusters,
                "cluster_analysis": cluster_analysis
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error analyzing contact clusters: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _find_contact_clusters(self, contact_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find clusters of contacts based on pair frequencies.

        Args:
            contact_pairs: List of contact pairs with counts

        Returns:
            List of contact clusters
        """
        # Need at least 3 pairs to form meaningful clusters
        if len(contact_pairs) < 3:
            return []
        
        # Create a graph of contacts
        contact_graph = defaultdict(set)
        
        # Add edges for pairs with count >= 2
        for pair in contact_pairs:
            if pair["count"] >= 2:
                contact1, contact2 = pair["contacts"]
                contact_graph[contact1].add(contact2)
                contact_graph[contact2].add(contact1)
        
        # Find connected components (clusters)
        clusters = []
        visited = set()
        
        for contact in contact_graph:
            if contact not in visited:
                # Start a new cluster
                cluster = set()
                queue = [contact]
                
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        cluster.add(current)
                        
                        # Add neighbors to queue
                        for neighbor in contact_graph[current]:
                            if neighbor not in visited:
                                queue.append(neighbor)
                
                # Only include clusters with at least 3 contacts
                if len(cluster) >= 3:
                    # Calculate cluster strength (average pair count)
                    strength = 0
                    pair_count = 0
                    
                    for pair in contact_pairs:
                        contact1, contact2 = pair["contacts"]
                        if contact1 in cluster and contact2 in cluster:
                            strength += pair["count"]
                            pair_count += 1
                    
                    avg_strength = strength / max(1, pair_count)
                    
                    clusters.append({
                        "contacts": list(cluster),
                        "size": len(cluster),
                        "strength": avg_strength,
                        "description": f"Cluster of {len(cluster)} contacts with average strength {avg_strength:.1f}"
                    })
        
        # Sort clusters by size (descending)
        clusters.sort(key=lambda x: x["size"], reverse=True)
        
        return clusters
