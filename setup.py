from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()


install_requires = [
    "pulumi==1.8.1",
    "pulumi_aws==1.17.0",
    "pulumi_docker",
    "requirements-parser"
]


setup(
    name='lambda_packaging',
    version='0.1.0',
    description="Pulumi-based python solution for Packaging an AWS Lambda and its Layer.",
    url='https://github.com/nuage-studio/lambda-packaging',
    packages=find_packages(exclude=('tests', 'example')),
    zip_safe=True,
    install_requires=install_requires
)
