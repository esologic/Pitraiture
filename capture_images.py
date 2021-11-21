"""
A command line interface to quickly take pictures using the Raspberry Pi camera.

TODO:
* Figure out reasonable ranges for shutter speed, red/blue gain.
"""

from datetime import datetime
from pathlib import Path
from time import sleep

import click

from pitraiture.camera_config import (
    AWBBlueGainType,
    AWBRedGainType,
    IsoType,
    PreviewTimeType,
    PromptOnTimeoutType,
    ResolutionType,
    ShutterSpeedType,
    configure_camera,
    verify_camera_config,
)
from pitraiture.cli_common import DEFAULT_DATASET_PATH
from pitraiture.file_common import IMAGE_EXTENSION, IMAGE_TIMESTAMP_FORMAT, create_image_filename
from pitraiture.logger_common import LOGGER

try:
    from picamera.camera import PiCamera
except ImportError:
    # This will be executed in non-Pis, for development.
    from fake_rpi.picamera import PiCamera


DEFAULT_CAPTURE_RESOLUTION_WIDTH = 2000
DEFAULT_CAPTURE_RESOLUTION_HEIGHT = 2000

# The amount of time in seconds to wait between the preview exiting
# and taking photos.
PREVIEW_CAPTURE_GRACE_PERIOD = 5

DEFAULT_ISO = 0
DEFAULT_SHUTTER_SPEED = 1000
DEFAULT_AWB_RED_GAIN = 3.125
DEFAULT_AWB_BLUE_GAIN = 1.96
DEFAULT_PREVIEW_TIME = 10
DEFAULT_PROMPT_ON_TIMEOUT = True
DEFAULT_NUM_PHOTOS_TO_TAKE = 10
DEFAULT_DATASET_NAME = "faces"
DEFAULT_DISPLAY_PHOTO_COUNT = True


