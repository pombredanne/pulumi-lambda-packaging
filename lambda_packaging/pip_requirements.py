import requirements as req
import subprocess
import os
from os import path
import pulumi
import json
from .utils import format_resource_name
from pulumi_docker import RemoteImage, Container


class PipRequirements:
    """
    Installs requirements.txt in .plp/requirements/ folder
    """

    def __init__(self,
                 resource_name,
                 project_root,
                 requirements_path,
                 no_deploy=[],
                 dockerize=False,
                 runtime="python3.6",
                 target_folder='.plp/',
                 install_folder='requirements/',
                 docker_image="lambci/lambda",
                 container_path="/io"):
        self.resource_name = resource_name
        self.pip_cmd = ['pip', 'install', '-r']
        self.project_root = project_root
        self.no_deploy = no_deploy
        self.runtime = runtime
        self.dockerize = dockerize
        self.target_folder = target_folder
        self.install_folder = path.join(target_folder, install_folder)
        self.docker_image = docker_image
        self.container_path = container_path

        self.target_requirements_path = path.join(
            self.project_root, self.target_folder, 'requirements.txt'
        )
        self.requirements_path = os.path.join(
            self.project_root, requirements_path
        )
        self.install_path = path.join(self.project_root, self.install_folder)

        if not os.path.isdir(self.install_path):
            os.makedirs(self.install_path, exist_ok=True)

    def generate_requirements_file(self):
        """
        Parses requirements and add requirements.txt in .plp folder    
        """
        requirements = self.filter_requirements()
        with open(self.target_requirements_path, 'w') as f:
            for k in requirements:
                f.write(f'{requirements[k]}\n')

    def filter_requirements(self):
        """
        Filter requirements from mentioned no_deploy paramter
        """
        with open(self.requirements_path, 'r') as f:
            requirements = {r.name: r.line for r in req.parse(f)}
        pulumi.log.info(self.requirements_path)
        pulumi.log.info(json.dumps(requirements))
        for n in self.no_deploy:
            try:
                requirements.pop(n)
            except:
                pass
        return requirements

    def dockerize_pip(self):

        self.image = RemoteImage(format_resource_name('python-runtime'),
                                 name=self.docker_image,
                                 keep_locally=True)

        # docker cmd to run in the container
        container_run_cmd = f'"cd {self.container_path}; pip install -r requirements.txt -t {path.join(self.install_folder)}"'

        # run container and install requirements
        self.container = Container(format_resource_name('docker-container'),
                                   image=self.image.name,
                                   command=["bash", "-c", container_run_cmd],
                                   volumes=[{
                                       'containerPath': self.container_path,
                                       'hostPath': path.join(self.project_root, self.target_folder)
                                   }])

    def install_requirements(self):
        """
        Install requirements.txt
        """
        self.generate_requirements_file()
        if self.dockerize:
            self.dockerize_pip()
        else:
            self.pip_cmd.append(self.target_requirements_path)
            self.pip_cmd.append('--upgrade')
            self.pip_cmd.append(f'--target={self.install_path}')
            subprocess.run(self.pip_cmd)
