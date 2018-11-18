#!/usr/bin/env python3

import argparse
import json

import boto3

def download_file(obj_name, bucket, region, aws_profile):
    sess = boto3.Session(profile_name=aws_profile, region_name=region)
    s3 = sess.resource("s3")
    bucket = s3.Bucket(s3_bucket)

    print("Attempting to download {}".format(obj_name))
    bucket.download_file(obj_name, obj_name)
    print("Downloaded successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downloads a file from s3")
    parser.add_argument("config_file", type=argparse.FileType("r"),
            default="-", help="A JSON configuration file specifying "
            "which modules to load and their parameters - used to read the "
            "relevant S3 parameters"
            )
    parser.add_argument("file_to_download", type=str,
            help="The name of the file to download - often a hash string")

    args = parser.parse_args()

    try:
        config_data = json.load(args.config_file)
    except json.decoder.JSONDecodeError as e:
        print("Error in JSON config file")
        exit(1)

    try:
        oem = config_data["OutputEndpointModules"]
    except KeyError as e:
        print("JSON config doesn't specify output endpoint modules...  Error!")
        exit(1)

    for mod_name, mod_props in oem:
        if mod_name == "S3StoreDownloadedObject":
            break
    if mod_name != "S3StoreDownloadedObject":
        print("JSON config didn't specify S3StoreDownloadedObject...  Error!")
        exit(1)

    s3_bucket = mod_props["s3_bucket"] if "s3_bucket" in mod_props else None
    region_name = mod_props["region_name"] \
            if "region_name" in mod_props else None
    profile_name = mod_props["profile_name"] \
            if "profile_name" in mod_props else None

    download_file(args.file_to_download, s3_bucket, region_name, profile_name)
