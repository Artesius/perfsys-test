# Serverless REST API
This test task demonstrates how to setup a REST API web service using Presigned URLs
to manage asset uploads and downloads. 

The initial POST creates a file entry in dynamo and returns a presigned upload URL. 
This is used to upload the file without needing any credentials. 
An s3 event triggers another lambda method to mark the asset as "RECEIVED" and send it to textract.
Textract operation results are saved in the DynamoDB and are marked as "PROCESSED" once the process finishes.
After that a textract results are sent on a callback url mentioned in the post request.

To retrieve a textract for a file do a GET to the file id.
This URL can be used to retrieve the information with no additional credentials.

DynamoDB is used to store the index and tracking data referring to the files on s3.

## Structure
This service has a separate directory for all the assets operations. 
For each operation exactly one file exists e.g. `functions/create.py`. In each of these files there is exactly one lambda defined.
### Logging
The log_cfg.py is an alternate way to setup the python logging to be more friendly wth AWS lambda.
The lambda default logging config is to not print any source file or line number which makes it harder to correleate with the source.

Adding the import:
```python
    from log_cfg import logger
```
at the start of every event handler ensures that the format of the log messages are consistent, customizable and all in one place. 

Default format uses:
```python
'%(asctime)-15s %(process)d-%(thread)d %(name)s [%(filename)s:%(lineno)d] :%(levelname)8s: %(message)s'
```

## Deploy

In order to deploy the serverless simply run

```bash
serverless deploy
```

The expected result should be similar to:

```
endpoints:
  POST - https://z0ujsglkge.execute-api.us-east-1.amazonaws.com/dev/files
  GET - https://z0ujsglkge.execute-api.us-east-1.amazonaws.com/dev/files/{file_id}
functions:
  create: perfsys-test-task-test-create
  bucket_trigger: perfsys-test-task-test-bucket
  get: perfsys-test-task-test-get
  dynamo_stream: perfsys-test-task-test-dynamo
```