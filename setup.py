# -*- coding: UTF-8 -*
# XXX-TODO
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
# XXX-JE-MAYBE:
from setuptools_behave import behave_test

# -----------------------------------------------------------------------------
# CONFIGURATION:
# -----------------------------------------------------------------------------
python_version = float("%s.%s" % sys.version_info[:2])
BEHAVE = os.path.join(HERE, "behave")
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
    version="0.1.0.dev0",
    description="cmake-build is a small wrapper around CMake to simplify its usage",
    long_description=description,
    author="Jens Engel",
    author_email="jenisys@users.noreply.github.com",
    url="http://github.com/jenisys/cmake-build",
    provides = ["cmake_build"],
    packages = find_packages_by_root_package("cmake_build"),
    py_modules = ["setuptools_behave"],
    entry_points={
        "console_scripts": [
            "cmake-build = cmake_build.__main__:main"
        ],
        "distutils.commands": [
            "behave_test = setuptools_behave:behave_test"
        ]
    },
    # -- REQUIREMENTS:
    # SUPPORT: python2.7, python3.3 (or higher)
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*",
    install_requires=[
        "path.py >= 10.1",
        "six >= 1.12.0",
        "enum34; python_version < '3.4'",
    ],
    # XXX test_suite="nose.collector",
    tests_require=[
        "pytest >= 3.0",
        "pytest-html >= 1.19.0",
        "mock >= 1.1",
        "PyHamcrest >= 1.8",
    ],
    cmdclass = {
        "behave_test": behave_test,
    },
    extras_require={
        'docs': ["sphinx >= 1.8", "sphinx_bootstrap_theme >= 0.6"],
        'develop': [
            "coverage", "pytest >= 3.0", "pytest-cov", "tox",
            "invoke >= 1.2.0", "path.py >= 10.1", "pycmd",
            "pathlib",  # python_version <= '3.4'
            "modernize >= 0.5",
            "pylint",
        ],
    },
    # MAYBE-DISABLE: use_2to3
    use_2to3= bool(python_version >= 3.0),
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",   # XXX
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        # XXX-MAYBE: "Programming Language :: Python :: Implementation :: CPython",
        # XXX-MAYBE:"Programming Language :: Python :: Implementation :: Jython",
        # XXX-MAYBE:"Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",  # XXX
        "License :: OSI Approved :: BSD License",
    ],
    zip_safe = True,
)


