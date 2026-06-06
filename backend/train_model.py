"""
PhishShield — Model Training Script
Datasets:
  - URLs  : UCI Phishing Websites Dataset (11,054 rows, 30 pre-extracted features)
            Source: kaggle.com/datasets/eswarchandt/phishing-website-detector
  - Emails: SMS Spam Collection Dataset (5,574 rows)
            Source: github.com/justmarkham/pycon-2016-tutorial
"""

import os
import pickle
import urllib.request
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier
from features import extract_email_features

SEED = 42
DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

UCI_DATA_PATH   = os.path.join(DATA_DIR, "phishing_uci.csv")
EMAIL_DATA_PATH = os.path.join(DATA_DIR, "emails.tsv")

EMAIL_DATASET_URL = (
    "https://raw.githubusercontent.com/justmarkham/"
    "pycon-2016-tutorial/master/data/sms.tsv"
)


def download_if_missing(path, url):
    if not os.path.exists(path):
        print(f"Downloading {url} ...")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            with open(path, "wb") as f:
                f.write(r.read())
        print(f"Saved to {path}")


# ── URL model (UCI pre-extracted features) ─────────────────────────────────────

def load_url_data():
    """
    UCI Phishing Websites Dataset — 30 pre-extracted structural/behavioural features.
    Labels: 1 = phishing, -1 = legitimate → remapped to 1/0.
    """
    if not os.path.exists(UCI_DATA_PATH):
        raise FileNotFoundError(
            f"UCI dataset not found at {UCI_DATA_PATH}.\n"
            "Download from: https://www.kaggle.com/datasets/eswarchandt/phishing-website-detector\n"
            "and save as data/phishing_uci.csv"
        )

    df = pd.read_csv(UCI_DATA_PATH)
    feature_cols = [c for c in df.columns if c not in ("Index", "class")]
    X = df[feature_cols].values.astype(float)
    y = (df["class"].values == 1).astype(int)

    print(f"UCI URL dataset: {len(df):,} rows  |  phishing={int(y.sum()):,}  legitimate={int((y==0).sum()):,}")
    return X, y, feature_cols


def train_url_model():
    print("\n── Training URL phishing model (UCI Dataset) ────────────────────")
    X, y, feature_cols = load_url_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    rf  = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=2,
                                  random_state=SEED, n_jobs=-1)
    xgb = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                        eval_metric="logloss", random_state=SEED, n_jobs=-1)

    ensemble = VotingClassifier(estimators=[("rf", rf), ("xgb", xgb)], voting="soft")
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Phishing"]))

    cv = cross_val_score(ensemble, X, y,
                         cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED),
                         scoring="accuracy", n_jobs=-1)
    print(f"5-fold CV: {cv.mean():.4f} ± {cv.std():.4f}")

    with open(os.path.join(MODEL_DIR, "url_model.pkl"), "wb") as f:
        pickle.dump({"model": ensemble, "feature_names": feature_cols}, f)

    return {"test_accuracy": round(acc, 4), "cv_mean": round(cv.mean(), 4), "cv_std": round(cv.std(), 4)}


# ── Email model ────────────────────────────────────────────────────────────────

def load_email_data():
    download_if_missing(EMAIL_DATA_PATH, EMAIL_DATASET_URL)

    rows = []
    with open(EMAIL_DATA_PATH, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                rows.append({"label": parts[0], "text": parts[1]})
    df = pd.DataFrame(rows)

    spam = df[df["label"] == "spam"]
    ham  = df[df["label"] == "ham"].sample(n=len(spam) * 3, random_state=SEED)
    df   = pd.concat([spam, ham]).sample(frac=1, random_state=SEED).reset_index(drop=True)

    print(f"Email dataset: {len(df):,} rows  |  spam={len(spam):,}  ham={len(ham):,}")

    features, labels = [], []
    for _, row in df.iterrows():
        feats = extract_email_features(subject="", body=str(row["text"]))
        features.append(list(feats.values()))
        labels.append(1 if row["label"] == "spam" else 0)

    return np.array(features), np.array(labels)


def train_email_model():
    print("\n── Training email phishing model ────────────────────────────────")
    X, y = load_email_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    rf  = RandomForestClassifier(n_estimators=200, max_depth=15, min_samples_leaf=2,
                                  random_state=SEED, n_jobs=-1)
    xgb = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                        eval_metric="logloss", random_state=SEED, n_jobs=-1)

    ensemble = VotingClassifier(estimators=[("rf", rf), ("xgb", xgb)], voting="soft")
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Phishing"]))

    cv = cross_val_score(ensemble, X, y,
                         cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED),
                         scoring="accuracy", n_jobs=-1)
    print(f"5-fold CV: {cv.mean():.4f} ± {cv.std():.4f}")

    email_feature_names = list(extract_email_features("", "").keys())
    with open(os.path.join(MODEL_DIR, "email_model.pkl"), "wb") as f:
        pickle.dump({"model": ensemble, "feature_names": email_feature_names}, f)

    return {"test_accuracy": round(acc, 4), "cv_mean": round(cv.mean(), 4), "cv_std": round(cv.std(), 4)}


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("PhishShield — Model Training")
    print("=" * 60)

    url_results   = train_url_model()
    email_results = train_email_model()

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"URL model   → accuracy: {url_results['test_accuracy']*100:.2f}%  |  CV: {url_results['cv_mean']*100:.2f}% ± {url_results['cv_std']*100:.2f}%")
    print(f"Email model → accuracy: {email_results['test_accuracy']*100:.2f}%  |  CV: {email_results['cv_mean']*100:.2f}% ± {email_results['cv_std']*100:.2f}%")
    print(f"\nModels saved to: {MODEL_DIR}")
