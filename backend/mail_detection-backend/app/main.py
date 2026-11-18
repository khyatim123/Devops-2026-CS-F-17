from pathlib import Path
import sys
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BACKEND_DIR / "spam_model.joblib"
sys.path.insert(0, str(BACKEND_DIR))

app = FastAPI(title="Email Spam Detection API", version="1.0.0",
              description="Classifies email text as spam or legitimate.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None

class EmailRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=20000,
                      description="Email subject and body text")

@app.on_event("startup")
def load_model():
    global model
    if not MODEL_PATH.exists():
        raise RuntimeError(
            "Model not found. From the backend folder run: python train_model.py"
        )
    model = joblib.load(MODEL_PATH)

@app.get("/")
def home():
    return {"message": "Email Spam Detection API is running"}

@app.get("/api/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/api/predict")
def predict_email(payload: EmailRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded.")
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Email text cannot be empty.")

    prediction = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)
    confidence = float(probabilities[classes.index(prediction)]) * 100

    return {
        "prediction": "SPAM" if prediction == "spam" else "NOT SPAM",
        "label": prediction,
        "confidence": round(confidence, 2),
        "message": (
            "This email looks suspicious." if prediction == "spam"
            else "This email appears legitimate."
        )
    }
