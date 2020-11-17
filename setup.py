# -*- coding: utf-8 -*-
from __future__ import print_function

import imp
import os
import subprocess
import sys
from distutils import spawn

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

try:
    import colorama

    colorama.init()  # Initialize colorama on Windows
except ImportError:
    # Don't require colorama just for running paver tasks. This allows us to
    # run `paver install' without requiring the user to first have colorama
    # installed.
    pass

# Add the current directory to the module search path.
sys.path.insert(0, os.path.abspath("."))

## Constants
CODE_DIRECTORY = "gn2gn"
DOCS_DIRECTORY = "docs"
TESTS_DIRECTORY = "tests"
PYTEST_FLAGS = ["--doctest-modules"]

# Import metadata. Normally this would just be:
#
#     from gn2gn_client import metadata
#
# However, when we do this, we also import `gn2gn_client/__init__.py'. If this
# imports names from some other modules and these modules have third-party
# dependencies that need installing (which happens after this file is run), the
# script will crash. What we do instead is to load the metadata module by path
# instead, effectively side-stepping the dependency problem. Please make sure
# metadata has no dependencies, otherwise they will need to be added to
# the setup_requires keyword.
metadata = imp.load_source("metadata", os.path.join(CODE_DIRECTORY, "metadata.py"))


## Miscellaneous helper functions


def get_project_files():
    """Retrieve a list of project files, ignoring hidden files.

    :return: sorted list of project files
    :rtype: :class:`list`
    """
    if is_git_project() and has_git():
        return get_git_project_files()

    project_files = []
    for top, subdirs, files in os.walk("."):
        for subdir in subdirs:
            if subdir.startswith("."):
                subdirs.remove(subdir)

        for f in files:
            if f.startswith("."):
                continue
            project_files.append(os.path.join(top, f))

    return project_files


def is_git_project():
    return os.path.isdir(".git")


def has_git():
    return bool(spawn.find_executable("git"))


def get_git_project_files():
    """Retrieve a list of all non-ignored files, including untracked files,
    excluding deleted files.

    :return: sorted list of git project files
    :rtype: :class:`list`
    """
    cached_and_untracked_files = git_ls_files(
        "--cached",  # All files cached in the index
        "--others",  # Untracked files
        # Exclude untracked files that would be excluded by .gitignore, etc.
        "--exclude-standard",
    )
    uncommitted_deleted_files = git_ls_files("--deleted")

    # Since sorting of files in a set is arbitrary, return a sorted list to
    # provide a well-defined order to tools like flake8, etc.
    return sorted(cached_and_untracked_files - uncommitted_deleted_files)


def git_ls_files(*cmd_args):
    """Run ``git ls-files`` in the top-level project directory. Arguments go
    directly to execution call.

    :return: set of file names
    :rtype: :class:`set`
    """
    cmd = ["git", "ls-files"]
    cmd.extend(cmd_args)
    return set(subprocess.check_output(cmd).splitlines())


def print_success_message(message):
    """Print a message indicating success in green color to STDOUT.

    :param message: the message to print
    :type message: :class:`str`
    """
    try:
        import colorama

        print(colorama.Fore.GREEN + message + colorama.Fore.RESET)
    except ImportError:
        print(message)


def print_failure_message(message):
    """Print a message indicating failure in red color to STDERR.

    :param message: the message to print
    :type message: :class:`str`
    """
    try:
        import colorama

        print(colorama.Fore.RED + message + colorama.Fore.RESET, file=sys.stderr)
    except ImportError:
        print(message, file=sys.stderr)


def read(filename):
    """Return the contents of a file.

    :param filename: file path
    :type filename: :class:`str`
    :return: the file's content
    :rtype: :class:`str`
    """
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


def _lint():
    """Run lint and return an exit code."""
    # Flake8 doesn't have an easy way to run checks using a Python function, so
    # just fork off another process to do it.

    # Python 3 compat:
    # - The result of subprocess call outputs are byte strings, meaning we need
    #   to pass a byte string to endswith.
    project_python_files = [
        filename for filename in get_project_files() if filename.endswith(b".py")
    ]
    retcode = subprocess.call(["flake8", "--max-complexity=10"] + project_python_files)
    if retcode == 0:
        print_success_message("No style errors")
    return retcode


def _test():
    """Run the unit tests.

    :return: exit code
    """
    # Make sure to import pytest in this function. For the reason, see here:
    # <http://pytest.org/latest/goodpractises.html#integration-with-setuptools-test-commands>  # NOPEP8
    import pytest

    # This runs the unit tests.
    # It also runs doctest, but only on the modules in TESTS_DIRECTORY.
    return pytest.main(PYTEST_FLAGS + [TESTS_DIRECTORY])


def _test_all():
    """Run lint and tests.

    :return: exit code
    """
    return _lint() + _test()


# The following code is to allow tests to be run with `python setup.py test'.
# The main reason to make this possible is to allow tests to be run as part of
# Setuptools' automatic run of 2to3 on the source code. The recommended way to
# run tests is still `paver test_all'.
# See <http://pythonhosted.org/setuptools/python3.html>
# Code based on <http://pytest.org/latest/goodpractises.html#integration-with-setuptools-test-commands>  # NOPEP8
class TestAllCommand(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        # These are fake, and just set to appease distutils and setuptools.
        self.test_suite = True
        self.test_args = []

    def run_tests(self):
        raise SystemExit(_test_all())


# define install_requires for specific Python versions
python_version_specific_requires = []

# as of Python >= 2.7 and >= 3.2, the argparse module is maintained within
# the Python standard library, otherwise we install it as a separate package
if sys.version_info < (2, 7) or (3, 0) <= sys.version_info < (3, 3):
    python_version_specific_requires.append("argparse")

# See here for more options:
# <http://pythonhosted.org/setuptools/setuptools.html>
setup_dict = dict(
    name=metadata.package,
    version=metadata.version,
    author=metadata.authors[0],
    author_email=metadata.emails[0],
    maintainer=metadata.authors[0],
    maintainer_email=metadata.emails[0],
    url=metadata.url,
    description=metadata.description,
    long_description=read("README.rst"),
    # Find a list of classifiers here:
    # <http://pypi.python.org/pypi?%3Aaction=list_classifiers>
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Software Distribution",
    ],
    packages=find_packages(exclude=(TESTS_DIRECTORY,)),
    install_requires=[
        "requests>=2.21.0",
        "toml>=0.10.0",
        "coloredlogs>=7.3",
        "schema>=0.6.7",
        "sqlalchemy>=1.2.18",
    ]
    + python_version_specific_requires,
    # Allow tests to be run with `python setup.py test'.
    tests_require=[
        "pytest>=3.10.1",
        "mock>=2.0.0",
        "flake8>=3.6.0",
    ],
    cmdclass={"test": TestAllCommand},
    zip_safe=False,
    entry_points={
        "console_scripts": ["gn2gn_cli = gn2gn.transfer_gn:run"],
        # if you have a gui, use this
        # 'gui_scripts': [
        #     'gn2gn_client_gui = gn2gn_client.gui:entry_point'
        # ]
    },
)


def main():
    setup(**setup_dict)


if __name__ == "__main__":
    main()