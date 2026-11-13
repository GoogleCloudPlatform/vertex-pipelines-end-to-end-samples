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

import argparse
import json
import os
import logging

from .train import train
from shared.training_config import TrainingConfig

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument("--input_path", type=str, required=True)
parser.add_argument("--input_test_path", type=str, required=False)
parser.add_argument("--output_train_path", type=str, required=True)
parser.add_argument("--output_valid_path", type=str, required=True)
parser.add_argument("--output_test_path", type=str, required=True)
parser.add_argument("--output_model", default=os.getenv("AIP_MODEL_DIR"), type=str)
parser.add_argument("--output_metrics", type=str, required=True)
parser.add_argument("--config", type=str, required=True)
args = vars(parser.parse_args())
config_dict = json.loads(args["config"])
config = TrainingConfig(**config_dict)

train(
    input_path=args["input_path"],
    input_test_path=args["input_test_path"],
    output_train_path=args["output_train_path"],
    output_valid_path=args["output_valid_path"],
    output_test_path=args["output_test_path"],
    output_model=args["output_model"],
    output_metrics=args["output_metrics"],
    config=config,
)
