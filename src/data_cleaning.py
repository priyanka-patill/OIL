import os
import re
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict

# Explicit list of columns allowed to be model feature candidates (source_sheet MUST NEVER BE INCLUDED)
MODEL_FEATURE_COLUMNS = [
    "Date",
    "Refinery_Unit",
    "Equipment_ID",
    "Work_Type",
    "Department",
    "Near_Miss_Description",
    "PPE_NonCompliance",
    "Supervisor_Negligence",
    "Maintenance_Delay_or_Issue",
    "Repeated_Issue_Ignored",
    "Previous_Similar_Reports",
    "Immediate_Cause"
]

AUDIT_ONLY_COLUMNS = [
    "source_sheet",
    "Near_Miss_ID"
]

# Post-investigation columns (flagged for Part 1B decision)
POST_INVESTIGATION_COLUMNS = [
    "Potential_Consequence",
    "Risk_Level",
    "Corrective_Action",
    "Action_Status"
]

TARGET_COLUMN = "High_Potential_Near_Miss"

SAFETY_NEGATION_TERMS = {
    "not", "no", "without", "bypassed", "failed", "ignored", 
    "continued", "never", "unable", "unavailable", "unlocked", 
    "un-isolated", "non-compliant", "overdue", "defective"
}

def clean_text_description(text: str) -> str:
    """
    Cleans Near_Miss_Description text while preserving safety-critical terms and negations.
    """
    if pd.isna(text) or not str(text).strip():
        return ""
    
    cleaned = str(text).strip()
    # Normalize multiple whitespaces to single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def normalize_boolean(val) -> bool:
    """Normalizes boolean inputs (True/False, 1/0, Yes/No, Y/N)."""
    if pd.isna(val):
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ['true', '1', 'yes', 'y']:
        return True
    if s in ['false', '0', 'no', 'n']:
        return False
    return bool(val)

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies reproducible cleaning rules to the raw combined dataset.
    """
    cleaned_df = df.copy()
    
    # 1. Standardize column names (strip whitespace)
    cleaned_df.columns = [col.strip() for col in cleaned_df.columns]
    
    # 2. Text cleaning (Near_Miss_Description)
    if 'Near_Miss_Description' in cleaned_df.columns:
        cleaned_df['Near_Miss_Description'] = cleaned_df['Near_Miss_Description'].apply(clean_text_description)
    
    # 3. Categorical normalization (strip leading/trailing whitespace)
    cat_cols = ['Refinery_Unit', 'Equipment_ID', 'Work_Type', 'Department', 
                'Immediate_Cause', 'Potential_Consequence', 'Risk_Level', 
                'Corrective_Action', 'Action_Status']
    for col in cat_cols:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
    
    # 4. Boolean normalization for factor columns
    factor_cols = ['PPE_NonCompliance', 'Supervisor_Negligence', 
                   'Maintenance_Delay_or_Issue', 'Repeated_Issue_Ignored']
    for col in factor_cols:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].apply(normalize_boolean)
            
    # 5. Numerical normalization (Previous_Similar_Reports)
    if 'Previous_Similar_Reports' in cleaned_df.columns:
        cleaned_df['Previous_Similar_Reports'] = pd.to_numeric(cleaned_df['Previous_Similar_Reports'], errors='coerce').fillna(0).astype(int)
        
    # 6. Date normalization
    if 'Date' in cleaned_df.columns:
        cleaned_df['Date'] = pd.to_datetime(cleaned_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
    # 7. Target normalization (High_Potential_Near_Miss -> binary 0/1)
    if TARGET_COLUMN in cleaned_df.columns:
        cleaned_df[TARGET_COLUMN] = cleaned_df[TARGET_COLUMN].apply(normalize_boolean).astype(int)
        
    return cleaned_df

def save_processed_dataset(cleaned_df: pd.DataFrame, output_dir: str = "data/processed") -> Tuple[str, str]:
    """Saves the cleaned dataset to CSV and Parquet formats."""
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, "cleaned_near_miss_dataset.csv")
    parquet_path = os.path.join(output_dir, "cleaned_near_miss_dataset.parquet")
    
    cleaned_df.to_csv(csv_path, index=False)
    cleaned_df.to_parquet(parquet_path, index=False)
    
    return csv_path, parquet_path
