    def _prepare_response_data(self, df: pd.DataFrame, mapped_cols: Dict[str, str]) -> Optional[pd.DataFrame]:
        """Prepare response data for analysis by identifying response pairs.
        
        Args:
            df (pd.DataFrame): The DataFrame to analyze
            mapped_cols (Dict[str, str]): Column mapping
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with response data or None if no responses found
        """
        ts_col = mapped_cols['timestamp']
        contact_col = mapped_cols['phone_number']
        type_col = mapped_cols['message_type']

        # Ensure DataFrame is sorted by contact, then timestamp
        df_sorted = df.sort_values(by=[contact_col, ts_col]).copy()

        # Get previous message info within each contact group
        df_sorted['prev_ts'] = df_sorted.groupby(contact_col)[ts_col].shift(1)
        df_sorted['prev_type'] = df_sorted.groupby(contact_col)[type_col].shift(1)

        # Identify response rows: current is 'sent', previous was 'received'
        is_response = (
            (df_sorted[type_col] == 'sent') &
            (df_sorted['prev_type'] == 'received')
        )

        # Filter potential response rows
        response_candidates = df_sorted[is_response].copy()

        if response_candidates.empty:
            self.logger.warning("No response pairs found to calculate response times.")
            return None

        # Calculate response time in seconds
        response_candidates['response_time_seconds'] = \
            (response_candidates[ts_col] - response_candidates['prev_ts']).dt.total_seconds()

        # Filter out negative/zero response times
        response_details_df = response_candidates[response_candidates['response_time_seconds'] > 0].copy()

        if response_details_df.empty:
            self.logger.warning("No valid positive response times found after filtering.")
            return None
            
        return response_details_df
        
    def _calculate_time_aggregations(self, response_details_df: pd.DataFrame, mapped_cols: Dict[str, str]) -> Dict[str, Union[Optional[float], Dict[str, float], Dict]]:
        """Calculate time-based aggregations from response data.
        
        Args:
            response_details_df (pd.DataFrame): Response data with response time information
            mapped_cols (Dict[str, str]): Column mapping for standard field names
            
        Returns:
            Dict containing time aggregation statistics with keys:
                - average_response_time_seconds (Optional[float]): Mean response time
                - median_response_time_seconds (Optional[float]): Median response time
                - response_time_distribution (Dict): Distribution statistics
                - per_contact_average (Dict[str, float]): Average by contact
                - by_hour_average (Dict[int, float]): Average by hour
                - by_day_average (Dict[str, float]): Average by day name
        """
        ts_col = mapped_cols['timestamp']
        contact_col = mapped_cols['phone_number']

        all_times = response_details_df['response_time_seconds']

        # Calculate basic statistics
        result = {
            "average_response_time_seconds": all_times.mean() if not all_times.empty else None,
            "median_response_time_seconds": all_times.median() if not all_times.empty else None,
            "response_time_distribution": calculate_distribution_stats(all_times),
            "per_contact_average": response_details_df.groupby(contact_col)['response_time_seconds'].mean().to_dict()
        }

        # Add time-based aggregations
        response_details_df['sent_hour'] = response_details_df[ts_col].dt.hour
        response_details_df['sent_day_name'] = response_details_df[ts_col].dt.day_name()

        result["by_hour_average"] = response_details_df.groupby('sent_hour')['response_time_seconds'].mean().to_dict()
        result["by_day_average"] = response_details_df.groupby('sent_day_name')['response_time_seconds'].mean().to_dict()
        
        return result
        
    def _process_response_outliers(self, response_details_df: pd.DataFrame, mapped_cols: Dict[str, str]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Process outliers in response time data.
        
        Args:
            response_details_df (pd.DataFrame): Response data with calculated response times
            mapped_cols (Dict[str, str]): Column mapping for standard field names
            
        Returns:
            Tuple[pd.DataFrame, List[Dict[str, Any]]]: 
                - Updated DataFrame with outlier flags
                - List of outliers with their details
        """
        ts_col = mapped_cols['timestamp']
        contact_col = mapped_cols['phone_number']
        all_times = response_details_df['response_time_seconds']
        
        # Find outliers
        outlier_indices = calculate_outliers_iqr(all_times)
        response_details_df['is_outlier'] = False
        response_details_df.loc[outlier_indices, 'is_outlier'] = True
        outliers_df = response_details_df[response_details_df['is_outlier']]
        
        # Create outlier list
        outliers_list = []
        if not outliers_df.empty:
            # Select desired columns
            outlier_columns = [contact_col, 'prev_ts', ts_col, 'response_time_seconds', 'is_outlier']
            valid_columns = [col for col in outlier_columns if col in outliers_df.columns]
            
            if valid_columns:
                outliers_list = outliers_df[valid_columns].rename(columns={
                    'prev_ts': 'received_ts',
                    ts_col: 'sent_ts'
                }).to_dict('records')
                
                # Format timestamps
                for outlier in outliers_list:
                    received_ts_val = outlier.get('received_ts')
                    sent_ts_val = outlier.get('sent_ts')
                    outlier['received_ts'] = received_ts_val.isoformat() if pd.notna(received_ts_val) else None
                    outlier['sent_ts'] = sent_ts_val.isoformat() if pd.notna(sent_ts_val) else None
        
        return response_details_df, outliers_list
