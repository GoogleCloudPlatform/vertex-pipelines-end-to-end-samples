from kfp.v2.dsl import Input, Output, component, Dataset
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def quote_csv_header(
    input_dataset: Input[Dataset],
    output_dataset: Output[Dataset],
    file_pattern: str = None,
) -> None:
    """
    Change header in CSV dataset to include quotes for each column name
    (e.g. "col1","col2","...").

    Args:
        input_dataset (Input[Dataset]): Input dataset in CSV format.
        output_dataset (Output[Dataset]): Output dataset containing the adjusted
            header.
        file_pattern (str): Optional file pattern which assumes `input_dataset`
            is a folder containing files. The file pattern can be e.g. "files-*.csv".
            Each file will be processed and saved with the same name in the folder
            `output_dataset`. If not provided both `input_dataset` and `output_dataset`
            are assumed to a single file.
    Returns:
        None
    """

    import logging
    import shutil
    from pathlib import Path

    logging.getLogger().setLevel(logging.INFO)

    def quote_cols_in_header(header, quote='"', delimiter=","):
        quoted_cols = [quote + col + quote for col in header.split(delimiter)]
        return delimiter.join(quoted_cols)

    def process_file(input_path: Path, output_path: Path):
        logging.info(f"reading input file {input_path}")
        with open(input_path, "r") as in_f:
            # read first line and strip newline char
            header = in_f.readline().rstrip("\n")
            logging.info(f"found header: {header}")

            # adjust header
            new_header = quote_cols_in_header(header)
            logging.info(f"adjusted header to: {new_header}")

            logging.info(f"writing output file {output_path}")
            with open(output_path, "w") as out_f:
                # write header with newline char
                out_f.write(new_header + "\n")
                # write remaining content from source to destination
                shutil.copyfileobj(in_f, out_f)

    input_path = Path(input_dataset.path)
    output_path = Path(output_dataset.path)

    if file_pattern:
        output_path.mkdir(exist_ok=True, parents=True)
        for input_file in input_path.glob(file_pattern):
            process_file(input_file, output_path / input_file.name)
    else:
        process_file(input_path, output_path)
