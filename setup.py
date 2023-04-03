#!/usr/bin/env python3

from setuptools import setup
from pathlib import Path
import re


root_dir = Path(__file__).parent

version = dict()
with open(str(root_dir/"version.txt")) as version_fd:
    for line in version_fd:
        level, no = re.fullmatch(r'^\s*VERSION_([A-Z]+)\s+([0-9]+)\s*$', line).groups()
        version[level.lower()] = int(no)

with open(str(root_dir/"requirements.txt")) as req_fd:
    requirements = [package.strip() for package in req_fd]


setup(name="approxism",
    version=f"{version['major']}.{version['minor']}.{version['patch']}",
    description="Approximate String Matching using libsdcxx",
    author="Václav Krpec",
    author_email="vencik@razdva.cz",
    url="https://github.com/vencik/approxism",
    license="BSD-3-Clause license",
    long_description=(root_dir/"README.md").read_text(),
    long_description_content_type="text/markdown",
    license_files=["LICENSE"],
    package_dir={"": "src"},
    include_package_data=True,
    packages=[
        "approxism",
        "approxism.transforms",
    ],
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Text Processing",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
    ],
)
