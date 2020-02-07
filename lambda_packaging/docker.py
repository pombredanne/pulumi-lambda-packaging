import pulumi
import pulumi_docker
from os import path
from pulumi_docker import RemoteImage, Container, Volume
from .config import Config


class DockerizePip(Config):
    """
    Install python requirements using docker image
    """
    def __init__(self, project_root, runtime):
        super().__init__()

        # fetch docker image
        self.image = RemoteImage("lambda-python-image",
                                 name=self.docker_image(runtime),
                                 keep_locally=True)
        
        # docker cmd to run in the container
        container_run_cmd = f'"cd {self.container_path}; pip install -r requirements.txt -t {path.join(self.install_folder)}"'
        
        # run container and install requirements
        self.container = Container("lambda-python",
                                   image=self.image.name,
                                   command=["bash", "-c", container_run_cmd],
                                   volumes={
                                       'containerPath': self.container_path,
                                       'hostPath': path.join(project_root, self.target_folder)
                                   })
