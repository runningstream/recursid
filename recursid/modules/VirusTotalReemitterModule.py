import requests
import time
from typing import Optional, Union

from .BaseModules import ReemitterModule
from ..BuiltinObjects import LogEntry, DownloadedObject

class VirusTotalReemitterModule(ReemitterModule):
    """
    A reemitter module that submits executable downloads to VirusTotal

    Configuration:
    api_key - your VirusTotal API key
    """

    VT_API_RATE = 60/4 # seconds - 4 per minute max API use rate...
    supported_objects = [DownloadedObject]
    last_api_req = None

    # Virus Total API Endpoints
    report_url = "https://www.virustotal.com/vtapi/v2/file/report"
    scan_url = "https://www.virustotal.com/vtapi/v2/file/scan"


    def is_right_filetype(self, input_obj: DownloadedObject):
        """
        Return true if the input_obj content is of a useful filetype
        """
        # Filter out only certain file types...
        filetype_keywords = ["Executable"]
        found_keywords = [kw for kw in filetype_keywords
                if kw in input_obj.filetype]
        if found_keywords:
            return True
        return False

    def rate_limit(self):
        """
        Limit the rate of access to VirusTotal API to 4 per min
        across all instances of this class
        """
        if self.__class__.last_api_req is None:
            # If we have no record of last API usage, assume we just used it
            # That's the worst case scenario, but keep us out of trouble
            self.__class__.last_api_req = time.time()
        time_since_last = time.time() - self.__class__.last_api_req
        if time_since_last < self.VT_API_RATE:
            time.sleep(self.VT_API_RATE - time_since_last)
        self.__class__.last_api_req = time.time()

    def do_api_request(self, req_type, endpoint, *args, **kwargs):
        """
        Perform a virustotal API request
        :param req_type: The requests function to execute - get/post...
        """
        self.rate_limit()
        response = req_type(endpoint, *args, **kwargs)
        self.logger.debug("Reponse code: {}".format(response.status_code))
        if response.status_code != 200:
            raise RuntimeError("VT Request Failed With Code: {}".format(
                    response.status_code)
                    )
        self.logger.debug("Reponse text: {}".format(response.text))
        return response.json()


    def get_report(self, input_obj: DownloadedObject, api_key: str):
        """
        Return the report for a given DownloadedObject
        """
        params = {"apikey": api_key, "resource": input_obj.hashdig}
        return self.do_api_request(requests.get, self.report_url, params=params)

    def report_present(self, input_obj: DownloadedObject, api_key: str):
        """
        Return True if VirusTotal already has a report for the input_obj
        """
        resp = self.get_report(input_obj, api_key)
        return resp["response_code"] == 1

    def submit_bin(self, input_obj: DownloadedObject, api_key: str):
        """
        Submit a downloaded object to VirusTotal
        """
        params = {"apikey": api_key}
        files = {"file": (input_obj.url, input_obj.content)}
        return self.do_api_request(requests.post, self.scan_url,
                files=files, params=params)

    def handle_object(self, input_obj: DownloadedObject, api_key: str):
        """
        If the input_obj is of a useful file type, and there's not already
        a VirusTotal entry for its hash, upload it to VirusTotal
        """
        if not self.is_right_filetype(input_obj):
            self.logger.info("URL was wrong type: {}".format(input_obj.url))
            return None

        if self.report_present(input_obj, api_key):
            self.logger.info("Hash was already submitted: {}".format(
                input_obj.hashdig)
                )
            return None

        response = self.submit_bin(input_obj, api_key)

        return LogEntry("Submitted URL {} hash {} to VirusTotal "\
                "with response code {} response {}".format(
                    input_obj.url, input_obj.hashdig, 
                    response["response_code"], response["verbose_msg"]
                    )
                )
