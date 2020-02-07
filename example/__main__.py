import pulumi
from pulumi import log
from lambda_packaging import LambdaPackaging

lambda_package = LambdaPackaging('example-test', dockerize=True, exclude=['__main__.py'])

pulumi.log.info(lambda_package.package_archive)

