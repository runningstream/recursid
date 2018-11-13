#!/usr/bin/env python3

import argparse
import itertools as it
import logging
import json

from URLHandler.MultithreadedFramework import MultithreadedFramework

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="Execute the URL Handling Framework"
            )
    parser.add_argument("config_file", type=argparse.FileType("r"),
            default="-", help="A JSON configuration file specifying "
            "which modules to load and their parameters"
            )
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--template", nargs=argparse.REMAINDER,
            default=list(),
            help="All arguments after this specify key and value to place "\
                    "in a config template, if any are needed.  "\
                    "Specify key then value as separate arguments."
                    )

    args = parser.parse_args()

    # Make sure template data might be valid
    if len(args.template) % 2 != 0:
        logging.critical("If template arguments are used, they must be in "
                "key value pairs, so the number of arguments must be "
                "divisible by 2")
        exit(1)

    # Setup any template info to be filled in...
    template_filler = {key: val
            for key, val in zip(args.template[0::2], args.template[1::2])}

    # Setup some basic logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Read in the config file
    try:
        config_data = json.load(args.config_file)
    except json.decoder.JSONDecodeError as e:
        logging.critical("JSON error in config file: {}".format(e))
        exit(1)

    # Fill in any template config info
    all_modules = it.chain(config_data["InputEndpointModules"],
            config_data["ReemitterModules"],
            config_data["OutputEndpointModules"])
    for mod_name, mod_config in all_modules:
        for key in mod_config:
            if not hasattr(mod_config[key], "format"):
                continue
            try:
                mod_config[key] = mod_config[key].format(**template_filler)
            except KeyError as e:
                logging.critical("Template entry not found on command "
                        "line: {}".format(e))
                exit(1)

    # Set a default start ttl for objects
    start_ttl = None
    if "start_ttl" in config_data:
        start_ttl = config_data["start_ttl"]

    # Instantiate and kick-off the framework
    mpf = MultithreadedFramework(
            config_data["InputEndpointModules"],
            config_data["ReemitterModules"],
            config_data["OutputEndpointModules"],
            start_ttl
            )
    mpf.main()
