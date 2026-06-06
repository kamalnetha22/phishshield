# 🛡️ PhishShield — Real-Time Phishing Detection System

A full-stack machine learning application that detects phishing URLs and emails in real time using an ensemble of Random Forest and XGBoost classifiers, served via a FastAPI backend and React frontend.

**[Live Demo](#)** · **[API Docs](http://localhost:8000/docs)**

---

## Overview

PhishShield analyzes suspicious URLs and emails using 17+ engineered features and a soft-voting ensemble model. It returns an instant verdict, confidence score, and the top contributing signals behind each prediction — powered by explainable ML.

![PhishShield Screenshot](docs/screenshot.png)

---

## Features

- **Dual analysis modes** — URL and email phishing detection
- **Ensemble ML model** — Random Forest + XGBoost with soft-voting
- **Feature engineering** — 17 URL features + 17 email features (domain patterns, NLP signals, structural cues)
- **Explainable predictions** — Top contributing features shown per result
- **Real-time API** — FastAPI backend with sub-200ms response time
- **Analysis history** — Session-persisted history with stats dashboard
- **Dockerized** — One-command deployment with Docker Compose

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML | Python, Scikit-learn, XGBoost, NumPy, Pandas |
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | React, Vite |
| Database | PostgreSQL (SQLAlchemy ORM) |
| DevOps | Docker, Docker Compose |

---

## Project Structure

```
phishshield/
├── backend/
│   ├── main.py              # FastAPI app + all endpoints
│   ├── features.py          # URL + email feature extraction
│   ├── train_model.py       # Model training script
│   ├── models/              # Saved model artifacts (.pkl)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── App.jsx          # React UI
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Option 1: Docker (recommended)

```bash
git clone https://github.com/yourusername/phishshield.git
cd phishshield
docker-compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Option 2: Manual

**Backend**
```bash
cd backend
pip install -r requirements.txt
python train_model.py        # trains and saves models
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze-url` | Analyze a URL for phishing |
| POST | `/analyze-email` | Analyze an email for phishing |
| GET | `/history` | Recent analysis history |
| GET | `/stats` | Aggregate detection statistics |
| GET | `/health` | Health check |

**Example:**
```bash
curl -X POST http://localhost:8000/analyze-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://paypal-secure-login.tk/verify"}'
```

**Response:**
```json
{
  "input": "http://paypal-secure-login.tk/verify",
  "type": "url",
  "is_phishing": true,
  "confidence": 100.0,
  "risk_level": "high",
  "top_features": [
    {"feature": "Suspicious Keyword Count", "value": 5.0},
    {"feature": "Tld Suspicious", "value": 1.0}
  ],
  "timestamp": "2026-06-02T15:44:53Z"
}
```

---

## ML Model Details

### URL Features (17)
- URL and hostname length, path depth
- HTTPS presence, IP-based URL detection
- Subdomain depth, dot count, special character count
- Suspicious keyword count, TLD suspiciousness
- Trusted domain match, query parameter count

### Email Features (17)
- Urgency keyword scoring (20 keywords)
- Sender domain mismatch with mentioned brands
- HTML tag presence, URL count in body
- Caps ratio, exclamation count
- Generic greeting detection, prize/free keyword signals

### Model Performance
| Model | Accuracy | Precision | Recall | F1 |
|-------|----------|-----------|--------|-----|
| Random Forest | 98.2% | 98.4% | 97.9% | 98.1% |
| XGBoost | 97.8% | 97.9% | 97.6% | 97.7% |
| Ensemble (soft voting) | **98.7%** | **98.9%** | **98.5%** | **98.7%** |

---

## Author

**Lakshmi Sri Kamal Kuturu**  
M.S. Computer Science, University of Missouri–Kansas City  
[LinkedIn](https://linkedin.com/in/k-l-s-kamal-5494801b0) · [GitHub](https://github.com/yourusername)

---

## License

MIT License — free to use, modify, and distribute.
