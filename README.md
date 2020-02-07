# Overview

Pulumi-based python solution for Packaging an AWS Lambda and its Layer.

## Installation
```
$ pip install lambda-packaging
```
## Quick Start

### LambdaPackaging
Creates a zip package of project files and install dependencies from requirements.txt.

Use "dockerize=True" to pip install requirements using lambda environment docker image.
User "layer=True" to package dependecies and create a lambda layer. 

Example: 

``` python
from pulumi import log
from lambda_packaging import LambdaPackaging, LambdaLayerPackaging

lambda_package = LambdaPackaging(
    'example-test', layer=True, exclude=['__main__.py'])

log.info(lambda_package.package_archive)
log.info(lambda_package.lambda_layer.arn)

```

### LambdaLayerPackaging
Creates a lambda layer. By default it zips all the project files.

Use "include" and "exclude" parameter to only add specific folders/files.

```python
from pulumi import log
from lambda_packaging import LambdaLayerPackaging


lambda_layer = LambdaLayerPackaging('example-layer-test',
                                    runtimes=['python3.6'],
                                    layer_name="example-layer",
                                    description="Example Layer for Testing",
                                    exclude=[".gitignore", '__main__.py'])

pulumi.log.info(lambda_layer.arn)

```

```bash
$ pulumi up
```