import requirements as req
import subprocess
import os
from os import path
import pulumi
from .docker import DockerizePip
from .config import Config

class PipRequirements(Config):
    """
    Installs requirements.txt in .plp/requirements/ folder
    """
    def __init__(self, project_root, requirements_path, no_deploy=[], dockerize=False, runtime="python3.6"):
        super().__init__()
        self.pip_cmd = ['python', '-m', 'pip', 'install', '-r']
        self.project_root = project_root
        self.no_deploy = no_deploy
        self.runtime = runtime
        self.target_requirements_path = path.join(self.project_root, self.target_folder, 'requirements.txt')
        self.dockerize = dockerize
        self.requirements_path = os.path.join(self.project_root, requirements_path)
        self.install_path = path.join(self.project_root, self.install_folder)
        if not os.path.isdir(self.install_path):
            os.makedirs(self.install_path, exist_ok=True)

    def generate_requirements_file(self):
        """
        Parses requirements and add requirements.txt in .plp folder    
        """
        requirements = self.filter_requirements()
        with open(self.target_requirements_path, 'w') as f:
            for requirements in requirements:
                f.write(f'{requirements}\n')

    def filter_requirements(self):
        """
        Filter requirements from mentioned no_deploy paramter
        """
        with open(self.requirements_path, 'r') as f:
            requirements = {r.name: r.line for r in req.parse(f)}
        for n in self.no_deploy:
            requirements.pop(n)
        return requirements


    def install_requirements(self):
        """
        Install requirements.txt
        """
        self.generate_requirements_file()

        self.pip_cmd.append(self.target_requirements_path)
        self.pip_cmd.append('--upgrade')
        self.pip_cmd.append(f'--target={self.install_path}')
        if self.dockerize:
            DockerizePip(self.project_root, self.runtime)
        else:
            subprocess.run(self.pip_cmd)
