import os
import pandas as pd
from typing import Dict, Any, List, Tuple

DEFAULT_WORKBOOK_PATH = "Indian_Refinery_Near_Miss_Datasets.xlsx"

EXPECTED_COLUMNS = [
    "Near_Miss_ID",
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
    "Immediate_Cause",
    "Potential_Consequence",
    "Risk_Level",
    "Corrective_Action",
    "Action_Status",
    "High_Potential_Near_Miss"
]

def locate_workbook(filepath: str = DEFAULT_WORKBOOK_PATH) -> str:
    """Locates and validates the Excel workbook path."""
    if os.path.exists(filepath):
        return os.path.abspath(filepath)
    # Search in current working directory or subdirectories
    for root, _, files in os.walk("."):
        for f in files:
            if f.lower() == DEFAULT_WORKBOOK_PATH.lower() or f.endswith(".xlsx"):
                return os.path.abspath(os.path.join(root, f))
    raise FileNotFoundError(f"Workbook {filepath} could not be found.")

def inspect_workbook(filepath: str = DEFAULT_WORKBOOK_PATH) -> Dict[str, Any]:
    """Inspects all sheets in the Excel workbook and generates profiling metadata."""
    path = locate_workbook(filepath)
    excel_file = pd.ExcelFile(path)
    sheet_names = excel_file.sheet_names
    
    sheet_profiles = {}
    total_records = 0
    
    for sheet in sheet_names:
        df = excel_file.parse(sheet)
        n_rows, n_cols = df.shape
        missing_dict = df.isnull().sum().to_dict()
        dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        dup_count = int(df.duplicated().sum())
        
        sheet_profiles[sheet] = {
            "num_rows": n_rows,
            "num_cols": n_cols,
            "columns": list(df.columns),
            "data_types": dtypes_dict,
            "missing_values": missing_dict,
            "duplicate_count": dup_count
        }
        if sheet != "00_Summary":
            total_records += n_rows

    profile = {
        "workbook_filename": os.path.basename(path),
        "workbook_full_path": path,
        "sheet_names": sheet_names,
        "num_sheets": len(sheet_names),
        "total_raw_observation_records": total_records,
        "sheet_profiles": sheet_profiles
    }
    return profile

def load_raw_dataset(filepath: str = DEFAULT_WORKBOOK_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads all observation sheets into a single combined DataFrame, adding 'source_sheet' for auditing.
    Also returns the summary sheet DataFrame if available.
    """
    path = locate_workbook(filepath)
    excel_file = pd.ExcelFile(path)
    sheet_names = excel_file.sheet_names
    
    dfs = []
    summary_df = None
    
    for sheet in sheet_names:
        df = excel_file.parse(sheet)
        if sheet == "00_Summary":
            summary_df = df
            continue
        
        df['source_sheet'] = sheet
        dfs.append(df)
        
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df, summary_df

if __name__ == "__main__":
    prof = inspect_workbook()
    print(f"Workbook: {prof['workbook_filename']}, Sheets: {prof['num_sheets']}, Raw records: {prof['total_raw_observation_records']}")
