# -*- coding: UTF-8 -*
"""
Setup script for cmake-build.

USAGE:
    python setup.py install

REQUIRES:
* setuptools >= 36.2.0

SEE ALSO:
* https://setuptools.readthedocs.io/en/latest/history.html
"""

import sys
import os.path

HERE0 = os.path.dirname(__file__) or os.curdir
os.chdir(HERE0)
HERE = os.curdir
sys.path.insert(0, HERE)

from setuptools import find_packages, setup

# -----------------------------------------------------------------------------
# CONFIGURATION:
# -----------------------------------------------------------------------------
python_version = float("%s.%s" % sys.version_info[:2])
README = os.path.join(HERE, "README.rst")
description = "".join(open(README).readlines()[4:])

# -----------------------------------------------------------------------------
# UTILITY:
# -----------------------------------------------------------------------------
def find_packages_by_root_package(where):
    """
    Better than excluding everything that is not needed,
    collect only what is needed.
    """
    root_package = os.path.basename(where)
    packages = [ "%s.%s" % (root_package, sub_package)
                 for sub_package in find_packages(where)]
    packages.insert(0, root_package)
    return packages


# -----------------------------------------------------------------------------
# SETUP:
# -----------------------------------------------------------------------------
setup(
    name="cmake-build",
    version="0.2.4.dev1",
    description="cmake-build is a small wrapper around CMake to simplify its usage as build system",
    long_description=description,
    author="Jens Engel",
    author_email="jenisys@users.noreply.github.com",
    url="http://github.com/jenisys/cmake-build",
    provides = ["cmake_build"],
    packages = find_packages_by_root_package("cmake_build"),
    entry_points={
        "console_scripts": [
            "cmake-build = cmake_build.__main__:program.run"
        ],
    },
    # -- REQUIREMENTS:
    # SUPPORT: python2.7, python3.3 (or higher)
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*",
    install_requires=[
        "invoke >= 1.7.0",
        "six >= 1.16.0",
        "pycmd",
        # DISABLED: "git+https://github.com/jenisys/invoke-cleanup@v0.3.7",
        # NOT-NEEDED: "click >= 7.0.0",
        # -- HINT: path.py => path (python-install-package was renamed for python3)
        "path.py >= 11.5.0; python_version <  '3.5'",
        "path >= 13.1.0;    python_version >= '3.5'",
        "pathlib2; python_version < '3.4'",
        # MAYBE: "backports.shutil_which; python_version <= '3.3'",
    ],
    tests_require=[
        "pytest <  5.0; python_version < '3.0'",
        "pytest >= 5.0; python_version >= '3.0'",
        "pytest-html >= 1.19.0",
        # -- DISABLED: "behave >= 1.2.6",
        "behave @ git+https://github.com/behave/behave.git@v1.2.7.dev5",
        "behave4cmd0 @ git+https://github.com/behave/behave4cmd0.git@v1.2.7.dev6"
        "PyHamcrest >= 1.9",
        # PREPARED: "mock >= 2.0",
    ],
    extras_require={
        'docs': ["sphinx >= 1.8", "sphinx_bootstrap_theme >= 0.6"],
        'develop': [
            "coverage",
            "pytest <  5.0; python_version < '3.0'",
            "pytest >= 5.0; python_version >= '3.0'",
            "pytest-html >= 1.19.0",
            "behave >= 1.2.6",
            # DISABLED: "git+https://github.com/behave/behave@v1.2.7.dev5",
            "PyHamcrest >= 1.9",
            "tox < 4.0",
            "modernize >= 0.5",
            "pylint",
        ],
    },
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Invoke",
        "Framework :: CMake",   # USING: CMake <https://cmake.org>
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",  # FOR: Intended Audience
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Build Tools :: CMake",
        "Topic :: Utilities",
    ],
    zip_safe = True,
)


