import gzip
import http.client as httplib
import json

from pynamodb.exceptions import DoesNotExist

from functions.file_model import FileModel
from log_cfg import logger


def get(event, _context):
    """Get a textract for file <file-id>."""
    logger.debug("event: {}".format(event))

    file_id = event["path"]["file_id"]
    try:
        file = FileModel.get(hash_key=file_id)
        textract = json.loads(gzip.decompress(file.textract).decode("utf-8"))

    except DoesNotExist:
        return {
            "statusCode": httplib.NOT_FOUND,
            "body": {
                "error_message": "File {} not found".format(file_id),
            },
        }

    except AssertionError as e:
        return {
            "statusCode": httplib.FORBIDDEN,
            "body": {
                "error_message": "Unable to download: {}".format(e),
            },
        }

    return {
        "statusCode": httplib.OK,
        "body": {
            "textract": textract,
        },
    }
