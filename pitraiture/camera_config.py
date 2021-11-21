"""
Common functionality required to set up the picamera.
"""

import typing as t
from fractions import Fraction
from pathlib import Path
from time import sleep

import inquirer

from pitraiture.file_common import IMAGE_EXTENSION
from pitraiture.logger_common import LOGGER

try:
    import picamera
except ImportError:
    from fake_rpi import picamera


DEFAULT_FRAMERATE = 30

IsoType = t.NewType("IsoType", int)
ShutterSpeedType = t.NewType("ShutterSpeedType", int)
AWBRedGainType = t.NewType("AWBRedGainType", float)
AWBBlueGainType = t.NewType("AWBBlueGainType", float)
PreviewTimeType = t.NewType("PreviewTimeType", float)
PromptOnTimeoutType = t.NewType("PromptOnTimeoutType", bool)
ResolutionType = t.NewType("ResolutionType", t.Tuple[int, int])  # (width, height)


def configure_camera(
    resolution: ResolutionType,
    iso: IsoType,
    shutter_speed: ShutterSpeedType,
    awb_red_gain: AWBRedGainType,
    awb_blue_gain: AWBBlueGainType,
) -> picamera.camera.PiCamera:
    """
    Helper function to set the values we care about in the PiCamera's configuration.
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
    :return: The configured PiCamera object
    """

    camera = picamera.PiCamera(
        resolution=resolution,
        framerate=DEFAULT_FRAMERATE,
    )

    camera.awb_mode = "off"

    # Now fix the values
    camera.iso = iso
    camera.shutter_speed = shutter_speed
    camera.awb_gains = (Fraction(awb_red_gain), Fraction(awb_blue_gain))

    return camera


def verify_camera_config(
    camera: picamera.camera.PiCamera,
    preview_time: PreviewTimeType,
    prompt_on_timeout: PromptOnTimeoutType,
    preview_capture_path: Path,
) -> bool:
    """
    Display a preview of the camera's output on the monitor the pi is currently attached to.
    Also save a capture to the given path so it can be quickly inspected.
    If `prompt_on_timeout` is True, ask the user if the settings look okay before returning.
    :param camera: The camera to preview.
    :param preview_time: The amount of time to display the preview for.
    :param prompt_on_timeout: if True, ask the user if the settings look okay before returning.
    If they respond False, return False. Otherwise return True.
    :param preview_capture_path:
    :return: See docs for `prompt_on_timeout`.
    """

    camera.start_preview()
    sleep(preview_time)

    LOGGER.info(f"Capturing Preview Image {preview_capture_path}")
    camera.capture(str(preview_capture_path), format=IMAGE_EXTENSION)
    LOGGER.info("Preview Image Available.")

    camera.stop_preview()

    # We wait until after the sleep because if these settings are calculated automatically
    # they'll need time to settle.
    LOGGER.info(
        f"Camera Settings - "
        f"iso: {camera.iso}, "
        f"shutter speed: {camera.shutter_speed}, "
        f"exposure speed: {camera.exposure_speed}, "
        f"awb gains: {camera.awb_gains}"
    )

    approved = True
    if prompt_on_timeout:
        approved = bool(
            inquirer.prompt(
                [
                    inquirer.List(
                        "settings",
                        message="Did the settings look good?",
                        choices=["Yes (Continue)", "No (Exit)"],
                    )
                ]
            )["settings"]
            == "Yes (Continue)"
        )

    # Always delete the preview file, it shouldn't be a part of the dataset
    preview_capture_path.unlink()
    return approved
