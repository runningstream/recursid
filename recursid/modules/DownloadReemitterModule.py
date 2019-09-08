from collections import deque
import itertools as it
import re
import urllib
import time
from typing import Iterable, List, Union

import requests

from ..BuiltinObjects import URLObject, DownloadedObject, LogEntry
from .BaseModules import ReemitterModule

DEFAULT_GET_TIMEOUT = 5 # seconds
DEFAULT_REDOWNLOAD_HOLDOFF = 60 * 60 * 6 # seconds
NUM_RECENT_DOWNLOADS_TO_TRACK = 1000

class DownloadURLReemitterModule(ReemitterModule):
    supported_objects = [URLObject]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recent_downloads = deque()

    # List size method
    def is_in_recent_downloads_size(self, input_obj: URLObject) -> bool:
        return input_obj.url in self.recent_downloads

    def add_to_recent_downloads_size(self, input_obj: URLObject) -> None:
        self.recent_downloads.append(input_obj.url)
        while len(self.recent_downloads) > NUM_RECENT_DOWNLOADS_TO_TRACK:
            self.recent_downloads.popleft()
    
    # Time method
    def is_in_recent_downloads_time(self, input_obj: URLObject) -> bool:
        return any(filter(
                lambda tup: tup[1] == input_obj.url, self.recent_downloads
                ))
    def add_to_recent_downloads_time(self, input_obj: URLObject) -> None:
        self.recent_downloads.append( (time.time(), input_obj.url) )
        timeout = time.time() - DEFAULT_REDOWNLOAD_HOLDOFF
        while self.recent_downloads[0][0] < timeout:
            self.recent_downloads.popleft()

    # Set the methods to use...
    is_in_recent_downloads = is_in_recent_downloads_time
    add_to_recent_downloads = add_to_recent_downloads_time

    def handle_object(self, input_obj: URLObject, max_download: int,
            user_agents: Iterable[str],
            domain_blacklist: Iterable[str],
            get_timeout: int = DEFAULT_GET_TIMEOUT
            ) -> List[Union[DownloadedObject, LogEntry]]:

        # Make sure we didn't download this recently...
        if self.is_in_recent_downloads(input_obj):
            return []

        # Parse the domain for the next checks
        try:
            domain = urllib.parse.urlparse(input_obj.url).netloc
        except ValueError as e:
            self.logger.error("Urlparse ValueError for {}".format(input_obj.url))
            return []

        # Make sure domain isn't in blacklist...
        if any(domain.endswith(bl_dom) for bl_dom in domain_blacklist):
            self.logger.info("Skipping download of {} - "
                    "domain is blacklisted".format(input_obj.url))
            return []

        # Complete all downloads
        all_downloads = (self.complete_download(input_obj.url, user_agent,
                                             max_download, get_timeout)
                for user_agent in user_agents)
        downloads = [download for download in all_downloads
                if download is not None]

        # Consolidate downloads
        def consol(hashdig):
            applicable_dls = (dl for dl in downloads if dl.hashdig == hashdig)
            consold_user_agent = ", ".join(dl.user_agent
                    for dl in applicable_dls)

            applicable_dls = (dl for dl in downloads if dl.hashdig == hashdig)
            output_dl = next(applicable_dls)
            output_dl.user_agent = consold_user_agent
            return output_dl

        unique_hashes = {download.hashdig for download in downloads}
        unique_downloads = [consol(hashdig) for hashdig in unique_hashes]

        # Create some log entries about this result
        log_entries = [LogEntry("Downloaded url {} hash {} "
            "user-agents {}".format(dl.url, dl.hashdig, dl.user_agent))
            for dl in unique_downloads]

        # We're about to return download info, so add this to the list of
        # successful recent downloads
        self.add_to_recent_downloads(input_obj)

        return unique_downloads + log_entries

    def complete_download(self, url: str , user_agent: str,
            max_download: int, get_timeout: int):
        headers = {"user-agent": user_agent}
        try:
            req = requests.get(url, headers=headers, timeout=get_timeout,
                    stream=True)
            
            if 400 <= req.status_code < 600:
                self.logger.debug("URL {} had status {}".format(url, 
                    req.status_code)
                    )
                return None

            download = next(req.iter_content(chunk_size=max_download))
            req.close()
        except requests.exceptions.ConnectionError as e:
            self.logger.error("Connection error while handling {}".format(
                url))
            return None
        except requests.exceptions.Timeout as e:
            self.logger.error("Timeout while handling {}".format(url))
            return None
        except BaseException as e:
            self.logger.error("Exception during download:")
            self.logger.exception(e)
            return None

        return DownloadedObject(url, user_agent, download)
