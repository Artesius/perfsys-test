import http.client as httplib
import uuid

from functions.file_model import FileModel
from log_cfg import logger


def create(event, _context):
    """
    No body needed here as POST is a request for a pre-signed upload URL.
    Create an entry for it in dynamo and return upload URL
    """
    logger.debug("event: {}".format(event))

    data = event["body"]

    try:
        file = FileModel()
        file.file_id = str(uuid.uuid1())
        file.callback_url = data["callback_url"]
        file.save()
        upload_url = file.get_upload_url()

    except KeyError:
        return {
            "statusCode": httplib.UNPROCESSABLE_ENTITY,
            "body": {
                "error_message": "Callback URL is not provided",
            },
        }

    return {
        "statusCode": httplib.CREATED,
        "body": {
            "upload_url": upload_url,
            "id": file.file_id,
        },
    }
