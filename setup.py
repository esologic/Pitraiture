"""Use this file to install pitraiture as a module"""

from distutils.core import setup
from setuptools import find_packages
from typing import List


def prod_dependencies() -> List[str]:
    """
    Pull the dependencies from the requirements dir
    :return: Each of the newlines, strings of the dependencies
    """
    with open("./requirements/prod.txt", "r") as file:
        return file.read().splitlines()


setup(
    name="pitraiture",
    version="0.0.1",
    description="Capture photos using a Raspberry Pi HQ camera for input into stylegan training.",
    author="Devon Bray",
    author_email="dev@esologic.com",
    packages=find_packages(),
    install_requires=prod_dependencies(),
)
