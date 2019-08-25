import hashlib
import json
from typing import Iterable, Any, Union

import magic

from .BaseObject import BaseObject
from .utilities import convert_bytes_to_str

class LogEntry(BaseObject):
    def __init__(self, log_data: str):
        self.log_data = convert_bytes_to_str(log_data)
    def str_content(self):
        return self.log_data

class DeathLog(BaseObject):
    def __init__(self, obj: BaseObject):
        self.log_data = "Object died!"
        self.ttl = 0
        self.ancestors = str(obj)
    def str_content(self):
        return self.log_data

class JSONObject(BaseObject):
    def __init__(self, json_dat: str, json_indent: int = 2):
        self.dat = json.loads(json_dat)
        self.json_indent = json_indent

    def str_content(self):
        return json.dumps(self.dat, indent=self.json_indent)

class FluentdRecord(JSONObject):
    pass

class URLObject(BaseObject):
    def __init__(self, url: Union[bytes, str]):
        self.url = convert_bytes_to_str(url)
    def str_content(self):
        return self.url

class BinaryBlobObject(BaseObject):
    def __init__(self, content: bytes):
        self.content = content

    def str_content(self):
        return convert_bytes_to_str(self.content[:1024])

class DownloadedObject(BinaryBlobObject):
    def __init__(self, url: str, user_agent: str, content: bytes):
        super().__init__(content = content)
        self.url = convert_bytes_to_str(url)
        self.user_agent = user_agent
        self.hashdig = hashlib.sha256(content).hexdigest()
        self.filetype = magic.from_buffer(content)

    def str_content(self):
        return "URL: {}\nUser-Agent: {}\nFiletype: {}"\
                "\nSHA256 Hash: {}\nHead Content: {}".format(
                        self.url, self.user_agent, self.filetype,
                        self.hashdig, super().str_content()
                        )
