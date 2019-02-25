from queue import Empty
import json

import msgpack
import zmq

from ..BuiltinObjects import FluentdRecord, JSONObject, LogEntry
from .BaseModules import InputEndpointModule

class ReemitInputEndpointModule(InputEndpointModule):
    refs = 0
    def __init__(self, *args, **kwargs):
        """
        Ensure that only one ReemitInputEndpointModule gets instantiated
        """
        if ReemitInputEndpointModule.refs == 1:
            raise RuntimeError("ReemitInputEndpointModule instantiated "
                    "more than once")
        else:
            ReemitInputEndpointModule.refs = 1
        super().__init__(*args, **kwargs)

    def main(self):
        while self.framework_still_running():
            try:
                obj = self.recv_obj_queue.get(True, 1)
            except Empty as e:
                continue
            self.logger.debug("Emitting obj: {}".format(obj))
            self.add_to_send_queue(obj)

# Do not register the ReemitInputEndpointModule

class FluentdJSONFileInputEndpointModule(InputEndpointModule):
    """
    Parse each line in a file as json, emitting FluentdRecords for each
    """
    def main(self, filename):
        with open(filename, "r") as f:
            file_dat = f.read()

        for line in file_dat.split("\n"):
            if line != "":
                self.logger.debug("Emitting line: {}".format(line))
                self.emit(FluentdRecord(line))

class EmitLinesInputEndpointModule(InputEndpointModule):
    """
    Emit each line in a block of text as a log entry
    """
    def main(self, text_block):
        for line in text_block.split("\n"):
            self.emit(LogEntry(line))

class FluentdZMQInputEndpointModule(InputEndpointModule):
    def byte_input_to_string(self, obj_dict):
        def try_decode(item):
            if hasattr(item, "decode"):
                return item.decode("utf-8", errors="backslashreplace")
            else:
                return str(item)
            return item

        return {try_decode(key): try_decode(dat)
                for key, dat in obj_dict.items()}

    def json_friendlify_input(self, obj_dict):
        strified_dict = self.byte_input_to_string(obj_dict)

        result = None
        try:
            # Sometimes stringifying still doesn't permit json parsing
            # This produces error output for those cases
            result = json.dumps(strified_dict)
        except BaseException as e:
            self.logger.error("JSONing failed for strified obj:\n{}"
                    "".format(strified_dict))
            self.logger.exception(e)
        return result

    def main(self, fluent_zmq_key: str,
            host: str ="127.0.0.1", port: int = 5556,
            protocol: str ="tcp"):
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        subscriber.connect("{}://{}:{}".format(protocol, host, port))
        subscriber.setsockopt_string(zmq.SUBSCRIBE, fluent_zmq_key)

        while self.framework_still_running():
            data_raw = subscriber.recv()
            key, data_recvd = data_raw.split(b" ", maxsplit=1)
            data = msgpack.unpackb(data_recvd)
            for entry in data:
                tag, time, entry_obj = entry
                friendly_ent = self.json_friendlify_input(entry_obj)
                if friendly_ent is not None:
                    self.logger.debug("Emitting string: {}"
                            "".format(friendly_ent))
                    self.emit(FluentdRecord(friendly_ent))
