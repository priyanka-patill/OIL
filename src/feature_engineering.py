import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from typing import Tuple, Dict, Any, List

# Strict exclusion list - source_sheet and leakage features MUST NEVER be passed to model training
EXCLUDED_FEATURES = [
    "source_sheet",
    "Near_Miss_ID",
    "Potential_Consequence",  # Direct target proxy
    "Risk_Level",             # Post-investigation leakage
    "Corrective_Action",      # Post-investigation leakage
    "Action_Status",          # Post-investigation leakage
    "High_Potential_Near_Miss"# Target column
]

SAFE_TEXT_FEATURE = "Near_Miss_Description"

SAFE_CATEGORICAL_FEATURES = [
    "Refinery_Unit",
    "Equipment_ID",
    "Work_Type",
    "Department"
]

SAFE_FACTOR_FEATURES = [
    "PPE_NonCompliance",
    "Supervisor_Negligence",
    "Maintenance_Delay_or_Issue",
    "Repeated_Issue_Ignored"
]

SAFE_NUMERICAL_FEATURES = [
    "Previous_Similar_Reports"
]

FEATURE_AUDIT_TABLE = [
    {"Feature": "Near_Miss_Description", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Primary worker text report logged at event time."},
    {"Feature": "PPE_NonCompliance", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Operational precursor flag available at entry."},
    {"Feature": "Supervisor_Negligence", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Operational precursor flag available at entry."},
    {"Feature": "Maintenance_Delay_or_Issue", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Operational precursor flag available at entry."},
    {"Feature": "Repeated_Issue_Ignored", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Operational precursor flag available at entry."},
    {"Feature": "Previous_Similar_Reports", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Historical site record count available at entry."},
    {"Feature": "Work_Type", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Operational task classification."},
    {"Feature": "Department", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Reporting unit metadata."},
    {"Feature": "Refinery_Unit", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Location metadata."},
    {"Feature": "Equipment_ID", "Prediction_Time": "Yes", "Leakage_Risk": "None", "Decision": "USE", "Reason": "Equipment identifier metadata."},
    {"Feature": "source_sheet", "Prediction_Time": "No", "Leakage_Risk": "Critical", "Decision": "EXCLUDE", "Reason": "Encodes target (12_High_Potential = SIF). Audit only."},
    {"Feature": "Potential_Consequence", "Prediction_Time": "No", "Leakage_Risk": "Critical", "Decision": "EXCLUDE", "Reason": "100% target proxy. Assigned post event."},
    {"Feature": "Risk_Level", "Prediction_Time": "No", "Leakage_Risk": "High", "Decision": "EXCLUDE", "Reason": "Critical risk only in SIF. Post-investigation rating."},
    {"Feature": "Corrective_Action", "Prediction_Time": "No", "Leakage_Risk": "High", "Decision": "EXCLUDE", "Reason": "Formulated post HSE investigation."},
    {"Feature": "Action_Status", "Prediction_Time": "No", "Leakage_Risk": "High", "Decision": "EXCLUDE", "Reason": "HSE tracking status post event."}
]

def load_processed_data(data_path: str = "data/processed/cleaned_near_miss_dataset.parquet") -> pd.DataFrame:
    """Loads the processed dataset generated in Part 1A."""
    if not os.path.exists(data_path):
        csv_fallback = "data/processed/cleaned_near_miss_dataset.csv"
        if os.path.exists(csv_fallback):
            return pd.read_csv(csv_fallback)
        raise FileNotFoundError(f"Processed dataset not found at {data_path} or {csv_fallback}")
    return pd.read_parquet(data_path)

def create_train_val_test_splits(
    df: pd.DataFrame, 
    target_col: str = "High_Potential_Near_Miss",
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Creates stratified 70% Train, 15% Validation, 15% Test splits.
    Ensures source_sheet is kept only as audit metadata in the dataframes.
    """
    assert abs(train_size + val_size + test_size - 1.0) < 1e-5, "Splits must sum to 1.0"
    
    y = df[target_col]
    
    # First split: Train (70%) vs Temp (30%)
    temp_size = val_size + test_size
    train_df, temp_df = train_test_split(
        df, 
        test_size=temp_size, 
        stratify=y, 
        random_state=random_state
    )
    
    # Second split: Val (15% overall -> 50% of temp) vs Test (15% overall -> 50% of temp)
    val_rel_size = val_size / temp_size
    val_df, test_df = train_test_split(
        temp_df, 
        test_size=(1.0 - val_rel_size), 
        stratify=temp_df[target_col], 
        random_state=random_state
    )
    
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)

def build_tfidf_vectorizer() -> TfidfVectorizer:
    """
    Builds a reproducible TF-IDF vectorizer for text features.
    Negations and safety terms are preserved intact.
    """
    return TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        lowercase=True
    )

def build_structured_transformer() -> ColumnTransformer:
    """
    Builds a ColumnTransformer for structured features (Categorical One-Hot + Scaled Numerical + Factors).
    """
    cat_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    num_transformer = StandardScaler()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', cat_transformer, SAFE_CATEGORICAL_FEATURES),
            ('num', num_transformer, SAFE_NUMERICAL_FEATURES),
            ('factor', 'passthrough', SAFE_FACTOR_FEATURES)
        ],
        remainder='drop'
    )
    return preprocessor

def prepare_feature_matrices(
    train_df: pd.DataFrame, 
    val_df: pd.DataFrame, 
    test_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Prepares fitted feature matrices for Configurations A, B, and C strictly fitting transformers on Train data only.
    """
    y_train = train_df['High_Potential_Near_Miss'].values
    y_val = val_df['High_Potential_Near_Miss'].values
    y_test = test_df['High_Potential_Near_Miss'].values
    
    # 1. Configuration A — Text Only
    tfidf = build_tfidf_vectorizer()
    X_train_text = tfidf.fit_transform(train_df[SAFE_TEXT_FEATURE].fillna(""))
    X_val_text = tfidf.transform(val_df[SAFE_TEXT_FEATURE].fillna(""))
    X_test_text = tfidf.transform(test_df[SAFE_TEXT_FEATURE].fillna(""))
    
    # 2. Configuration B — Structured Only
    struct_trans = build_structured_transformer()
    X_train_struct = struct_trans.fit_transform(train_df)
    X_val_struct = struct_trans.transform(val_df)
    X_test_struct = struct_trans.transform(test_df)
    
    # 3. Configuration C — Text + Structured Combined
    from scipy.sparse import hstack, csr_matrix
    X_train_comb = hstack([X_train_text, csr_matrix(X_train_struct)]).tocsr()
    X_val_comb = hstack([X_val_text, csr_matrix(X_val_struct)]).tocsr()
    X_test_comb = hstack([X_test_text, csr_matrix(X_test_struct)]).tocsr()
    
    # Extract feature names for explainability
    text_feature_names = list(tfidf.get_feature_names_out())
    struct_feature_names = list(struct_trans.get_feature_names_out())
    comb_feature_names = text_feature_names + struct_feature_names
    
    return {
        "y_train": y_train, "y_val": y_val, "y_test": y_test,
        "config_a_text": {
            "X_train": X_train_text, "X_val": X_val_text, "X_test": X_test_text,
            "feature_names": text_feature_names, "transformer": tfidf
        },
        "config_b_struct": {
            "X_train": X_train_struct, "X_val": X_val_struct, "X_test": X_test_struct,
            "feature_names": struct_feature_names, "transformer": struct_trans
        },
        "config_c_combined": {
            "X_train": X_train_comb, "X_val": X_val_comb, "X_test": X_test_comb,
            "feature_names": comb_feature_names, "transformers": (tfidf, struct_trans)
        }
    }
