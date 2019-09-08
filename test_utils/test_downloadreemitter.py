#!/usr/bin/env python3

import unittest

from recursid.BuiltinObjects import URLObject, DownloadedObject, LogEntry
from recursid.modules.DownloadReemitterModule import \
        DownloadURLReemitterModule

MAX_DL_SIZE = 1024 * 3
USER_AGENTS = ["Nothing"]

class Test_Download(unittest.TestCase):
    def test_download(self):
        url_lst = [
            ("https://upload.wikimedia.org/wikipedia/commons/7/72/Power_off_icon.png",
                "4fb6327de39ca0f9053fc0f64da3523fcdef6b08c34e6304260ff5554424ae28",
                "PNG image data, 104 x 104, 8-bit/color RGBA, non-interlaced",
                ),
            ]

        mod = DownloadURLReemitterModule(0, None, None, None, None)

        for url, hsh, typ in url_lst:
            url_obj = URLObject(url)
            ret_val = mod.handle_object(url_obj, MAX_DL_SIZE, USER_AGENTS, [])
            
            for ret_obj in ret_val:
                if isinstance(ret_obj, DownloadedObject):
                    self.assertEqual(ret_obj.hashdig, hsh)
                    self.assertEqual(ret_obj.filetype, typ)

    def test_no_redownload(self):
        url_lst = [
            ("https://upload.wikimedia.org/wikipedia/commons/7/72/Power_off_icon.png",
                "4fb6327de39ca0f9053fc0f64da3523fcdef6b08c34e6304260ff5554424ae28",
                "PNG image data, 104 x 104, 8-bit/color RGBA, non-interlaced",
                ),
            ]

        mod = DownloadURLReemitterModule(0, None, None, None, None)

        # Do initial downloads
        for url, hsh, typ in url_lst:
            url_obj = URLObject(url)
            ret_val = mod.handle_object(url_obj, MAX_DL_SIZE, USER_AGENTS, [])
            
            for ret_obj in ret_val:
                if isinstance(ret_obj, DownloadedObject):
                    self.assertEqual(ret_obj.hashdig, hsh)
                    self.assertEqual(ret_obj.filetype, typ)

        # Now do re-download
        for url, hsh, typ in url_lst:
            url_obj = URLObject(url)
            ret_val = mod.handle_object(url_obj, MAX_DL_SIZE, USER_AGENTS, [])
            
            print(ret_val)
            self.assertEqual(len(ret_val), 0)

if __name__ == "__main__":
    unittest.main()
