import pickle
import os
import numpy as np
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from features import extract_url_features, extract_email_features

app = FastAPI(title="PhishShield API", description="Real-time phishing detection", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models")
history_store: List[dict] = []

def load_model(name: str):
    path = f"{MODEL_PATH}/{name}.pkl"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model {name} not found. Run train_model.py first.")
    with open(path, "rb") as f:
        return pickle.load(f)

url_model_data = load_model("url_model")
email_model_data = load_model("email_model")

URL_MODEL = url_model_data["model"]
URL_FEATURES = url_model_data["feature_names"]
EMAIL_MODEL = email_model_data["model"]
EMAIL_FEATURES = email_model_data["feature_names"]


class URLRequest(BaseModel):
    url: str

class EmailRequest(BaseModel):
    subject: str
    body: str
    sender: str = ""

class AnalysisResult(BaseModel):
    input: str
    type: str
    is_phishing: bool
    confidence: float
    risk_level: str
    top_features: List[dict]
    timestamp: str


def get_risk_level(confidence: float, is_phishing: bool) -> str:
    if not is_phishing:
        if confidence > 0.85:
            return "safe"
        return "low"
    if confidence > 0.85:
        return "high"
    if confidence > 0.65:
        return "medium"
    return "low"


def get_top_features(feature_names, feature_values, n=5):
    pairs = sorted(zip(feature_names, feature_values), key=lambda x: abs(x[1]), reverse=True)
    return [{"feature": name.replace("_", " ").title(), "value": round(float(val), 4)}
            for name, val in pairs[:n]]


@app.get("/")
def root():
    return {"message": "PhishShield API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "models_loaded": True, "timestamp": datetime.utcnow().isoformat()}


@app.post("/analyze-url", response_model=AnalysisResult)
def analyze_url(req: URLRequest):
    if not req.url or len(req.url.strip()) < 4:
        raise HTTPException(status_code=400, detail="Invalid URL")

    features = extract_url_features(req.url.strip())
    feature_vector = np.array([[features[f] for f in URL_FEATURES]])

    proba = URL_MODEL.predict_proba(feature_vector)[0]
    is_phishing = bool(proba[1] >= 0.5)
    confidence = float(proba[1] if is_phishing else proba[0])

    top_feats = get_top_features(URL_FEATURES, feature_vector[0])

    result = {
        "input": req.url,
        "type": "url",
        "is_phishing": is_phishing,
        "confidence": round(confidence * 100, 1),
        "risk_level": get_risk_level(confidence, is_phishing),
        "top_features": top_feats,
        "timestamp": datetime.utcnow().isoformat()
    }
    history_store.append(result)
    if len(history_store) > 100:
        history_store.pop(0)

    return result


@app.post("/analyze-email", response_model=AnalysisResult)
def analyze_email(req: EmailRequest):
    if not req.body or len(req.body.strip()) < 5:
        raise HTTPException(status_code=400, detail="Email body is required")

    features = extract_email_features(req.subject, req.body, req.sender)
    feature_vector = np.array([[features[f] for f in EMAIL_FEATURES]])

    proba = EMAIL_MODEL.predict_proba(feature_vector)[0]
    is_phishing = bool(proba[1] >= 0.5)
    confidence = float(proba[1] if is_phishing else proba[0])

    top_feats = get_top_features(EMAIL_FEATURES, feature_vector[0])

    result = {
        "input": f"Subject: {req.subject[:60]}",
        "type": "email",
        "is_phishing": is_phishing,
        "confidence": round(confidence * 100, 1),
        "risk_level": get_risk_level(confidence, is_phishing),
        "top_features": top_feats,
        "timestamp": datetime.utcnow().isoformat()
    }
    history_store.append(result)
    if len(history_store) > 100:
        history_store.pop(0)

    return result


@app.get("/history")
def get_history(limit: int = 20):
    return {"results": history_store[-limit:][::-1], "total": len(history_store)}


@app.get("/stats")
def get_stats():
    if not history_store:
        return {"total": 0, "phishing": 0, "legitimate": 0, "phishing_rate": 0}
    total = len(history_store)
    phishing = sum(1 for r in history_store if r["is_phishing"])
    return {
        "total": total,
        "phishing": phishing,
        "legitimate": total - phishing,
        "phishing_rate": round(phishing / total * 100, 1)
    }
