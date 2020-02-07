from pulumi import log
from lambda_packaging import LambdaPackaging, LambdaLayerPackaging

lambda_package = LambdaPackaging(
    'example-test', layer=True, exclude=['__main__.py'])

lambda_layer = LambdaLayerPackaging('example-layer-test',
                                    runtimes=['python3.6'],
                                    layer_name="example-layer",
                                    description="Example Layer for Testing",
                                    exclude=[".gitignore", '__main__.py'])


# path of package archive 
# and lambda layer containing installed requirements
log.info(lambda_package.package_archive)
log.info(lambda_package.lambda_layer.arn)

# lambda layer arn
log.info(lambda_layer.lambda_layer.arn)
