import zipfile
import glob
import os
import pulumi
from os import path
import stat
from pathlib import Path
import fnmatch
from .utils import format_resource_name, format_file_name

# Files pattern to ignore for deterministic zip archive
IGNORE_PATTERNS = ["*.py[c|o]", "*/__pycache__*", "__pycache__*", "*.dist-info*"]

# Constand DateTime
CONST_DATETIME = (2020, 1, 1, 0, 0, 0)


class ZipPackage:
    """
    Creates Zip archive and injects requirements into the zip archive.
    """

    def __init__(
        self,
        resource_name,
        project_root,
        include=["**"],
        exclude=[],
        target_folder="dist/",
        install_folder="requirements/",
    ):
        self.resource_name = resource_name
        self.project_root = Path(project_root)
        self.target_folder = Path(target_folder)
        self.install_folder = self.target_folder / install_folder
        self.zipfile_name = format_file_name(resource_name, "lambda.zip")
        self.zip_path = self.get_path(self.zipfile_name)
        self.include = include.copy()
        self.exclude = exclude.copy()
        self.install_path = self.project_root / self.install_folder

        self.exclude.append(self.target_folder / "**")
        self.installed_requirements = self.project_root / self.install_folder

        # create temporary directory if not exists
        if not os.path.isdir(self.installed_requirements):
            os.makedirs(self.installed_requirements, exist_ok=True)

    def get_path(self, file_name):
        """Return absolute file path"""
        return self.project_root / self.target_folder / file_name

    def _match_glob_files(self, patterns: list):
        """
        Returns list of files matching the glob pattern
        """
        return [
            f
            for pattern in patterns
            for f in glob.glob(str(self.project_root / pattern), recursive=True)
        ]

    def filter_package(self):
        """
        Filters files based on exclude and include option
        """
        self.exclude = [str(Path(p)) for p in self.exclude]
        self.include = [str(Path(p)) for p in self.include]
        self.exclude_files = self._match_glob_files(self.exclude)
        self.include_files = self._match_glob_files(self.include)

        filtered_package = []
        if "**" in self.exclude and "**" not in self.include:
            filtered_package = set(self.include_files)
        elif "**" not in self.exclude:
            filtered_package = set(self.include_files) - set(self.exclude_files)
        return list(filtered_package)

    def zip_package(self, requirements=True):
        """
        Creates zip archive of file and folders
        and inject requirements into the zip package when "requirements=True"
        """
        self._add_files(self.zip_path, self.filter_package(), "w", self.project_root)
        if requirements:
            self._inject_requirements()
        return self.zip_path

    def zip_requirements(self):
        """
        Creates zip archive of dependencies requirements
        """
        requirement_files = glob.glob(
            os.path.join(self.installed_requirements, "**"), recursive=True
        )
        requirements_zip_path = self.get_path(
            format_file_name(self.resource_name, "requirements.zip")
        )
        self._add_files(
            requirements_zip_path,
            requirement_files,
            base_path=self.installed_requirements,
        )
        return requirements_zip_path

    def _add_files(self, zip_path, files, mode="w", base_path=""):
        """
        Utility function to add new files in existing/new zip and create deterministic zip

        Reference: https://github.com/bboe/deterministic_zip#how-does-it-work
        """
        zip_file = zipfile.ZipFile(zip_path, mode)

        # sort files to preserve the order
        for file in filter(self.is_file_allowed, sorted(files)):
            zip_path = os.path.relpath(file, base_path)

            zip_info = zipfile.ZipInfo.from_file(file, zip_path)

            # set consistent date info for the file
            zip_info.date_time = CONST_DATETIME

            if os.path.isfile(file):
                with open(file, "rb") as fp:
                    zip_file.writestr(
                        zip_info, fp.read(), compress_type=zipfile.ZIP_DEFLATED
                    )

        zip_file.close()

    def is_file_allowed(self, file_name):
        """
        Ignore dynamic & redundant files/folders for deterministic zip archive
        """
        for pattern in IGNORE_PATTERNS:
            if fnmatch.fnmatch(Path(file_name), pattern):
                return False
        return True

    def _inject_requirements(self):
        """
        Inject requirements into the package archive.
        """
        requirement_files = glob.glob(
            str(self.installed_requirements / "**"), recursive=True
        )
        self._add_files(
            zip_path=self.zip_path,
            files=requirement_files,
            mode="a",
            base_path=self.installed_requirements,
        )