@click.command()
@click.option(
    "--resolution",
    type=click.Tuple(types=(click.IntRange(min=0, max=4056), click.IntRange(min=0, max=3040))),
    default=(DEFAULT_CAPTURE_RESOLUTION_WIDTH, DEFAULT_CAPTURE_RESOLUTION_HEIGHT),
    show_default=True,
    help="Resolution of output images. Tuple, (width, height).",
)
@click.option(
    "--iso",
    type=click.IntRange(min=0, max=800),
    default=DEFAULT_ISO,
    show_default=True,
    help=(
        "ISO or film speed is a way to digitally increase the brightness of the image. Ideally "
        "one would use the lowest ISO value possible to still get a clear image, but it can be "
        "increased to make the image brighter. See: https://en.wikipedia.org/wiki/Film_speed "
        "for more details."
    ),
)
@click.option(
    "--shutter-speed",
    type=click.IntRange(0, DEFAULT_SHUTTER_SPEED * 1000),
    default=DEFAULT_SHUTTER_SPEED,
    show_default=True,
    help=(
        "How long the shutter is 'open' to capture an image in milliseconds. Shorter speeds "
        "will result in darker images but be able to capture moving objects more easily. Longer "
        "exposures will make it easier to see in darker lighting conditions but could have "
        "motion blur if the subject moves while being captured."
    ),
)
@click.option(
    "--awb-red-gain",
    type=click.FloatRange(0.0, 8.0),
    default=DEFAULT_AWB_RED_GAIN,
    show_default=True,
    help=(
        "Controls how much red light should be filtered into the image."
        "The two parameters `--awb-red-gain` and `--awb-blue-gain` should be set such that a "
        "known white object appears white in color in a resulting image."
    ),
)
@click.option(
    "--awb-blue-gain",
    type=click.FloatRange(0.0, 8.0),
    default=DEFAULT_AWB_BLUE_GAIN,
    show_default=True,
    help=(
        "Controls how much green light should be filtered into the image."
        "The two parameters `--awb-red-gain` and `--awb-blue-gain` should be set such that a "
        "known white object appears white in color in a resulting image."
    ),
)
@click.option(
    "--preview-time",
    type=click.IntRange(min=0),
    default=DEFAULT_PREVIEW_TIME,
    show_default=True,
    help=(
        "Controls the amount of time in seconds the preview is displayed before photo capturing "
        "starts."
    ),
)
@click.option(
    "--prompt-on-timeout",
    type=click.BOOL,
    default=DEFAULT_PROMPT_ON_TIMEOUT,
    show_default=True,
    help=(
        "If set to True, the user is asked if the preview looked okay before moving onto the "
        "capture phase. If set to False the capture phase will begin right away after the preview "
        "closes."
    ),
)
@click.option(
    "--datasets-location",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    default=DEFAULT_DATASET_PATH,
    show_default=True,
    help=(
        "The location of the directory that all datasets will be saved to on disk. "
        "This should be a place that has ample disk space, probably not on the Pi's SD card."
    ),
)
@click.option(
    "--dataset-name",
    type=click.STRING,
    default=DEFAULT_DATASET_NAME,
    show_default=True,
    help=(
        "Photos will be placed in a directory named after this value within the directory given by "
        "`--datasets-location`. Think of it like: /datasets_location/dataset_name/image1.png"
    ),
)
@click.option(
    "--num-photos-to-take",
    type=click.IntRange(min=1),
    default=DEFAULT_NUM_PHOTOS_TO_TAKE,
    show_default=True,
    help="The number of photos to take for this run.",
)
def capture_images(  # pylint: disable=too-many-locals
    resolution: ResolutionType,
    iso: IsoType,
    shutter_speed: ShutterSpeedType,
    awb_red_gain: AWBRedGainType,
    awb_blue_gain: AWBBlueGainType,
    preview_time: PreviewTimeType,
    prompt_on_timeout: PromptOnTimeoutType,
    datasets_location: str,
    dataset_name: str,
    num_photos_to_take: int,
) -> None:
    """
    Show a preview of the camera settings on the display attached to the Pi, and then capture a
    given number of images.

    \f # Truncate docs for click

    :param resolution: Resolution of output images. Tuple, (width, height).
    :param iso: ISO or film speed is a way to digitally increase the brightness of the image.
    Ideally one would use the lowest ISO value possible to still get a clear image, but it can be
    increased to make the image brighter. See: https://en.wikipedia.org/wiki/Film_speed for
    more details.
    :param shutter_speed: How long the shutter is 'open' to capture an image in milliseconds.
    Shorter speeds will result in darker images but be able to capture moving objects more easily.
    Longer exposures will make it easier to see in darker lighting conditions but could have motion
    blur if the subject moves while being captured.
    :param awb_red_gain: Controls how much red light should be filtered into the image. The two
    parameters `awb_red_gain` and `awb_blue_gain` should be set such that a known white object
    appears white in color in a resulting image.
    :param awb_blue_gain: Controls how much green light should be filtered into the image.
    The two parameters `awb_red_gain` and `awb_blue_gain` should be set such that a known white
    object appears white in color in a resulting image.
    :param preview_time: Controls the amount of time in seconds the preview is displayed before
    photo capturing starts.
    :param prompt_on_timeout: If set to True, the user is asked if the preview looked okay before
    moving onto the capture phase. If set to False the capture phase will begin right away after
    the preview closes.
    :param datasets_location: The location of the directory that all datasets will be saved to on
    disk. This should be a place that has ample disk space, probably not on the Pi's SD card.
    :param dataset_name: Photos will be placed in a directory named after this value within the
    directory given by `datasets_location`.
    Think of it like: /datasets_location/dataset_name/image1.png
    :param num_photos_to_take: The number of photos to take for this run.
    :return: None
    """

    images_directory = Path(datasets_location).joinpath(dataset_name)

    if images_directory.exists():
        LOGGER.warning(
            f"Directory {str(images_directory)} already exists, you'll be adding to an "
            f"existing dataset rather than creating a new one."
        )
    else:
        images_directory.mkdir(exist_ok=True)

    with configure_camera(
        resolution=resolution,
        iso=iso,
        shutter_speed=shutter_speed,
        awb_red_gain=awb_red_gain,
        awb_blue_gain=awb_blue_gain,
    ) as camera:

        LOGGER.info("Camera configured. Opening Preview.")

        if not verify_camera_config(
            camera=camera,
            preview_time=preview_time,
            prompt_on_timeout=prompt_on_timeout,
            preview_capture_path=images_directory.joinpath(
                f"{dataset_name}_PREVIEW_{datetime.now().strftime(IMAGE_TIMESTAMP_FORMAT)}."
                f"{IMAGE_EXTENSION}"
            ),
        ):
            LOGGER.info("Camera config rejected after preview. Exiting.")
            return None

        camera.start_preview()

        LOGGER.info(f"Waiting {PREVIEW_CAPTURE_GRACE_PERIOD} seconds before capturing photos...")

        sleep(PREVIEW_CAPTURE_GRACE_PERIOD)

        LOGGER.info("Starting to capture images...")

        capture_start_time = datetime.now()

        for index in range(int(num_photos_to_take)):
            image = str(
                images_directory.joinpath(
                    create_image_filename(dataset_name=dataset_name, capture_time=datetime.now())
                )
            )

            LOGGER.info(f"Capturing image {index}/{num_photos_to_take} - {image}")
            camera.capture(image, format=IMAGE_EXTENSION)

        capture_end_time = datetime.now()

        camera.stop_preview()

        LOGGER.info(
            f"Captured all images. Capture rate: "
            f"{num_photos_to_take / (capture_end_time-capture_start_time).total_seconds()} "
            f"Photos per second. Bye."
        )

        return None


if __name__ == "__main__":
    capture_images()  # pylint: disable=no-value-for-parameter
