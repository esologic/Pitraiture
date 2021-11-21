# Pitraiture - pitraiture 

![Hardware setup for this project](./setup.JPG)

Capture photos using a Raspberry Pi HQ camera for input into stylegan training.

See [esologic.com/gance](https://www.esologic.com/gance) for more information.


## Usage

```
$ python capture_images.py --help
Usage: capture_images.py [OPTIONS]

  Show a preview of the camera settings on the display attached to the Pi, and
  then capture a given number of images.

Options:
  --resolution <INTEGER RANGE INTEGER RANGE>...
                                  Resolution of output images. Tuple, (width,
                                  height).  [default: 2000, 2000]
  --iso INTEGER RANGE             ISO or film speed is a way to digitally
                                  increase the brightness of the image.
                                  Ideallyone would use the lowest ISO value
                                  possible to still get a clear image, but it
                                  can be increased to make the image brighter.
                                  See:
                                  https://en.wikipedia.org/wiki/Film_speed for
                                  more details.  [default: 0; 0<=x<=800]
  --shutter-speed INTEGER RANGE   How long the shutter is 'open' to capture an
                                  image in milliseconds. Shorter speeds will
                                  result in darker images but be able to
                                  capture moving objects more easily.
                                  Longerexposures will make it easier to see
                                  in darker lighting conditions but could have
                                  motion blur if the subject moves while being
                                  captured.  [default: 1000; 0<=x<=1000000]
  --awb-red-gain FLOAT RANGE      Controls how much red light should be
                                  filtered into the image.The two parameters
                                  `--awb-red-gain` and `--awb-blue-gain`
                                  should be set such that a known white object
                                  appears white in color in a resulting image.
                                  [default: 3.125; 0.0<=x<=8.0]
  --awb-blue-gain FLOAT RANGE     Controls how much green light should be
                                  filtered into the image.The two parameters
                                  `--awb-red-gain` and `--awb-blue-gain`
                                  should be set such that a known white object
                                  appears white in color in a resulting image.
                                  [default: 1.96; 0.0<=x<=8.0]
  --preview-time INTEGER RANGE    Controls the amount of time in seconds the
                                  preview is displayed before photo capturing
                                  starts.  [default: 10; x>=0]
  --prompt-on-timeout BOOLEAN     If set to True, the user is asked if the
                                  preview looked okay before moving onto the
                                  capture phase. If set to False the capture
                                  phase will begin right away after the
                                  preview closes.  [default: True]
  --datasets-location DIRECTORY   The location of the directory that all
                                  datasets will be saved to on disk. This
                                  should be a place that has ample disk space,
                                  probably not on the Pi's SD card.  [default:
                                  ./datasets]
  --dataset-name TEXT             Photos will be placed in a directory named
                                  after this value within the directory given
                                  by `--datasets-location`. Think of it like:
                                  /datasets_location/dataset_name/image1.png
                                  [default: faces]
  --num-photos-to-take INTEGER RANGE
                                  The number of photos to take for this run.
                                  [default: 10; x>=1]
  --help                          Show this message and exit.
```


## Getting Started

### Python Dependencies

See the `requirements` directory for required Python modules for building, testing, developing etc.
They can all be installed in a [virtual environment](https://docs.python.org/3/library/venv.html).

Use the tool script to install python dependencies on a raspberry pi to take photos:

```
source ./tools/create_venv_pi.sh
```

or, install mock dependencies that will let you develop the tool on any kind of system, 
PC or otherwise:

```
source ./tools/create_venv.sh
```

## Developer Guide

The following is documentation for developers that would like to contribute
to Pitraiture.

### Pycharm Note

Make sure you mark `pitraiture` and `./test` as source roots!

### Testing

This project uses pytest to manage and run unit tests. Unit tests located in the `test` directory 
are automatically run during the CI build. You can run them manually with:

```
./tools/run_tests.sh
```

### Local Linting

There are a few linters/code checks included with this project to speed up the development process:

* Black - An automatic code formatter, never think about python style again.
* Isort - Automatically organizes imports in your modules.
* Pylint - Check your code against many of the python style guide rules.
* Mypy - Check your code to make sure it is properly typed.

You can run these tools automatically in check mode, meaning you will get an error if any of them
would not pass with:

```
./tools/run_checks.sh
```

Or actually automatically apply the fixes with:

```
./tools/apply_linters.sh
```

There are also scripts in `./tools/` that include run/check for each individual tool.


### Using pre-commit

First you need to init the repo as a git repo with:

```
git init
```

Then you can set up the git hook scripts with:

```
pre-commit install
```

By default:

* black
* pylint
* isort
* mypy

Are all run in apply-mode and must pass in order to actually make the commit.

Also by default, pytest needs to pass before you can push.

If you'd like skip these checks you can commit with:

```
git commit --no-verify
```

If you'd like to quickly run these pre-commit checks on all files (not just the staged ones) you
can run:

```
pre-commit run --all-files
```

