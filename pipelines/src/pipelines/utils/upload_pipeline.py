import argparse
from kfp.registry import RegistryClient

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=str, required=True)
    parser.add_argument("--yaml", type=str, required=True)
    parser.add_argument("--tag", type=str, action="append")
    args = parser.parse_args()

    client = RegistryClient(
        host=args.dest,
    )

    templateName, versionName = client.upload_pipeline(
        file_name=args.yaml,
        tags=args.tag,
    )
