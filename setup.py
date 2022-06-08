#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ["numpy", "pandas", "xlrd", "openpyxl", "matplotlib"]
test_requirements = ["pytest>=6.2.5"]
development_requirements = ["pre-commit"]

setup(
    author="Lennart Damen",
    author_email="lennart.damen@bigdatarepublic.nl",
    python_requires="==3.7.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
    description="Matching LIS to TecDoc",
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        "dev": test_requirements + development_requirements,
        "test": test_requirements,
    },
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    name="olyslager",
    packages=find_packages(include=["oly_matching", "oly_matching.*"]),
    version="0.0.0",
    zip_safe=False,
)
