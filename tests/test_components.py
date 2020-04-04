from unittest import TestCase
from unittest.mock import patch, MagicMock
from lambda_packaging.components import LambdaPackage
import pulumi
import shutil
from pathlib import Path

class ResourceMock(pulumi.runtime.Mocks):
    def call(self, token, args, provider):
        return {}

    def new_resource(self, type_, name, inputs, provider, id_):
        return ["", {}]


pulumi.runtime.set_mocks(ResourceMock())


# test outputs of expected zipfiles hash
test_hash_1 = "pkTEi+w+/P3ThNx31BdzMK1GVfBXvfdwTF8+uUkDlUQ="
test_hash_2 = "fgPhqs9YpRQvT1dXXiy4w+T0AFSGkjNpdFVeLtggujQ="
test_hash_3 = "Qn6WRrkmRHVgcOqY1QREst0Q4Y9mIuoXd9op3OMQI6w="


class TestComponents(TestCase):
    @pulumi.runtime.test
    def test_lambda_package(self):
        with patch("lambda_packaging.components.os") as mock_os:
            mock_os.path.dirname.return_value = Path("tests/data")
            lambda_package = LambdaPackage(
                name="example-test",
                layer=False,
                exclude=["requirements*.txt"],
                requirements_path="requirements_test_1.txt",
            )

            # verify archive path
            self.assertEqual(
                lambda_package.package_archive,
                "tests/data/dist/stack-example-test-lambda.zip",
            )

            # verify archive hash
            self.assertEqual(
                lambda_package.package_hash, test_hash_1,
            )

    @pulumi.runtime.test
    def test_lambda_package_with_layer(self):
        with patch("lambda_packaging.components.os") as mock_os:
            mock_os.path.dirname.return_value = Path("tests/data")
            lambda_package = LambdaPackage(
                name="example-test",
                layer=True,
                exclude=["**/requirements*.txt"],
                requirements_path="requirements_test_1.txt",
            )

            # verify package archive path
            self.assertEqual(
                lambda_package.package_archive,
                "tests/data/dist/stack-example-test-lambda.zip",
            )

            #verify layer archive path
            self.assertEqual(
                lambda_package.layer_archive_path,
                "tests/data/dist/stack-example-test-requirements.zip",
            )

            # verify package hash
            self.assertEqual(lambda_package.package_hash, test_hash_2)
            
            # verify layer archive hash
            self.assertEqual(lambda_package.layer_hash, test_hash_3)

    @pulumi.runtime.test
    def test_archive_hash_consistency_when_files_not_ordered(self):
        with patch("lambda_packaging.components.os") as mock_os:
            # mock "sorted" function to diable sort behaviour
            with patch("lambda_packaging.zip_package.sorted") as mock_sorted:
                mock_sorted.side_effect = lambda x: x
                mock_os.path.dirname.return_value = Path("tests/data")
                lambda_package = LambdaPackage(
                    name="example-test",
                    layer=False,
                    exclude=["**/requirements*.txt"],
                    requirements_path="requirements_test_1.txt",
                )

                # asert archive hash not equal to detenmined hash
                self.assertNotEqual(lambda_package.package_hash, test_hash_2)

    @pulumi.runtime.test
    def test_archive_hash_consistency_when_datetime_is_changed(self):
        with patch("lambda_packaging.components.os") as mock_os:
            # change datetime value of files being archived
            with patch(
                "lambda_packaging.zip_package.CONST_DATETIME", (2020, 2, 1, 0, 0, 0)
            ):
                mock_os.path.dirname.return_value = Path("tests/data")
                lambda_package = LambdaPackage(
                    name="example-test",
                    layer=False,
                    exclude=["**/requirements*.txt"],
                    requirements_path="requirements_test_1.txt",
                )

                # verify archive hash not equal to detenmined hash
                self.assertNotEqual(lambda_package.package_hash, test_hash_2)

    def tearDown(self):
        # delete the generated files & directories after each test is run
        shutil.rmtree("tests/data/dist/", ignore_errors=True)
