import binascii
import datetime
from email.message import EmailMessage
import logging
import os
import os.path
import re
import smtplib
import sqlite3
import string
import time
from typing import Optional, Union, List

import boto3
import logstash

from .BaseModules import OutputEndpointModule
from ..BuiltinObjects import LogEntry, DeathLog, DownloadedObject

class LogOutputEndpointModule(OutputEndpointModule):
    """
    An OutputEndpointModule that simply logs objects sent to it
    """
    supported_objects = [LogEntry, DeathLog]
    def handle_object(self, input_obj: Union[LogEntry, DeathLog], level: str):
        LOGGER_METHODS = {
                "DEBUG": self.logger.debug,
                "INFO": self.logger.info,
                "WARN": self.logger.warn,
                "ERROR": self.logger.error,
                "CRITICAL": self.logger.critical
                }
        if level not in LOGGER_METHODS:
            raise RuntimeError("Invalid logging level in "
                    "LogOutputEndpointModule")
        log_func = LOGGER_METHODS[level]
        log_func("{}".format(input_obj))

class LogstashOutputEndpointModule(OutputEndpointModule):
    supported_objects = [LogEntry]
    logstash_logger = None

    def setup_logger(self, host: str, port: int,
            protocol: Optional[str] = None):
        if self.logstash_logger is None:
            self.logstash_logger = logging.getLogger("RecursidLogstash")
            self.logstash_logger.setLevel(logging.INFO)
            self.logstash_logger.propagate = False
            
            if protocol == "udp":
                handler_cls = logstash.LogstashHandler
            else:
                handler_cls = logstash.TCPLogstashHandler

            handler = handler_cls(host, port)
            self.logstash_logger.addHandler(handler)

    def handle_object(self, input_obj: LogEntry, host: str, port: int):
        self.logger.debug("Logstash logging: {}".format(input_obj))
        self.setup_logger(host, port)
        self.logstash_logger.info(str(input_obj))

class EmailOutputEndpointModule(OutputEndpointModule):
    """
    Send email to an address for LogEntry objects matching a regex
    Parameters:
      search_regex - string - the regular expression to search log entries
        for.  Matching log entries get sent via email.
      smtp_server - string - the address of the SMTP server
      smtp_port - integer - the port of the SMTP server (often 587)
      smtp_user - string - the username for logging in to the SMTP server.
        Passing no user skips login.
      smtp_pass - string - the user's password for login
      from_addr - string - the "from" address in the email
      to_addr - string - the "to" address in the email
      subject - string - a static subject line for the email, log entry data
        gets placed in the message
      use_tls - bool - True uses TLS for the connection (Default: True)
    """
    supported_objects = [LogEntry]
    def handle_object(self, input_obj: LogEntry, search_regex: str,
            smtp_server: str, smtp_port: int, smtp_pass: str, from_addr: str,
            to_addr: str, subject: str,
            smtp_user: Union[str, None] = None, use_tls: bool = True):
        if not re.search(search_regex, str(input_obj)):
            return
        
        msg = EmailMessage()
        msg.set_content(str(input_obj))
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        try:
            with smtplib.SMTP(host=smtp_server, port=smtp_port) as smtp_sock:
                if use_tls:
                    smtp_sock.starttls()
                if smtp_user:
                    smtp_sock.login(user=smtp_user, password=smtp_pass)
                smtp_sock.send_message(msg)
        except Exception as e:
            self.logger.error("Error during email send attempt!")
            self.logger.exception(e)
            

class LocalStoreDownloadedObject(OutputEndpointModule):
    supported_objects = [DownloadedObject]
    def handle_object(self, input_obj: DownloadedObject, output_dir: str):
        output_file = os.path.join(output_dir, input_obj.hashdig)
        try:
            with open(output_file, "xb") as outfile:
                outfile.write(input_obj.content)
        except FileExistsError as e:
            self.logger.info("Not outputting {} - EXISTS - {}".format(
                output_file, input_obj)
                )
        else:
            self.logger.debug("Wrote file {}".format(output_file))

