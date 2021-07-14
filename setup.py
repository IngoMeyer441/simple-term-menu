import os
import runpy
import subprocess
from distutils.cmd import Command
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple, cast

from setuptools import setup


class PyinstallerCommand(Command):
    description = "create a self-contained executable with PyInstaller"
    user_options = []  # type: List[Tuple[str, Optional[str], str]]

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        with TemporaryDirectory() as temp_dir:
            subprocess.check_call(["python3", "-m", "venv", os.path.join(temp_dir, "env")])
            subprocess.check_call([os.path.join(temp_dir, "env/bin/pip"), "install", "."])
            subprocess.check_call([os.path.join(temp_dir, "env/bin/pip"), "install", "pyinstaller<4.4"])
            with open(os.path.join(temp_dir, "entrypoint.py"), "w") as f:
                f.write(
                    """
#!/usr/bin/env python3

from simple_term_menu import main


if __name__ == "__main__":
    main()
                    """.strip()
                )
            subprocess.check_call(
                [
                    os.path.join(temp_dir, "env/bin/pyinstaller"),
                    "--clean",
                    "--name=simple-term-menu",
                    "--onefile",
                    "--strip",
                    os.path.join(temp_dir, "entrypoint.py"),
                ]
            )


def get_version_from_pyfile(version_file: str = "simple_term_menu.py") -> str:
    file_globals = runpy.run_path(version_file)
    return cast(str, file_globals["__version__"])


def get_long_description_from_readme(readme_filename: str = "README.md") -> Optional[str]:
    long_description = None
    if os.path.isfile(readme_filename):
        with open(readme_filename, "r", encoding="utf-8") as readme_file:
            long_description = readme_file.read()
    return long_description


version = get_version_from_pyfile()
long_description = get_long_description_from_readme()

setup(
    name="simple-term-menu",
    version=version,
    py_modules=["simple_term_menu"],
    python_requires="~=3.5",
    entry_points={"console_scripts": ["simple-term-menu = simple_term_menu:main"]},
    cmdclass={"bdist_pyinstaller": PyinstallerCommand},
    author="Ingo Meyer",
    author_email="i.meyer@fz-juelich.de",
    description="A Python package which creates simple interactive menus on the command line.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/IngoMeyer441/simple-term-menu",
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
