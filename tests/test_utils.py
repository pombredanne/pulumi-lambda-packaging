from unittest import TestCase
from unittest.mock import patch
from lambda_packaging.utils import (
    format_file_name,
    format_resource_name,
    sha256sum,
    filebase64sha256,
)


class TestUtils(TestCase):
    def test_format_resource_name(self):
        with patch("lambda_packaging.utils.pulumi") as mock_pulumi:
            mock_pulumi.get_project.return_value = "project_name"
            mock_pulumi.get_stack.return_value = "test"
            self.assertEqual(
                format_resource_name("resource_name"), "project_name-test-resource_name"
            )

    def test_format_file_name(self):
        with patch("lambda_packaging.utils.pulumi") as mock_pulumi:
            mock_pulumi.get_stack.return_value = "test"
            self.assertEqual(
                format_file_name("resource_name", "file_name"),
                "test-resource_name-file_name",
            )

    def test_filebase64sha256(self):
        expected_hash = "7tmXmHm+TRjBYobZQ5ovx9h0S7iH14vSmH5/ut64Slc="
        self.assertEqual(filebase64sha256('tests/data/sample_file.py'), expected_hash)