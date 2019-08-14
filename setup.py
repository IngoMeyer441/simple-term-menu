import os
import runpy
from setuptools import setup, find_packages


def get_version_from_pyfile(version_file="simple_term_menu.py"):
    file_globals = runpy.run_path(version_file)
    return file_globals["__version__"]


def get_install_requires_from_requirements(requirements_filename="requirements.txt"):
    try:
        with open(requirements_filename, "r", encoding="utf-8") as requirements_file:
            requirements = requirements_file.readlines()
    except OSError:
        import logging

        logging.warning("Could not read the requirements file.")
    return requirements


def get_long_description_from_readme(readme_filename="README.md"):
    long_description = None
    if os.path.isfile(readme_filename):
        with open(readme_filename, "r", encoding="utf-8") as readme_file:
            long_description = readme_file.read()
    return long_description


version = get_version_from_pyfile()
long_description = get_long_description_from_readme()
install_requires = get_install_requires_from_requirements()

setup(
    name="simple-term-menu",
    version=version,
    py_modules=["simple_term_menu"],
    python_requires="~=3.3",
    install_requires=install_requires,
    author="Ingo Heimbach",
    author_email="i.heimbach@fz-juelich.de",
    description="A Python package which creates simple interactive menus on the command line.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/IngoHeimbach/simple-term-menu",
    keywords=["terminal", "menu", "choice"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Terminals",
        "Topic :: Utilities",
    ],
)
