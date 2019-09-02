from .BaseModules import InputEndpointModule, ReemitterModule, \
        OutputEndpointModule
from .BuiltinInputEndpointModules import ReemitInputEndpointModule, \
        FluentdJSONFileInputEndpointModule, EmitLinesInputEndpointModule, \
        FluentdZMQInputEndpointModule
from .BuiltinOutputEndpointModules import LogOutputEndpointModule, \
        LocalStoreDownloadedObject, S3StoreDownloadedObject, \
        SQLLiteRememberDownloadedObjects, LogstashOutputEndpointModule
from .BuiltinReemitterModules import LineDoubler, URLParserReemitterModule
from .DownloadReemitterModule import DownloadURLReemitterModule
from .VirusTotalReemitterModule import VirusTotalReemitterModule

all_iems = dict()
all_rems = dict()
all_oems = dict()

def __registerModule(module, baseclass, container):
    if not issubclass(module, baseclass):
        raise TypeError("Registered module not a subclass of {}".format(
            baseclass.__name__)
            )
    if module is baseclass:
        raise TypeError("Attempted to register base class {}".format(
            baseclass.__name__)
            )

    if module.__name__ in container:
        raise RuntimeError("Already registered class {}".format(
            module.__name__)
            )

    if module is ReemitInputEndpointModule:
        raise RuntimeError("Attempted to register reemitter.")

    container[module.__name__] = module

def registerIEM(module):
    return __registerModule(module, InputEndpointModule, all_iems)

def registerREM(module):
    return __registerModule(module, ReemitterModule, all_rems)

def registerOEM(module):
    return __registerModule(module, OutputEndpointModule, all_oems)

[registerIEM(cls) for cls in [FluentdJSONFileInputEndpointModule, EmitLinesInputEndpointModule, FluentdZMQInputEndpointModule]]

[registerREM(cls) for cls in [LineDoubler, URLParserReemitterModule, DownloadURLReemitterModule, VirusTotalReemitterModule]]

[registerOEM(cls) for cls in [LogOutputEndpointModule, LocalStoreDownloadedObject, S3StoreDownloadedObject, SQLLiteRememberDownloadedObjects, LogstashOutputEndpointModule]]
