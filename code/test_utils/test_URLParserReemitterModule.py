#!/usr/bin/env python3

import unittest

from URLHandler.modules.BuiltinReemitterModules import \
        URLParserReemitterModule

class Test_Reemitter(unittest.TestCase):
    def test_url_finder(self):
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
                    ["https%3A/%2Fall.kinds%2Fasdf.lwej?qwer",
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
                ]

        mod = URLParserReemitterModule(0, None, None, None, None)

        for in_dat, out_dat in url_test:
            self.assertEqual(mod.find_urls_in_str(in_dat), out_dat)
            self.assertEqual(mod.find_urls_in_bytes(in_dat.encode()),
                    [od.encode() for od in out_dat])

if __name__ == "__main__":
    unittest.main()
