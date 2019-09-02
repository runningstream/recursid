#!/usr/bin/env python3

import logging
import os.path
import time
import unittest

from recursid.modules.VirusTotalReemitterModule import \
        VirusTotalReemitterModule

virus_total_api_keyfile = os.path.expanduser("~/.virus_total_api")

class Test_Reemitter(unittest.TestCase):
    def setUp(self):
        with open(virus_total_api_keyfile,"r") as api_keyfile:
            self.virustotal_apikey = api_keyfile.read().strip()
    
    def test_rate_lim(self):
        inst = VirusTotalReemitterModule(0, None, None, None, None)
        inst2 = VirusTotalReemitterModule(0, None, None, None, None)

        # Test the rate limiting across all objects
        st_time = time.time()
        inst.rate_limit()
        inst2.rate_limit()
        inst.rate_limit()
        ed_time = time.time()
        self.assertGreaterEqual(ed_time-st_time, inst.VT_API_RATE * 2)

    def test_get_report(self):
        class Test_Obj:
            def __init__(self, dig):
                self.hashdig = dig

        test_hashes_match = [
                "be4c77a7538dfe1e300998b9e582fdd111bc31128a0380850305ecc5ca756565",
                #"5d51051fbe3df180dfdfbe2fed5ce6fddafb4b7afa88c09f1adc5670e0d5a6ff",
                #"beb7531a0740c2818b10dc23ff2482cc260b74535908949e5ca0ecc316b13c1f",
                #"cb3af105f9d29294bd71ad99e15ba67473d39a61a5184eb2d355b135ceb84c85",
            ]
        test_hashes_no_match = [
                "00207989d662bc5095d810b90d5413310966e528564e8efa496b6f2c1245e844",
                #"00317378ac84c122a1cf348fee67ca9a43a68abc1cb14e809a525e4ae7f2cdc8",
                #"008054057a4edd7d07a12448f658f167f47833dbbb2a426fc272ba9d1bbe394b",
                #"008dd63c949fd4b8ac2156cd68709e685e5a5414feda1debcb1c712fa6863dbd",
            ]

        test_match_objs = (Test_Obj(hval) for hval in test_hashes_match)
        test_no_match_objs = (Test_Obj(hval) for hval in test_hashes_no_match)
        
        inst = VirusTotalReemitterModule(0, None, None, None, None)

        for test_obj in test_match_objs:
            self.assertTrue(
                inst.report_present(test_obj, self.virustotal_apikey)
                )

        for test_obj in test_no_match_objs:
            self.assertFalse(
                inst.report_present(test_obj, self.virustotal_apikey)
                )

    def test_submitter(self):
        class Test_Obj(object):
            def __init__(self, filename):
                self.url="http://example.com"
                with open(filename, "rb") as file_in:
                    self.content = file_in.read()

        test_files = ["./test_file_html"]
        test_objs = (Test_Obj(fname) for fname in test_files)

        inst = VirusTotalReemitterModule(0, None, None, None, None)

        for test_obj in test_objs:
            response = inst.submit_bin(test_obj, self.virustotal_apikey)
            self.assertEqual(response["response_code"], 1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
