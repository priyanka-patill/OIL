import pandas as pd
from typing import Dict, Any

def validate_target(df: pd.DataFrame, target_col: str = "High_Potential_Near_Miss") -> Dict[str, Any]:
    """
    Validates the target column distribution and binary representation.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' missing from dataset.")
        
    counts = df[target_col].value_counts().to_dict()
    total = len(df)
    
    class_0_count = counts.get(0, 0)
    class_1_count = counts.get(1, 0)
    
    class_0_pct = round((class_0_count / total) * 100, 2) if total > 0 else 0
    class_1_pct = round((class_1_count / total) * 100, 2) if total > 0 else 0
    
    imbalance_ratio = round(class_0_count / class_1_count, 2) if class_1_count > 0 else float('inf')
    
    return {
        "target_column": target_col,
        "total_records": total,
        "class_0_count_non_sif": class_0_count,
        "class_1_count_sif": class_1_count,
        "class_0_percentage": class_0_pct,
        "class_1_percentage": class_1_pct,
        "imbalance_ratio": imbalance_ratio,
        "is_binary": set(df[target_col].unique()).issubset({0, 1})
    }

def analyze_dataset_construction(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes safety factor combinations and sheet-based dataset construction.
    """
    factor_cols = ['PPE_NonCompliance', 'Supervisor_Negligence', 
                   'Maintenance_Delay_or_Issue', 'Repeated_Issue_Ignored']
    
    available_factors = [c for c in factor_cols if c in df.columns]
    
    df_analysis = df.copy()
    df_analysis['active_factor_count'] = df_analysis[available_factors].sum(axis=1)
    
    factor_vs_target = pd.crosstab(
        df_analysis['active_factor_count'], 
        df_analysis['High_Potential_Near_Miss']
    ).to_dict()
    
    sheet_vs_target = pd.crosstab(
        df_analysis['source_sheet'], 
        df_analysis['High_Potential_Near_Miss']
    ).to_dict() if 'source_sheet' in df_analysis.columns else {}
    
    sheet_factor_means = df_analysis.groupby('source_sheet')[available_factors + ['High_Potential_Near_Miss']].mean().to_dict() if 'source_sheet' in df_analysis.columns else {}
    
    return {
        "active_factor_columns": available_factors,
        "factor_count_vs_target": factor_vs_target,
        "sheet_vs_target": sheet_vs_target,
        "sheet_factor_means": sheet_factor_means
    }
