import gzip
import http.client as httplib
import json
import os

import boto3
from pynamodb.exceptions import DoesNotExist, UpdateError

from functions.file_model import FileModel
from log_cfg import logger


def detect_file_text(bucket, key):
    textract = boto3.client("textract")
    response = textract.detect_document_text(Document={'S3Object': {'Bucket': bucket, 'Name': key}})
    blocks = response['Blocks']
    return blocks


def event(event, context):
    """Triggered by s3 events, object create and remove."""
    logger.debug("event: {}".format(event))

    event_name = event["Records"][0]["eventName"]
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    file_id = key.replace("{}/".format(os.environ["S3_KEY_BASE"]), "")

    try:
        if event_name == "ObjectCreated:Put":

            try:
                file = FileModel.get(hash_key=file_id)
                file.mark_received()
                file_text = detect_file_text(bucket, key)
                logger.debug("textract: {}".format(file_text))
                file.textract = gzip.compress(json.dumps(file_text).encode("utf-8"))
                file.mark_uploaded()
            except UpdateError:
                return {
                    "statusCode": httplib.BAD_REQUEST,
                    "body": {
                        "error_message": "Unable to update File"},
                }

    except DoesNotExist:
        return {
            "statusCode": httplib.NOT_FOUND,
            "body": {
                "error_message": "File {} not found".format(file_id),
            },
        }

    return {"statusCode": httplib.ACCEPTED}
