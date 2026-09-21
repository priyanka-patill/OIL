import os
import json
import re
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional

DEFAULT_MODEL_DIR = "models/final_model"

_MODEL_CACHE: Dict[str, Any] = {}

def load_model(model_dir: str = DEFAULT_MODEL_DIR) -> Dict[str, Any]:
    """
    Loads and caches all saved model package artifacts from disk.
    Supports single-load reuse for high-throughput prediction environments.
    """
    global _MODEL_CACHE
    abs_dir = os.path.abspath(model_dir)
    
    if abs_dir in _MODEL_CACHE:
        return _MODEL_CACHE[abs_dir]
        
    model_path = os.path.join(abs_dir, "model.joblib")
    vectorizer_path = os.path.join(abs_dir, "tfidf_vectorizer.joblib")
    threshold_path = os.path.join(abs_dir, "threshold.json")
    label_map_path = os.path.join(abs_dir, "label_mapping.json")
    feature_config_path = os.path.join(abs_dir, "feature_config.json")
    metadata_path = os.path.join(abs_dir, "model_metadata.json")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError(f"TF-IDF vectorizer artifact not found at {vectorizer_path}")

    model = joblib.load(model_path)
    tfidf_vectorizer = joblib.load(vectorizer_path)

    threshold = 0.60
    if os.path.exists(threshold_path):
        with open(threshold_path, "r", encoding="utf-8") as f:
            t_data = json.load(f)
            threshold = t_data.get("optimal_threshold", 0.60)

    label_mapping = {"0": "Non-SIF", "1": "SIF-Potential"}
    if os.path.exists(label_map_path):
        with open(label_map_path, "r", encoding="utf-8") as f:
            label_mapping = json.load(f)

    feature_config = {}
    if os.path.exists(feature_config_path):
        with open(feature_config_path, "r", encoding="utf-8") as f:
            feature_config = json.load(f)

    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    pkg = {
        "model": model,
        "tfidf_vectorizer": tfidf_vectorizer,
        "threshold": threshold,
        "label_mapping": label_mapping,
        "feature_config": feature_config,
        "metadata": metadata,
        "model_dir": abs_dir
    }
    
    _MODEL_CACHE[abs_dir] = pkg
    return pkg

def validate_report(report: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates input report structure, strips excluded leakage fields (source_sheet, etc.),
    and returns a clean report dictionary and validation warnings.
    """
    if not isinstance(report, dict):
        raise ValueError("Report input must be a Python dictionary.")

    warnings = []
    clean_report = report.copy()

    # 1. Stripping excluded leakage fields
    excluded_fields = [
        "source_sheet", "Near_Miss_ID", "Potential_Consequence", 
        "Risk_Level", "Corrective_Action", "Action_Status", "High_Potential_Near_Miss"
    ]
    for field in excluded_fields:
        if field in clean_report:
            warnings.append(f"Excluded leakage field '{field}' removed from model prediction input.")
            clean_report.pop(field, None)

    # 2. Text validation
    description = clean_report.get("Near_Miss_Description", "")
    if pd.isna(description) or not str(description).strip():
        warnings.append("Near_Miss_Description is empty or missing.")
        clean_report["Near_Miss_Description"] = ""
    else:
        clean_report["Near_Miss_Description"] = str(description).strip()

    return clean_report, warnings

def generate_explanation(report_text: str, tfidf_vectorizer, model, top_n: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    """
    Generates feature-level term explanations and a human-readable summary based on actual model coefficients.
    """
    if not report_text or not hasattr(model, 'coef_'):
        return [], "Prediction generated from non-text or baseline features."

    # Transform text to TF-IDF vector
    X_vec = tfidf_vectorizer.transform([report_text])
    feature_names = tfidf_vectorizer.get_feature_names_out()
    coefs = model.coef_[0]

    # Find active features in the input report text
    active_indices = X_vec.nonzero()[1]
    if len(active_indices) == 0:
        return [], "Report text did not match any learned vocabulary terms."

    explanations = []
    pos_terms = []
    neg_terms = []

    for idx in active_indices:
        term = feature_names[idx]
        tfidf_val = X_vec[0, idx]
        weight = coefs[idx]
        contribution = round(float(tfidf_val * weight), 4)

        item = {
            "type": "text_ngram",
            "feature": term,
            "weight": round(float(weight), 4),
            "contribution": contribution
        }
        explanations.append(item)

        if weight > 0:
            pos_terms.append(term)
        else:
            neg_terms.append(term)

    # Sort explanations by absolute contribution
    explanations.sort(key=lambda x: abs(x['contribution']), reverse=True)
    explanations = explanations[:top_n]

    # Human readable summary
    if len(pos_terms) > 0:
        readable = f"Model prediction influenced by key safety-hazard terms: '{', '.join(pos_terms[:4])}'."
    elif len(neg_terms) > 0:
        readable = f"Model prediction influenced by routine operational phrasing: '{', '.join(neg_terms[:4])}'."
    else:
        readable = "Model prediction generated from general report text structure."

    return explanations, readable

def predict_sif(
    report: Dict[str, Any], 
    model_package: Optional[Dict[str, Any]] = None, 
    threshold: Optional[float] = None,
    model_dir: str = DEFAULT_MODEL_DIR
) -> Dict[str, Any]:
    """
    Main reusable SIF prediction function.
    Accepts a report dictionary, performs input validation & leakage stripping,
    runs model prediction, extracts explainability, and returns a standardized response.
    """
    if model_package is None:
        model_package = load_model(model_dir)

    model = model_package["model"]
    tfidf_vectorizer = model_package["tfidf_vectorizer"]
    eval_threshold = threshold if threshold is not None else model_package["threshold"]
    label_mapping = model_package["label_mapping"]
    version = model_package.get("metadata", {}).get("model_version", "sif_model_v1")

    # Validate and clean report
    clean_report, validation_warnings = validate_report(report)
    text_input = clean_report.get("Near_Miss_Description", "")

    # Preprocess text
    X_vec = tfidf_vectorizer.transform([text_input])

    # Predict probability and class
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_vec)[0]
        prob_sif = float(probs[1])
    else:
        prob_sif = 1.0 if model.predict(X_vec)[0] == 1 else 0.0

    classification = 1 if prob_sif >= eval_threshold else 0
    prediction_label = label_mapping.get(str(classification), "SIF-Potential" if classification == 1 else "Non-SIF")

    # Generate Explainability
    explanation_details, human_explanation = generate_explanation(text_input, tfidf_vectorizer, model)

    response = {
        "prediction": prediction_label,
        "classification": classification,
        "probability": round(prob_sif, 4),
        "threshold": round(eval_threshold, 4),
        "model_version": version,
        "explanation": explanation_details,
        "human_readable_explanation": human_explanation,
        "disclaimer": "This prediction is an AI safety decision-support score and requires qualified HSE professional review.",
        "warnings": validation_warnings
    }

    return response
