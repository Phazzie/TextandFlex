# Metacognitive Custom Instructions for Phone Records Analyzer Development

## Reasoning Process Guidance

1. **Pattern Analysis First, Implementation Second**

   - Before writing any analytical function, first reason about what patterns in communication data it should detect
   - Consider both obvious patterns (frequency) and non-obvious patterns (timing clusters, reciprocity imbalances)
   - Articulate how the pattern might manifest in different scenarios before coding detection logic

2. **Multi-perspective Analysis**

   - For each analysis component, consider at least three perspectives:
     - Time-based: How patterns appear across different timeframes
     - Contact-based: How patterns differ between contacts
     - Direction-based: How sent vs. received communications reveal different insights
   - Explicitly evaluate which perspective yields the most valuable insights for each feature

3. **Decision Tree Reasoning**
   - When designing analytical logic, use branching decision trees to handle pattern variations
   - First branch: Is there sufficient data for meaningful analysis?
   - Second branch: Does the pattern appear in aggregate or only with specific contacts?
   - Third branch: Is the pattern consistent over time or episodic?
   - Fourth branch: Does the pattern correlate with other detected patterns?

## Implementation Strategy

4. **Evidence Threshold Framework**

   - Implement tiered confidence levels for detected patterns:
     - Level 1: Statistically significant deviation (p < 0.05)
     - Level 2: Repeated pattern across multiple time periods
     - Level 3: Pattern validated across multiple analytical dimensions
   - Code should explicitly track and expose confidence levels in its output

5. **Counter-hypothesis Testing**

   - For each detection algorithm, implement a counter-check that attempts to disprove the pattern
   - If implementing a "suspicious timing" detector, also implement logic to evaluate innocent explanations
   - Design functions to return both the detected pattern AND the strength of alternative explanations

6. **Incremental Complexity Model**
   - Begin with base statistical analysis (counts, averages, distributions)
   - Add correlation detection as a separate layer
   - Add anomaly detection as a third layer
   - Add pattern classification as a fourth layer
   - Each layer should be independently testable and usable

## Code Organization Principles

7. **Explainability Architecture**

   - Structure code so that it can explain WHY it reached conclusions, not just what it found
   - Maintain analysis audit trails showing what data points influenced each conclusion
   - Design separation between raw analysis, pattern detection, and interpretation components

8. **Edge Case Anticipation**

   - Explicitly handle these scenarios in all analytical functions:
     - Very small datasets (< 10 entries)
     - Very large datasets (> 10,000 entries)
     - Heavy outliers (communications 3+ standard deviations from mean)
     - Missing data periods
     - Conflicting pattern indicators

9. **Adaptive Analysis Depth**
   - Implement progressive analysis depth based on data characteristics
   - Initial quick-scan functions that determine if deeper analysis is warranted
   - Computational resource allocation proportional to pattern significance
   - Early termination for unpromising analytical paths

## Communication of Results

10. **Insight Hierarchy Framework**

    - Structure results to clearly distinguish between:
      - Primary insights (high confidence, significant findings)
      - Secondary insights (moderate confidence or significance)
      - Exploratory observations (potential patterns requiring more data)
    - Code should tag findings according to this hierarchy

11. **Contextual Significance Assessment**

    - For each detected pattern, evaluate significance in the specific context of communication records
    - Distinguish between statistical significance and practical significance
    - Calculate and expose effect sizes, not just p-values or binary detection
    - Compare patterns against baseline communication behavior

12. **Interconnected Finding Network**
    - Design components that track relationships between different detected patterns
    - Implement graph structures that link related findings
    - Create mechanisms to identify reinforcing or contradicting patterns
    - Build visualizations that expose pattern networks, not just individual insights

## Code Quality Requirements

13. **Analytical Validation Standards**

    - Every statistical function must include validity checks for its assumptions
    - Data transformations must preserve analytical integrity
    - Randomization tests to validate pattern detection against null hypothesis
    - Cross-validation for all predictive components

14. **Transparent Limitations**
    - Each analysis function should explicitly document its limitations
    - Code should detect when it's operating outside its reliable parameters
    - Functions should gracefully degrade rather than produce misleading results
    - Error bounds should be calculated and exposed for all significant findings
