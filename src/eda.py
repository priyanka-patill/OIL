import os
import matplotlib
matplotlib.use('Agg') # Headless backend for command execution
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List

# Premium design styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

COLOR_PALETTE = ['#2b5c8f', '#d9534f', '#428bca', '#5cb85c', '#f0ad4e', '#5bc0de', '#6f42c1']

def generate_eda_plots(df: pd.DataFrame, output_dir: str = "reports/figures") -> List[str]:
    """
    Generates 21 distinct, high-quality EDA charts saved as PNG images in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    df_plot = df.copy()
    if 'High_Potential_Near_Miss' in df_plot.columns:
        df_plot['Target_Label'] = df_plot['High_Potential_Near_Miss'].map({0: 'Non-SIF (0)', 1: 'SIF / High-Pot (1)'})
    
    # Calculate description length
    if 'Near_Miss_Description' in df_plot.columns:
        df_plot['desc_len'] = df_plot['Near_Miss_Description'].astype(str).str.len()
        df_plot['word_count'] = df_plot['Near_Miss_Description'].astype(str).str.split().str.len()

    # Chart 1: Target Distribution
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.countplot(data=df_plot, x='Target_Label', hue='Target_Label', palette=['#2b5c8f', '#d9534f'], legend=False, ax=ax)
    ax.set_title("1. Target Distribution (High_Potential_Near_Miss)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Target Class", fontweight='bold')
    ax.set_ylabel("Record Count", fontweight='bold')
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())} ({p.get_height()/len(df_plot)*100:.1f}%)", 
                    (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                    ha='center', va='center', fontsize=11, color='white', fontweight='bold')
    plt.tight_layout()
    f1 = os.path.join(output_dir, "01_target_distribution.png")
    fig.savefig(f1, dpi=300)
    plt.close(fig)
    generated_files.append(f1)

    # Chart 2: Records by Source Sheet
    fig, ax = plt.subplots(figsize=(10, 5))
    sheet_order = df_plot['source_sheet'].value_counts().index if 'source_sheet' in df_plot.columns else []
    sns.countplot(data=df_plot, y='source_sheet', hue='source_sheet', order=sheet_order, palette='Blues_r', legend=False, ax=ax)
    ax.set_title("2. Raw Record Distribution by Source Sheet", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Record Count", fontweight='bold')
    ax.set_ylabel("Source Sheet", fontweight='bold')
    plt.tight_layout()
    f2 = os.path.join(output_dir, "02_records_by_source_sheet.png")
    fig.savefig(f2, dpi=300)
    plt.close(fig)
    generated_files.append(f2)

    # Chart 3: Risk Level Distribution
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.countplot(data=df_plot, x='Risk_Level', hue='Risk_Level', order=['Low', 'Medium', 'High', 'Critical'], palette='YlOrRd', legend=False, ax=ax)
    ax.set_title("3. Overall Risk Level Distribution", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Risk Level", fontweight='bold')
    ax.set_ylabel("Count", fontweight='bold')
    plt.tight_layout()
    f3 = os.path.join(output_dir, "03_risk_level_distribution.png")
    fig.savefig(f3, dpi=300)
    plt.close(fig)
    generated_files.append(f3)

    # Chart 4: Work Type Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df_plot, y='Work_Type', hue='Work_Type', palette='viridis', legend=False, ax=ax)
    ax.set_title("4. Work Type Distribution", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Count", fontweight='bold')
    ax.set_ylabel("Work Type", fontweight='bold')
    plt.tight_layout()
    f4 = os.path.join(output_dir, "04_work_type_distribution.png")
    fig.savefig(f4, dpi=300)
    plt.close(fig)
    generated_files.append(f4)

    # Chart 5: Department Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df_plot, y='Department', hue='Department', palette='mako', legend=False, ax=ax)
    ax.set_title("5. Department Distribution", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Count", fontweight='bold')
    ax.set_ylabel("Department", fontweight='bold')
    plt.tight_layout()
    f5 = os.path.join(output_dir, "05_department_distribution.png")
    fig.savefig(f5, dpi=300)
    plt.close(fig)
    generated_files.append(f5)

    # Chart 6: Refinery Unit Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df_plot, y='Refinery_Unit', hue='Refinery_Unit', palette='crest', legend=False, ax=ax)
    ax.set_title("6. Refinery Unit Distribution", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Count", fontweight='bold')
    ax.set_ylabel("Refinery Unit", fontweight='bold')
    plt.tight_layout()
    f6 = os.path.join(output_dir, "06_refinery_unit_distribution.png")
    fig.savefig(f6, dpi=300)
    plt.close(fig)
    generated_files.append(f6)

    # Chart 7: Potential Consequence Distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.countplot(data=df_plot, y='Potential_Consequence', hue='Potential_Consequence', palette='rocket', legend=False, ax=ax)
    ax.set_title("7. Potential Consequence Distribution", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Count", fontweight='bold')
    ax.set_ylabel("Potential Consequence", fontweight='bold')
    plt.tight_layout()
    f7 = os.path.join(output_dir, "07_potential_consequence_distribution.png")
    fig.savefig(f7, dpi=300)
    plt.close(fig)
    generated_files.append(f7)

    # Chart 8: Immediate Cause Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df_plot, y='Immediate_Cause', hue='Immediate_Cause', palette='magma', legend=False, ax=ax)
    ax.set_title("8. Immediate Cause Distribution", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Count", fontweight='bold')
    ax.set_ylabel("Immediate Cause", fontweight='bold')
    plt.tight_layout()
    f8 = os.path.join(output_dir, "08_immediate_cause_distribution.png")
    fig.savefig(f8, dpi=300)
    plt.close(fig)
    generated_files.append(f8)

    # Chart 9: PPE NonCompliance Distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df_plot, x='PPE_NonCompliance', hue='PPE_NonCompliance', palette=['#5cb85c', '#d9534f'], legend=False, ax=ax)
    ax.set_title("9. PPE Non-Compliance Flag", fontsize=12, fontweight='bold')
    plt.tight_layout()
    f9 = os.path.join(output_dir, "09_ppe_noncompliance_distribution.png")
    fig.savefig(f9, dpi=300)
    plt.close(fig)
    generated_files.append(f9)

    # Chart 10: Supervisor Negligence Distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df_plot, x='Supervisor_Negligence', hue='Supervisor_Negligence', palette=['#5cb85c', '#d9534f'], legend=False, ax=ax)
    ax.set_title("10. Supervisor Negligence Flag", fontsize=12, fontweight='bold')
    plt.tight_layout()
    f10 = os.path.join(output_dir, "10_supervisor_negligence_distribution.png")
    fig.savefig(f10, dpi=300)
    plt.close(fig)
    generated_files.append(f10)

    # Chart 11: Maintenance Delay Distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df_plot, x='Maintenance_Delay_or_Issue', hue='Maintenance_Delay_or_Issue', palette=['#5cb85c', '#d9534f'], legend=False, ax=ax)
    ax.set_title("11. Maintenance Delay Flag", fontsize=12, fontweight='bold')
    plt.tight_layout()
    f11 = os.path.join(output_dir, "11_maintenance_delay_distribution.png")
    fig.savefig(f11, dpi=300)
    plt.close(fig)
    generated_files.append(f11)

    # Chart 12: Repeated Issue Ignored Distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df_plot, x='Repeated_Issue_Ignored', hue='Repeated_Issue_Ignored', palette=['#5cb85c', '#d9534f'], legend=False, ax=ax)
    ax.set_title("12. Repeated Issue Ignored Flag", fontsize=12, fontweight='bold')
    plt.tight_layout()
    f12 = os.path.join(output_dir, "12_repeated_issue_ignored_distribution.png")
    fig.savefig(f12, dpi=300)
    plt.close(fig)
    generated_files.append(f12)

    # Chart 13: Previous Similar Reports Distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=df_plot, x='Previous_Similar_Reports', discrete=True, color='#2b5c8f', ax=ax)
    ax.set_title("13. Previous Similar Reports Frequency", fontsize=12, fontweight='bold')
    plt.tight_layout()
    f13 = os.path.join(output_dir, "13_previous_similar_reports_distribution.png")
    fig.savefig(f13, dpi=300)
    plt.close(fig)
    generated_files.append(f13)

    # Chart 14: Near Miss Description Length Distribution
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(data=df_plot, x='word_count', hue='Target_Label', kde=True, palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("14. Description Word Count Distribution by Target", fontsize=12, fontweight='bold')
    ax.set_xlabel("Word Count", fontweight='bold')
    plt.tight_layout()
    f14 = os.path.join(output_dir, "14_description_length_distribution.png")
    fig.savefig(f14, dpi=300)
    plt.close(fig)
    generated_files.append(f14)

    # Chart 15: Target vs Major Safety Factors
    factors = ['PPE_NonCompliance', 'Supervisor_Negligence', 'Maintenance_Delay_or_Issue', 'Repeated_Issue_Ignored']
    df_factors = df_plot.groupby('Target_Label')[factors].mean().T
    fig, ax = plt.subplots(figsize=(8, 5))
    df_factors.plot(kind='bar', color=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("15. Mean Safety Factor Rate by Target Class", fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel("Proportion Active (True)", fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')
    plt.tight_layout()
    f15 = os.path.join(output_dir, "15_target_vs_safety_factors.png")
    fig.savefig(f15, dpi=300)
    plt.close(fig)
    generated_files.append(f15)

    # Chart 16: Target vs Risk Level
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df_plot, x='Risk_Level', hue='Target_Label', order=['Low', 'Medium', 'High', 'Critical'], palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("16. Target Class Breakdown across Risk Levels (Leakage Audit)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Risk Level", fontweight='bold')
    ax.set_ylabel("Count", fontweight='bold')
    plt.tight_layout()
    f16 = os.path.join(output_dir, "16_target_vs_risk_level.png")
    fig.savefig(f16, dpi=300)
    plt.close(fig)
    generated_files.append(f16)

    # Chart 17: Target vs Work Type
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.countplot(data=df_plot, y='Work_Type', hue='Target_Label', palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("17. Target Class Distribution by Work Type", fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    f17 = os.path.join(output_dir, "17_target_vs_work_type.png")
    fig.savefig(f17, dpi=300)
    plt.close(fig)
    generated_files.append(f17)

    # Chart 18: Target vs Department
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.countplot(data=df_plot, y='Department', hue='Target_Label', palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("18. Target Class Distribution by Department", fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    f18 = os.path.join(output_dir, "18_target_vs_department.png")
    fig.savefig(f18, dpi=300)
    plt.close(fig)
    generated_files.append(f18)

    # Chart 19: Target vs Refinery Unit
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.countplot(data=df_plot, y='Refinery_Unit', hue='Target_Label', palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("19. Target Class Distribution by Refinery Unit", fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    f19 = os.path.join(output_dir, "19_target_vs_refinery_unit.png")
    fig.savefig(f19, dpi=300)
    plt.close(fig)
    generated_files.append(f19)

    # Chart 20: Factor Combinations vs Target
    df_plot['active_factors_count'] = df_plot[factors].sum(axis=1)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df_plot, x='active_factors_count', hue='Target_Label', palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("20. Target Distribution by Active Safety Factor Count", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Number of Active Safety Factors (1 to 4)", fontweight='bold')
    ax.set_ylabel("Count", fontweight='bold')
    plt.tight_layout()
    f20 = os.path.join(output_dir, "20_factor_combinations.png")
    fig.savefig(f20, dpi=300)
    plt.close(fig)
    generated_files.append(f20)

    # Chart 21: Cross-Sheet Target Distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.countplot(data=df_plot, y='source_sheet', hue='Target_Label', palette=['#2b5c8f', '#d9534f'], ax=ax)
    ax.set_title("21. Cross-Sheet Target Distribution (Source Sheet Leakage Audit)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Count", fontweight='bold')
    ax.set_ylabel("Source Sheet", fontweight='bold')
    plt.tight_layout()
    f21 = os.path.join(output_dir, "21_cross_sheet_target_distribution.png")
    fig.savefig(f21, dpi=300)
    plt.close(fig)
    generated_files.append(f21)

    return generated_files
