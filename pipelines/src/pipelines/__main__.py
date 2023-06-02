from argparse import ArgumentParser
from os import environ as env

from pipelines.utils import compile_pipeline


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--compile", action="store_true")
    args = parser.parse_args()

    if args.compile:
        missing_keys = [x for x in ["pipeline", "config"] if env.get(x) is None]
        if missing_keys:
            raise ValueError(f"Missing environment variables: {missing_keys}")
        compile_pipeline(env["pipeline"])
