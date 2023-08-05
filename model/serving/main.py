# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
