import pulumi
from lambda_packaging import LambdaPackage
from pulumi_aws import lambda_, iam
import json


lambda_package = LambdaPackage(
    name="example-test",
    layer=True,
    no_deploy=["pulumi", "pulumi_aws", "pulumi_docker"],
    exclude=["__main__.py"],
)

role = iam.Role(
    resource_name="role",
    description=f"Role used by Lambda to run the `{pulumi.get_project()}-{pulumi.get_stack()}` project",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": ["lambda.amazonaws.com"]},
                }
            ],
        }
    ),
)

# Attach the basic Lambda execution policy to our Role
iam.RolePolicyAttachment(
    resource_name="policy-attachment",
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    role=role.name,
)

lambda_layer = lambda_.LayerVersion(
    resource_name="layer",
    layer_name="example-layer",
    compatible_runtimes=["python3.6"],
    code=lambda_package.layer_archive_path,
    source_code_hash=lambda_package.layer_hash,
)

# Create Lambda function
function = lambda_.Function(
    resource_name="function",
    role=role.arn,
    runtime="python3.6",
    description=f"Lambda function running the f`{pulumi.get_project()}` ({pulumi.get_stack()}) project",
    handler="handler.lambda_handler",
    code=lambda_package.package_archive,
    source_code_hash=lambda_package.package_hash,
    layers=[lambda_layer],
)

# path of package archive and lambda layer
# containing installed requirements
pulumi.export("package_archive_path", lambda_package.package_archive)

pulumi.export("lambda_function", function.name)
