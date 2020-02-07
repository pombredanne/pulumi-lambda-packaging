import zipfile
import glob
import os
import pulumi
from .config import Config
from os import path


class ZipPackage(Config):
    """
    Creates Zip archive and injects requirements into the zip archive.
    """
    def __init__(self,
                 project_root,
                 include=["**"],
                 exclude=[]
                 ):
        super().__init__()
        self.project_root = project_root
        self.zip_path = path.join(self.project_root, self.target_folder, self.zipfile_name)
        self.include = include
        self.exclude = exclude
        self.zip_path = self.get_path(self.zipfile_name)
        self.exclude.append(path.join(self.target_folder, "**"))
        self.installed_requirements = path.join(self.project_root, self.install_folder)
        if not os.path.isdir(self.installed_requirements):
            os.makedirs(self.installed_requirements, exist_ok=True)

    def get_path(self, file_name):
        """Return absolute file path"""
        return path.join(self.project_root, self.target_folder, file_name)

    def _match_glob_files(self, patterns: list):
        """
        Returns list of files matching the glob pattern
        """
        return [f for pattern in patterns
                for f in glob.glob(os.path.join(self.project_root, pattern), recursive=True)
                ]

    def filter_package(self):
        """
        Filters files based on exclude and include option
        """
        self.exclude_files = self._match_glob_files(self.exclude)
        self.include_files = self._match_glob_files(self.include)

        filtered_package = []
        if "**" in self.exclude:
            filtered_package = set(self.include_files)
        else:
            filtered_package = set(self.include_files) - \
                set(self.exclude_files)
        return filtered_package

    def zip_package(self, requirements=True):
        """
        Creates zip archive of file and folders
        and inject requirements into the zip "requirements.txt=True"
        """
        self._add_files(self.zip_path, self.filter_package(), 'w', self.project_root)
        if requirements:
            self._inject_requirements()
        return self.zip_path

    def zip_requirements(self):
        """
        Creates zip archive of dependencies requirements
        """
        requirement_files = glob.glob(os.path.join(
            self.installed_requirements, '**'), recursive=True)
        requirements_zip_path = self.get_path('requirements.txt')
        self._add_files(requirements_zip_path, requirement_files, base_path=self.installed_requirements)
        return requirements_zip_path

    def _add_files(self, zip_path, files, mode='w', base_path=""):
        """
        Utility function to add new files in existing/new zip
        """
        zip_file = zipfile.ZipFile(zip_path, mode)
        for file in files:
            zip_file.write(file, os.path.relpath(file, base_path))
        zip_file.close()

    def _inject_requirements(self):
        """
        Inject requirements into the package archive.
        """
        requirement_files = glob.glob(os.path.join(
            self.installed_requirements, '**'), recursive=True)
        self._add_files(self.zip_path, requirement_files, 'a', self.installed_requirements)
