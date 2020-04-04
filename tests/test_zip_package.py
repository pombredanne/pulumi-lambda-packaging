from unittest import TestCase
from unittest.mock import patch, mock_open
from lambda_packaging.zip_package import ZipPackage
from pathlib import PosixPath, Path


class TestZipPackage(TestCase):
    @patch("lambda_packaging.zip_package.format_file_name")
    @patch("lambda_packaging.zip_package.os")
    def setUp(self, mock_os, mock_format_file_name):
        # setup ZipPackage object
        mock_os.path.isdir.return_value = False
        mock_format_file_name.return_value = "test-lambda.zip"
        self.zip_package = ZipPackage(
            resource_name="test-zip-package", project_root="./"
        )
        self.mock_os = mock_os

    def test_init(self):
        # verify the value of instance variables
        self.assertEqual(self.zip_package.resource_name, "test-zip-package")

        self.assertEqual(
            self.zip_package.install_folder, PosixPath("dist/requirements/")
        )
        self.assertEqual(
            self.zip_package.installed_requirements, PosixPath("dist/requirements")
        )

        self.assertEqual(self.zip_package.zipfile_name, "test-lambda.zip")

        self.assertEqual(self.zip_package.zip_path, PosixPath("dist/test-lambda.zip"))

        self.assertEqual(self.zip_package.install_path, PosixPath("dist/requirements/"))

        self.assertEqual(self.zip_package.include, ["**"])

        self.assertEqual(self.zip_package.exclude, [PosixPath("dist/**")])

        # verify the dir dist/ is created
        self.mock_os.path.isdir.assert_called_with(PosixPath("dist/requirements"))

        self.mock_os.makedirs.assert_called_with(
            PosixPath("dist/requirements"), exist_ok=True
        )

    def test_get_path(self):
        self.assertEqual(
            self.zip_package.get_path("sample_file.py"),
            PosixPath("dist/sample_file.py"),
        )

    def test_match_glob_files(self):
        # assert output of glob pattern matching
        with patch.object(
            self.zip_package, "project_root", Path("tests/data/test_files")
        ):
            self.assertEqual(
                sorted(self.zip_package._match_glob_files(["*.py"])),
                ["tests/data/test_files/file_1.py"],
            )
            self.assertEqual(
                sorted(self.zip_package._match_glob_files(["**/*.py"])),
                sorted(
                    [
                        "tests/data/test_files/file_1.py",
                        "tests/data/test_files/test_nest/file_4.py",
                    ]
                ),
            )

            self.assertEqual(
                sorted(self.zip_package._match_glob_files(["**"])),
                sorted(
                    [
                        "tests/data/test_files/",
                        "tests/data/test_files/file_1.py",
                        "tests/data/test_files/file_2.txt",
                        "tests/data/test_files/file_3.md",
                        "tests/data/test_files/test_nest",
                        "tests/data/test_files/test_nest/file_4.py",
                    ]
                ),
            )

    def test_filter_package(self):
        # verify the filter_package output based upon exclude and include input
        with patch.object(
            self.zip_package, "project_root", Path("tests/data/test_files")
        ):
            with patch.object(self.zip_package, "exclude", ["*.txt", "*.md"]):
                self.assertAlmostEqual(
                    sorted(self.zip_package.filter_package()),
                    sorted(
                        [
                            "tests/data/test_files/file_1.py",
                            "tests/data/test_files/test_nest/file_4.py",
                            "tests/data/test_files/test_nest",
                            "tests/data/test_files/",
                        ]
                    ),
                )
            with patch.object(self.zip_package, "exclude", ["**"]):
                self.assertEqual(self.zip_package.filter_package(), [])
                with patch.object(self.zip_package, "include", ["**/*.py"]):
                    self.assertEqual(
                        sorted(self.zip_package.filter_package()),
                        sorted(
                            [
                                "tests/data/test_files/test_nest/file_4.py",
                                "tests/data/test_files/file_1.py",
                            ]
                        ),
                    )

    def test_zip_package(self):
        with patch.object(self.zip_package, "_add_files") as mocked_add_files:
            with patch.object(
                self.zip_package, "_inject_requirements"
            ) as mocked_inject_files:
                self.assertEqual(
                    self.zip_package.zip_package(requirements=False),
                    Path("dist/test-lambda.zip"),
                )
                mocked_add_files.assert_called_once()
                mocked_inject_files.assert_not_called()
                self.assertEqual(
                    self.zip_package.zip_package(), Path("dist/test-lambda.zip")
                )
                mocked_inject_files.assert_called_once()

    @patch("lambda_packaging.zip_package.format_file_name")
    def test_zip_requirements(self, mocked_format_file_name):
        mocked_format_file_name.return_value = "test-lambda.zip"
        with patch.object(
            self.zip_package, "installed_requirements", Path("tests/data/")
        ):
            with patch.object(self.zip_package, "_add_files"):
                self.assertEqual(
                    self.zip_package.zip_requirements(), Path("dist/test-lambda.zip")
                )

    @patch("lambda_packaging.zip_package.zipfile.ZipFile")
    def test_add_files(self, mocked_zip_file):
        test_file = "tests/data/test_files/file_1.py"
        zip_path = "tests/data/test.zip"
        self.zip_package._add_files(
            zip_path, [test_file], mode="w", base_path="tests/data",
        )
        # assert if files are writen into a zip archive
        mocked_zip_file().writestr.assert_called_once()

    def test_is_file_allowed(self):
        self.assertEqual(self.zip_package.is_file_allowed("hello.py"), True)
        self.assertEqual(self.zip_package.is_file_allowed("hello.pyc"), False)
        self.assertEqual(self.zip_package.is_file_allowed("hello.pyc"), False)
        self.assertEqual(self.zip_package.is_file_allowed("./__pycache__"), False)
        self.assertEqual(self.zip_package.is_file_allowed("mock/__pycache__"), False)
        self.assertEqual(self.zip_package.is_file_allowed("mock/file/hello.pyc"), False)

    def test_inject_requirements(self):
        # verify the injection of pip requiements into zip archive
        with patch.object(
            self.zip_package, "installed_requirements", Path("tests/data/")
        ):
            with patch.object(self.zip_package, "_add_files") as mocked_add_files:
                self.zip_package._inject_requirements()
                mocked_add_files.assert_called_once()
