import itertools as it
import re
from typing import Iterable
import urllib.parse

from ..BuiltinObjects import FluentdRecord, URLObject, \
        LogEntry, DownloadedObject
from .BaseModules import ReemitterModule

class LineDoubler(ReemitterModule):
    supported_objects = [LogEntry]
    def handle_object(self, input_obj):
        return [LogEntry(input_obj.log_data + input_obj.log_data)]

class URLParserReemitterModule(ReemitterModule):
    supported_objects = [FluentdRecord, DownloadedObject]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        re_str = "(https?(?::|%3A)(?:/|%2F)(?:/|%2F).*?)"\
                "(?:\+|\s|%20|;|%3b|\"|%22|\'|%27|$)"
        self.url_str_re = re.compile(re_str)
        self.url_bytes_re = re.compile(re_str.encode())

    def handle_object(self, input_obj):
        if issubclass(input_obj.__class__, FluentdRecord):
            return self.handle_fluentd_record(input_obj)
        elif issubclass(input_obj.__class__, DownloadedObject):
            return self.handle_downloaded_obj(input_obj)
        else:
            raise RuntimeError("Type not implemented")

    def find_urls_in_str(self, data: str):
        """
        Look for straightforward urls using an re in the block of text data
        """
        return self.url_str_re.findall(data)

    def find_urls_in_bytes(self, data: bytes):
        """
        Look for straightforward urls using an re in the block of text data
        """
        return self.url_bytes_re.findall(data)

    def unquote_if_necessary(self, url):
        """
        If a URL needs unquoting to be valid, unquote it.
        Otherwise return unchanged.
        """
        if "://" in url:
            return url
        return urllib.parse.unquote(url) 

    def handle_downloaded_obj(self, input_obj: DownloadedObject) \
            -> Iterable[URLObject]:
        url_set = set(self.find_urls_in_bytes(input_obj.content))
        urls_fixed = (self.unquote_if_necessary(url) for url in url_set)
        return [URLObject(url) for url in urls_fixed]
    
    def handle_fluentd_record(self, input_obj: FluentdRecord) \
            -> Iterable[URLObject]:
        SEARCH_FIELDS_BY_TYPE = {
                "cowrie": ["input"],
                "glastopf": ["http_body"],
                "echo_and_log": ["data_ascii"],
                }
        if input_obj.dat["type"] not in SEARCH_FIELDS_BY_TYPE:
            self.logger.debug("No URL search fields for record type {}"
                    "".format(input_obj.dat["type"])
                    )
            return set()

        search_fields = SEARCH_FIELDS_BY_TYPE[input_obj.dat["type"]]
        tosearch = (input_obj.dat[fld]
            for fld in input_obj.dat if fld in search_fields)
        urls = set(
            it.chain.from_iterable(self.find_urls_in_str(search)
                for search in tosearch)
            )
        urls_fixed = (self.unquote_if_necessary(url) for url in urls)
        return [URLObject(url) for url in urls_fixed]
