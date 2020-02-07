import pulumi
import os

conf = {
    'install_folder': 'requirements/',
    'zip_name': 'lambda.zip',
    'container_path': '/io',
    'target_folder': '.plp',
    'docker_image': 'lambci/lambda'
}


class Config(object):
    """
    Contains configuration data
    """
    def __init__(self, custom_config={}):
        conf.update(custom_config)
        self._config = conf

    def get_property(self, property_name):
        return self._config.get(property_name)

    @property
    def zipfile_name(self):
        template = '{project}-{stack}.zip'
        resource_name = template.format(
            project=pulumi.get_project(),
            stack=pulumi.get_stack(),
        )
        return resource_name

    @property
    def host_path(self):
        self.get_property('host_path')

    @property
    def container_path(self):
        return self.get_property('container_path')

    @property
    def target_folder(self):
        return self.get_property('target_folder')

    @property
    def install_folder(self):
        return os.path.join(self.get_property('target_folder'), self.get_property('install_folder'))

    def docker_image(self, runtime):
        return f'{self.get_property("docker_image")}:{runtime}'
