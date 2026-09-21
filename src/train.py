import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from typing import Dict, Any, Tuple

class MajorityClassBaseline:
    """Baseline 1: Always predicts the majority class (0 = Non-SIF)."""
    def fit(self, X, y):
        vals, counts = np.unique(y, return_counts=True)
        self.majority_class_ = vals[np.argmax(counts)]
        return self
        
    def predict(self, X):
        n_samples = X.shape[0]
        return np.full(n_samples, self.majority_class_)
        
    def predict_proba(self, X):
        n_samples = X.shape[0]
        probs = np.zeros((n_samples, 2))
        probs[:, self.majority_class_] = 1.0
        return probs

class FourFactorRuleBaseline:
    """
    Baseline 2: Predicts SIF (1) iff all 4 safety precursor factors are True:
    - PPE_NonCompliance == True
    - Supervisor_Negligence == True
    - Maintenance_Delay_or_Issue == True
    - Repeated_Issue_Ignored == True
    """
    def fit(self, X, y):
        return self
        
    def predict_from_df(self, df: pd.DataFrame) -> np.ndarray:
        factors = ['PPE_NonCompliance', 'Supervisor_Negligence', 
                   'Maintenance_Delay_or_Issue', 'Repeated_Issue_Ignored']
        # Check if all 4 factors are active
        all_active = (df[factors].sum(axis=1) == 4).astype(int).values
        return all_active

    def predict_proba_from_df(self, df: pd.DataFrame) -> np.ndarray:
        preds = self.predict_from_df(df)
        n_samples = len(preds)
        probs = np.zeros((n_samples, 2))
        probs[:, 1] = preds.astype(float)
        probs[:, 0] = 1.0 - probs[:, 1]
        return probs

def train_candidate_models(X_train, y_train, config_name: str) -> Dict[str, Any]:
    """
    Trains multiple candidate models for a given feature configuration.
    """
    models = {}
    
    # 1. Logistic Regression (Balanced)
    lr = LogisticRegression(C=1.0, class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    models['LogisticRegression_Balanced'] = lr

    # 2. Logistic Regression (Standard)
    lr_std = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    lr_std.fit(X_train, y_train)
    models['LogisticRegression_Standard'] = lr_std

    # 3. Linear SVM (Calibrated for probabilities)
    svc = LinearSVC(C=1.0, class_weight='balanced', random_state=42, dual=False if X_train.shape[0] > X_train.shape[1] else True)
    calibrated_svc = CalibratedClassifierCV(estimator=svc, cv=3)
    calibrated_svc.fit(X_train, y_train)
    models['LinearSVC_Calibrated'] = calibrated_svc

    # 4. Naive Bayes (ComplementNB for pure TF-IDF non-negative features)
    if config_name == "config_a_text":
        nb = ComplementNB(alpha=1.0)
        nb.fit(X_train, y_train)
        models['ComplementNB'] = nb

    # 5. Random Forest (Balanced)
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    models['RandomForest_Balanced'] = rf

    return models
