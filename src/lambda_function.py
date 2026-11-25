import json, logging, os, time, uuid
import boto3
from aws_xray_sdk.core import patch_all
from boto3.dynamodb.conditions import Key

patch_all()  # traces boto3 calls (DynamoDB) in X-Ray

logger = logging.getLogger()
table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def respond(code, body):
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body, default=str)}


def lambda_handler(event, context):
    try:
        user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
        route = event["routeKey"]
        logger.info("request received", extra={"route": route})

        if route == "POST /notes":
            data = json.loads(event.get("body") or "{}")
            text = str(data.get("text", "")).strip()
            if not text:
                return respond(400, {"error": "text is required"})
            item = {"userId": user_id, "noteId": str(uuid.uuid4()),
                    "text": text[:500], "createdAt": int(time.time())}
            table.put_item(Item=item)
            logger.info("note created", extra={"noteId": item["noteId"]})
            return respond(201, item)

        if route == "GET /notes":
            result = table.query(KeyConditionExpression=Key("userId").eq(user_id))
            logger.info("notes listed", extra={"count": len(result["Items"])})
            return respond(200, result["Items"])

        if route == "DELETE /notes/{noteId}":
            note_id = event["pathParameters"]["noteId"]
            try:
                table.delete_item(
                    Key={"userId": user_id, "noteId": note_id},
                    ConditionExpression="attribute_exists(noteId)",
                )
            except table.meta.client.exceptions.ConditionalCheckFailedException:
                return respond(404, {"error": "note not found"})
            logger.info("note deleted", extra={"noteId": note_id})
            return respond(204, {})

        return respond(404, {"error": "not found"})

    except json.JSONDecodeError:
        return respond(400, {"error": "invalid JSON"})
    except Exception:
        logger.exception("unhandled error")
        return respond(500, {"error": "internal error"})