class S3StoreDownloadedObject(OutputEndpointModule):
    supported_objects = [DownloadedObject]
    last_dl_time = None
    last_s3_list = None
    max_list_time = 60 * 60 * 24
    def update_bucket_file_list(self, s3_bucket: str,
            aws_profile: Optional[str], region_name: Optional[str]):
        self.logger.debug("Updating S3 bucket file list")
        sess = boto3.Session(profile_name=aws_profile, region_name=region_name)
        s3 = sess.resource("s3")
        bucket = s3.Bucket(s3_bucket)
        self.last_s3_list = [obj.key for obj in bucket.objects.all()]
        self.last_dl_time = time.time()

    def list_bucket_files(self, s3_bucket: str, aws_profile: Optional[str], 
            region_name: Optional[str]):
        if self.last_s3_list is None or \
                time.time() - self.last_dl_time > self.max_list_time:
            self.update_bucket_file_list(s3_bucket, aws_profile, region_name)
        return self.last_s3_list

    def add_bucket_file(self, name: str):
        """
        Add a file we uploaded to the file list - keep track of some changes
        locally
        """
        self.last_s3_list.append(name)

    def is_right_filetype(self, input_obj: DownloadedObject,
            filetype_contains: Optional[List[str]]):
        """
        Return true if the filetype of input_obj contains any
        substring in filetype_contains

        If filetype_contains is None or is empty, always return True
        """
        if not filetype_contains:
            return True

        return any((ftype.lower() in input_obj.filetype.lower())
                for ftype in filetype_contains
                )

    def handle_object(self, input_obj: DownloadedObject, 
            s3_bucket: str,
            filetype_contains: Optional[List[str]]=None,
            aws_profile: Optional[str]=None,
            region_name: Optional[str]=None):
        """
        Handles input_obj of type DownloadedObject, stores them in s3_bucket
        for given profile and region if the object's filetype string contains
        any substrings in filetype_contains's list.
        """
        # Verify the filetype is desired
        if not self.is_right_filetype(input_obj, filetype_contains):
            self.logger.info("File {} is wrong filetype".format(input_obj.url))
            return

        bucket_files = self.list_bucket_files(s3_bucket, aws_profile,
                region_name)
        if input_obj.hashdig not in bucket_files:
            sess = boto3.Session(profile_name=aws_profile,
                    region_name=region_name)
            s3 = sess.resource("s3")
            bucket = s3.Bucket(s3_bucket)
            bucket.put_object(Key=input_obj.hashdig, Body=input_obj.content)
            self.logger.info("Uploaded {} to S3".format(input_obj.hashdig))
            self.add_bucket_file(input_obj.hashdig)
        else:
            self.logger.info("File {} already present, not uploaded to S3"
                    "".format(input_obj.hashdig))

class SQLLiteRememberDownloadedObjects(OutputEndpointModule):
    supported_objects = [DownloadedObject]
    def handle_object(self, input_obj: DownloadedObject, db_filename: str,
            db_table: str):
        valid_table_chars = string.ascii_letters + string.digits + "_"
        is_table_clean = all(val in valid_table_chars for val in db_table)
        if not is_table_clean and not db_table[0].isdigit():
            raise RuntimeError("Table name was invalid: started with a digit "
                    "or contained characters outside a-zA-Z0-9 and _")

        db = sqlite3.connect(db_filename)
        try:
            self.ensure_db_setup(db, db_table)
            self.add_to_db_if_not_duplicate(input_obj, db, db_table)
        finally:
            db.close()

    def ensure_db_setup(self, db, db_table: str):
        try:
            rescur = db.execute("SELECT * FROM {}".format(db_table))
            results = rescur.fetchone()
        except sqlite3.OperationalError as e:
            self.logger.debug("Table not found - creating")
            db.execute("CREATE TABLE {} "
                    "(hash text, url text, insert_time text)".format(
                        db_table)
                    )

    def add_to_db_if_not_duplicate(self, input_obj: DownloadedObject,
            db, db_table: str):
        rescur = db.execute("SELECT * FROM {} WHERE url=? AND hash=?"
                "".format(db_table),
                (input_obj.url, input_obj.hashdig)
                )
        results = rescur.fetchall()
        if len(results) == 0:
            self.logger.debug("Entry not present, adding: {} {}"
                    "".format(input_obj.url, input_obj.hashdig))
            timenow = datetime.datetime.utcnow().isoformat(sep=" ")
            with db:
                db.execute("INSERT INTO {} VALUES (?, ?, ?)".format(db_table),
                        (input_obj.hashdig, input_obj.url, timenow)
                        )

        else:
            self.logger.debug("Entry already present, not adding: {} {}"
                    "".format(input_obj.url, input_obj.hashdig))
