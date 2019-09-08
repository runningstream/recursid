import itertools as it
import re
from typing import Iterable, Union
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

    def handle_object(self,
            input_obj: Union[FluentdRecord, DownloadedObject],
            limit_url_count: int = None) -> URLObject:
        """
        Parse the input_obj for any potential URLs
        Limit the return count to limit_url_count, if specified

        Return URLObjects
        """
        #TODO don't limit URL returns in such a limited way
        if issubclass(input_obj.__class__, FluentdRecord):
            retval = self.handle_fluentd_record(input_obj)
        elif issubclass(input_obj.__class__, DownloadedObject):
            retval = self.handle_downloaded_obj(input_obj)
        else:
            raise RuntimeError("Type not implemented")

        if limit_url_count is not None:
            return retval[:limit_url_count]

        return retval

    def find_urls_in_str(self, data: str):
        """
        Look for straightforward urls using an re in the block of text data
        """
        def str_unquoter(url):
            if "://" in url:
                return url
            return urllib.parse.unquote(url) 
        urls = self.url_str_re.findall(data)
        return [str_unquoter(url) for url in urls]

    def find_urls_in_bytes(self, data: bytes):
        """
        Look for straightforward urls using an re in the block of text data
        """
        def byte_unquoter(url):
            if b"://" in url:
                return url
            return urllib.parse.unquote_to_bytes(url) 
        urls = self.url_bytes_re.findall(data)
        return [byte_unquoter(url) for url in urls]

    def handle_downloaded_obj(self, input_obj: DownloadedObject) \
            -> Iterable[URLObject]:
        url_set = set(self.find_urls_in_bytes(input_obj.content))
        return [URLObject(url) for url in url_set]
    
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
        return [URLObject(url) for url in urls]
