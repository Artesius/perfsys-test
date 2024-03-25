import gzip
import http.client as httplib
import json

import requests

from functions.file_model import State
from log_cfg import logger


def event(event, _context):
    """
    Called by DynamoDB stream to make a callback on an url.
    """
    logger.debug("event: {}".format(event))

    event_name = event["Records"][0]["eventName"]
    dynamodb = event["Records"][0]["dynamodb"]
    state = dynamodb["NewImage"]["state"]["N"]
    callback_url = dynamodb["NewImage"]["callback_url"]["S"]
    textract = dynamodb["NewImage"]["textract"]["S"]

    if event_name == "MODIFY" and state == State.PROCESSED:
        requests.post(url=callback_url, data={"textract": json.loads(gzip.decompress(textract).decode("utf-8"))})

    return {
        "statusCode": httplib.ACCEPTED,
    }
