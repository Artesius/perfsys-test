import os
from datetime import datetime
from enum import IntEnum

import boto3
from pynamodb.attributes import NumberAttribute, UnicodeAttribute, UTCDateTimeAttribute, BinaryAttribute
from pynamodb.models import Model

from log_cfg import logger


BUCKET = os.environ["S3_BUCKET"]
KEY_BASE = os.environ["S3_KEY_BASE"]


class State(IntEnum):
    """
    Manage file states in dynamo with an int field.
    """

    CREATED = 1
    RECEIVED = 2
    PROCESSED = 3


class FileModel(Model):
    class Meta:
        table_name = os.environ["DYNAMODB_TABLE"]
        if "ENV" in os.environ:
            host = "http://localhost:8000"
        else:
            region = os.environ["REGION"]
            host = os.environ["DYNAMODB_HOST"]

    file_id = UnicodeAttribute(hash_key=True)
    state = NumberAttribute(null=False, default=State.CREATED.value)
    callback_url = UnicodeAttribute(null=False)
    textract = BinaryAttribute(null=False, default=b"", legacy_encoding=False)
    createdAt = UTCDateTimeAttribute(null=False, default=datetime.now().astimezone())
    updatedAt = UTCDateTimeAttribute(null=False, default=datetime.now().astimezone())

    def __str__(self):
        return "file_id:{}, state:{}".format(self.file_id, self.state)

    def get_key(self):
        return u"{}/{}".format(KEY_BASE, self.file_id)

    def save(self, conditional_operator=None, **expected_values):
        try:
            self.updatedAt = datetime.now().astimezone()
            logger.debug("saving: {}".format(self))
            super().save()
        except Exception as e:
            logger.error("save {} failed: {}".format(self.file_id, e), exc_info=True)
            raise e

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))

    def get_upload_url(self, ttl=60):
        """
        :param ttl: url duration in seconds
        :return: a temporary presigned PUT url
        """
        s3 = boto3.client("s3")
        put_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": self.get_key(),
            },
            ExpiresIn=ttl,
            HttpMethod="PUT",
        )
        logger.debug("upload URL: {}".format(put_url))
        return put_url

    def mark_received(self):
        """Marks file as having been received via the s3 objectCreated:Put event."""
        self.state = State.RECEIVED.value
        logger.debug("mark file received: {}".format(self.file_id))
        self.save()

    def mark_processed(self):
        """Marks file as having been processed via a textract and saved to DynamoDB."""
        processed_states = [State.RECEIVED.value, State.PROCESSED.value]
        if self.state not in processed_states:
            raise AssertionError('State: "{}" must be one of {}'.format(self.state, processed_states))
        self.state = State.PROCESSED.value
        logger.debug("mark file processed: {}".format(self.file_id))
        self.save()
