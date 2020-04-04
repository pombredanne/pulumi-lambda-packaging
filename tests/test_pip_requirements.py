from unittest import TestCase
from unittest.mock import patch, Mock, mock_open
from lambda_packaging.pip_requirements import PipRequirements
from pathlib import PosixPath
import sys


# test inputs and outputes of sample requirements
actual_requirements = """
# Pulumi
pulumi==1.8.1
requirements-parser==0.2.0

# Code quality
black
pylint==2.4.4
"""

parsed_requirements = {
    "pulumi": "pulumi==1.8.1",
    "requirements-parser": "requirements-parser==0.2.0",
    "black": "black",
    "pylint": "pylint==2.4.4",
}

no_deploy = ["pylint", "black"]

filtered_requirements = {
    "pulumi": "pulumi==1.8.1",
    "requirements-parser": "requirements-parser==0.2.0",
}

filtered_content = """
pulumi==1.8.1
requirements-parser==0.2.0
"""


class TestPipRequirements(TestCase):
    @patch("lambda_packaging.pip_requirements.os")
    def setUp(self, mock_os):
        # setup PipRequirements Object and mock os
        mock_os.path.isdir.return_value = False
        self.pip = PipRequirements(
            resource_name="test-pip-requirements",
            project_root="./",
            requirements_path="requirements.txt",
            no_deploy=no_deploy,
        )

        self.mock_os = mock_os

    def test_init(self):
        # verify value of instanace variables
        self.assertEqual(self.pip.resource_name, "test-pip-requirements")
        self.assertEqual(self.pip.pip_cmd, [sys.executable, "-m", "pip", "install", "-r"])
        self.assertEqual(self.pip.install_folder.__str__(), "dist/requirements")
        self.assertEqual(
            self.pip.target_requirements_path.__str__(), "dist/requirements.txt"
        )
        self.assertEqual(self.pip.requirements_path.__str__(), "requirements.txt")

        self.mock_os.path.isdir.assert_called_with(PosixPath("dist/requirements"))
        self.mock_os.makedirs.assert_called_with(
            PosixPath("dist/requirements"), exist_ok=True
        )

    def test_generate_requirements_file(self):
        self.pip.filter_requirements = Mock()
        self.pip.filter_requirements.return_value = filtered_requirements

        # verify the creation of parsed requirements.txt
        with patch(
            "lambda_packaging.pip_requirements.open", mock_open()
        ) as mocked_file:

            self.pip.generate_requirements_file()

        mocked_file.assert_called_once_with(PosixPath("dist/requirements.txt"), "w")

    def test_filter_requirements(self):
        with patch(
            "lambda_packaging.pip_requirements.open",
            new=mock_open(read_data=actual_requirements),
        ) as mocked_file:
            requirements = self.pip.filter_requirements()
            mocked_file.assert_called_once_with(PosixPath("requirements.txt"), "r")

        # assert the outpur requirements parsing
        self.assertEqual(requirements, filtered_requirements)

    def test_install_requirements(self):
        expected_cmd = [
            sys.executable, 
            "-m",
            "pip",
            "install",
            "-r",
            "dist/requirements.txt",
            "--target=dist/requirements",
        ]

        with patch.object(self.pip, "generate_requirements_file") as generate_file:
            with patch(
                "lambda_packaging.pip_requirements.subprocess.run"
            ) as mock_subprocess:
            # verify the pip installation process
                self.pip.install_requirements()
                generate_file.assert_called()
                mock_subprocess.assert_called_with(expected_cmd, stdout=-1, stderr=-1)

                with patch.object(self.pip, "dockerize_pip") as dockerize:
                    self.pip.install_requirements()
                    dockerize.assert_not_called()

            with patch.object(self.pip, "dockerize", True):
                # verify dockerize() when docker=True
                with patch.object(self.pip, "dockerize_pip") as dockerize:
                    self.pip.install_requirements()
                    dockerize.assert_called()

    @patch("lambda_packaging.pip_requirements.RemoteImage")
    @patch("lambda_packaging.pip_requirements.Container")
    @patch("lambda_packaging.pip_requirements.format_resource_name")
    def test_dockerize_pip(self, mock_resource_name, mock_container, mock_remote_image):
        self.pip.dockerize_pip()
        mock_remote_image.assert_called_with(
            mock_resource_name("python-runtime"),
            name="lambci/lambda",
            keep_locally=True,
        )

        mock_container.assert_called_once()

    def test_docker_cmd(self):
        # assert docker command output
        expected_cmd = '''"cd /io; pip install -r requirements.txt -t dist/requirements"'''
        self.assertEqual(self.pip.docker_cmd(), expected_cmd)

