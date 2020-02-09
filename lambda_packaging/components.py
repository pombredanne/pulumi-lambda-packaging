import pulumi
from pulumi import log
import sys
import os
from pulumi_aws import lambda_, iam
from .utils import format_resource_name, filebase64sha256
import glob
from .zip_package import ZipPackage
from .pip_requirements import PipRequirements


class LambdaPackage(pulumi.ComponentResource):
    """
    Creates a package of project files 
    and install/dependencies from requirements.txt.

    Use "dockerize=True" to pip install requirements 
    using lambda environment docker image.

    User "layer=True" to package dependecies and create a lambda layer.
    """

    def __init__(self,
                 name,
                 requirements_path='requirements.txt',
                 runtime='python3.6',
                 layer=False,
                 dockerize=False,
                 include=["**"],
                 no_deploy=[],
                 exclude=[],
                 install_folder='requirements/',
                 container_path='/io',
                 target_folder='.plp',
                 docker_image='lambci/lambda',
                 opts=None):
        """
        :name: name of the resource
        :requirements_path: relative path of requirements.txt file from __main__.py
        :runtime: python runtime
        :layer: use lambda layer
        :dockerize: dockerize python requirements
        :no_deploy: list of requirements to prevent from packaging
        :include: list of glob pattern for files to include (default: "**")
        :exclude: list of glob pattern for dirs, files to exclude while packaging
        :install_folder: name of the folder to install requirements before packaging(temporary)
        :container: mount path for container
        :target_folder: temporary folder for pip installation
        :docker_image: docker image name to use for pip installation
        """
        super().__init__('nuage:aws:LambdaPackage', name, None, opts)
        self.name = name
        self.requirements_path = requirements_path
        self.runtime = runtime
        self.layer = layer
        self.dockerize = dockerize
        self.no_deploy = no_deploy
        self.include = include
        self.exclude = exclude

        # root of __main__.py file
        self.project_root = os.path.dirname(
            os.path.abspath(sys.modules['__main__'].__file__))

        # install requirements
        pip = PipRequirements(
            resource_name=name,
            project_root=self.project_root,
            requirements_path=requirements_path,
            dockerize=self.dockerize,
            target_folder=target_folder,
            install_folder=install_folder,
            no_deploy=self.no_deploy,
            docker_image=docker_image,
            container_path=container_path
        )
        pip.install_requirements()

        # zip files and dirs
        packaged_asset = ZipPackage(
            resource_name=name,
            project_root=self.project_root,
            include=self.include,
            exclude=self.exclude,
            install_folder=install_folder,
            target_folder=target_folder
        )

        self.layer_archive_path = None
        if layer:
            self.package_archive = packaged_asset.zip_package(
                requirements=False)
            self.layer_archive_path = packaged_asset.zip_requirements()

            # output archive path and lambda layer resource
            self.register_outputs({
                'package_archive': self.package_archive,
                'layer_archive': self.layer_archive_path
            })
        else:
            self.package_archive = packaged_asset.zip_package()

            # output archive path and lambda layer resource
            self.register_outputs({
                'package_archive': self.package_archive
            })


class LambdaLayerPackage(pulumi.ComponentResource):
    """
    Creates lambda layer from the files.

    By default it zips all the project files.
    Use "include" and "exclude" parameter to only add specific folder/files.
    """

    def __init__(self,
                 name,
                 runtimes,
                 description,
                 layer_name,
                 include=["**"],
                 no_deploy=[],
                 exclude=[],
                 target_folder='.plp/',
                 opts=None):
        """
        :name: name of the resource
        :runtimes: runtimes for lambda layer
        :layer_name: name for the layer
        :description: Description for lambda layer
        :include: list of glob pattern for files to include (default: all)
        :exclude: list of glob pattern for dirs, files to exclude while packaging
        :target_folder: temporary folder for pip installation
        """
        super().__init__('nuage:aws:LambdaLayerPackage', name, None, opts)

        self.name = name
        self.layer_name = layer_name
        self.runtimes = runtimes
        self.description = description
        self.include = include
        self.exclude = exclude
        self.project_root = os.path.dirname(
            os.path.abspath(sys.modules['__main__'].__file__))

        # package project into a zipfile
        packaged_asset = ZipPackage(
            resource_name=name,
            project_root=self.project_root,
            include=self.include,
            exclude=self.exclude,
            target_folder=target_folder)
        self.archive_path = packaged_asset.zip_package(requirements=False)

        # create lambda layer
        self.lambda_layer = lambda_.LayerVersion(
            name,
            compatible_runtimes=self.runtimes,
            description=self.description,
            code=self.archive_path,
            layer_name=self.layer_name,
            source_code_hash=filebase64sha256(self.archive_path))
    
        # output layer archive path and lambda layer resource
        self.register_outputs({
            'layer_archive': self.archive_path,
            'lambda_layer': self.lambda_layer
        })
