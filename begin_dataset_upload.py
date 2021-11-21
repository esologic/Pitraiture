"""
Prompts user to select datasets to be zipped and then moved to a location where they will
automatically be uploaded to ownCloud.
"""

import shutil
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Optional

import click
import inquirer

from pitraiture.cli_common import DEFAULT_DATASET_PATH
from pitraiture.logger_common import LOGGER

COMPRESSED_DATASET_EXTENSION = "zip"

DEFAULT_UPLOADS_ZIP_ENABLED = False


def copy_dataset_to_upload_location(
    path_to_dataset_to_upload: Path, upload_directory: Path
) -> None:
    """
    Copy the dataset, uncompressed, to the upload directory.
    :param path_to_dataset_to_upload: The directory of images to copy to the upload directory.
    :param upload_directory: The location the dataset should be copied to.
    :return: None
    """
    destination_path = upload_directory.joinpath(path_to_dataset_to_upload.name)
    LOGGER.info(f"Copying {path_to_dataset_to_upload} -> {destination_path}")
    destination_path.mkdir(exist_ok=True)
    for image_path in path_to_dataset_to_upload.glob("*.jpeg"):
        source = str(image_path)
        destination = destination_path.joinpath(image_path.name)
        try:
            shutil.copyfile(src=source, dst=destination)
            LOGGER.info(f"Copied {image_path.name}")
        except shutil.SameFileError:
            LOGGER.info(f"Skipped {source}, same file.")
    LOGGER.info(
        f"Dataset: {path_to_dataset_to_upload.name} Copied to upload folder. "
        f"It will now be uploaded."
    )


def compress_directory_move_to_upload_location(
    path_to_dataset_to_upload: Path, upload_directory: Path
) -> None:
    """
    Compresses a given target_path and places the resulting zip file in upload_directory.
    Log two statements before and after the process is complete.
    :param path_to_dataset_to_upload: The folder to compress and upload
    :param upload_directory: The location to place the compressed folder.
    :return: None
    """
    zip_path = upload_directory.joinpath(path_to_dataset_to_upload.name)
    LOGGER.info(
        f"Compressing {path_to_dataset_to_upload} -> "
        f"{str(zip_path) + f'.{COMPRESSED_DATASET_EXTENSION}'}"
    )
    shutil.make_archive(
        str(zip_path),
        COMPRESSED_DATASET_EXTENSION,
        str(path_to_dataset_to_upload.parent),
        str(path_to_dataset_to_upload.name),
    )
    LOGGER.info(
        f"{zip_path.name + f'.{COMPRESSED_DATASET_EXTENSION}'} "
        f"Successfully Created! It will now be uploaded."
    )


def _num_files_in_dir(path: Path) -> int:
    """
    Count the number of files at a given directory Path.
    :param path: The path to the directory.
    :return: The number of files or directories in the given path.
    """
    return len(list(path.glob("*")))


@click.command()
@click.option(
    "--datasets-location",
    type=click.Path(file_okay=False, dir_okay=True),
    default=DEFAULT_DATASET_PATH,
    show_default=True,
    help=(
        "The top-level directory that contains all datasets."
        "This should be the same location as`--datasets_location` used in `capture_images_pi.py`."
    ),
)
@click.option(
    "--upload-location",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="The directory that compressed datasets will be moved to for upload.",
)
@click.option(
    "--zip-uploads",
    type=click.BOOL,
    default=DEFAULT_UPLOADS_ZIP_ENABLED,
    show_default=True,
    help="Datasets will be zipped before being uploaded",
)
def begin_dataset_upload(datasets_location: str, upload_location: str, zip_uploads: bool) -> None:
    """
    Lists the candidate files for compression/upload and prompts user to decide which ones to
    actually compress and then expose to ownCloud for upload.

    \f # Truncate docs for click

    :param datasets_location: The directory to search for datasets in.
    :param upload_location: The location to put compressed datasets for upload.
    :param: zip_uploads: If given, compress datasets before upload.
    :return: None
    """
    LOGGER.info(f"Scanning datasets location: {datasets_location}")

    datasets_location_path = Path(datasets_location)
    upload_location_path = Path(upload_location)

    def _upload_directory_missing_files(uploaded_path: Path) -> Optional[Path]:
        """
        If there are files present in the dataset directory, but not in the upload directory,
        return the path to the dataset directory. Otherwise return None.
        :param uploaded_path: The path to scan.
        :return: The path to the dataset directory if the two directories do not have the same num
        files, None if otherwise.
        """

        dataset_location = datasets_location_path.joinpath(uploaded_path.name)
        return (
            dataset_location
            if (
                dataset_location.exists()
                and (_num_files_in_dir(dataset_location) != _num_files_in_dir(uploaded_path))
            )
            else None
        )

    questions = [
        inquirer.Checkbox(
            "upload",
            message="Which un-uploaded datasets would you like to upload to ownCloud?",
            choices=[
                (f"{path}, files: {_num_files_in_dir(path)}", path)
                for path in [path for path in datasets_location_path.iterdir() if path.is_dir()]
                if path.name
                not in [path.with_suffix("").name for path in upload_location_path.iterdir()]
            ],
        ),
        inquirer.Checkbox(
            "re-upload",
            message=(
                "These datasets were partially uploaded. "
                "Select the datasets you would like re-attempt to upload."
            ),
            choices=[
                (
                    f"dataset: {dataset.name} - "
                    f"{_num_files_in_dir(dataset)} files,"
                    f" uploaded: {upload_location_path.joinpath(dataset.name)} - "
                    f"{_num_files_in_dir(upload_location_path.joinpath(dataset.name))} files",
                    dataset,
                )
                for dataset in filter(
                    lambda d_p: d_p is not None,
                    [
                        _upload_directory_missing_files(path)
                        for path in upload_location_path.iterdir()
                        if path.is_dir()
                    ],
                )
            ],
        ),
    ]

    prompt_result = inquirer.prompt(questions)
    paths_to_datasets_to_upload = prompt_result["upload"] + prompt_result["re-upload"]

    if zip_uploads:
        processing_function = partial(
            compress_directory_move_to_upload_location, upload_directory=upload_location_path
        )
    else:
        processing_function = partial(
            copy_dataset_to_upload_location, upload_directory=upload_location_path
        )

    # Break up the compression/move logic across multiple processes so we can go faster.
    with Pool() as p:
        p.map(processing_function, paths_to_datasets_to_upload)


if __name__ == "__main__":
    begin_dataset_upload()  # pylint: disable=no-value-for-parameter
