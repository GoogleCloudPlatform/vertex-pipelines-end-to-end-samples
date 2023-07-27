import joblib
import os

import pandas as pd
from fastapi import FastAPI, Request
from google.cloud import storage

app = FastAPI()
client = storage.Client()

with open("model.joblib", "wb") as f:
    client.download_blob_to_file(f"{os.environ['AIP_STORAGE_URI']}/model.joblib", f)
_model = joblib.load("model.joblib")


@app.get(os.environ.get("AIP_HEALTH_ROUTE", "/healthz"))
def health():
    return {}


@app.post(os.environ.get("AIP_PREDICT_ROUTE", "/predict"))
async def predict(request: Request):
    body = await request.json()

    instances = body["instances"]
    inputs_df = pd.DataFrame(instances)
    outputs = _model.predict(inputs_df).tolist()

    return {"predictions": outputs}
