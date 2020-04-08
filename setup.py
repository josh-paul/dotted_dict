#!/usr/bin/env python

from setuptools import find_packages, setup

desc = ""
with open("README.rst") as f:
    desc = f.read()

setup(
    name="dotted_dict",
    version="1.1.3",
    description=("dict object with support for addressing keys in dot notation."),
    long_description=desc,
    url="https://github.com/josh-paul/dotted_dict",
    author="Josh Paul",
    author_email="trevalen@me.com",
    license="Apache v2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="dotted dict dotted_dict",
    packages=find_packages(exclude=["contrib", "docs", "examples", "test*"]),
    install_requires=[],
    extras_require={},
    package_data={},
    data_files=[],
    entry_points={},
)
