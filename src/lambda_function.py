import json
import uuid
from decimal import Decimal
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("expenses")


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    if method == "DELETE":
        return delete_expense(event)
  
    if method == "POST":
        return create_expense(event)

    if method == "GET":
        return list_expenses()

    return response(200, {"message": "Hello from the expense API!"})


def create_expense(event):
    try:
        data = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Body must be valid JSON"})

    missing = [field for field in ("amount", "category", "date") if field not in data]
    if missing:
        return response(400, {"error": "Missing fields: " + ", ".join(missing)})

    try:
        amount = Decimal(str(data["amount"]))
    except Exception:
        return response(400, {"error": "amount must be a number"})
    if amount <= 0:
        return response(400, {"error": "amount must be more than 0"})

    expense = {
        "userid": "test-user",
        "expenseid": str(uuid.uuid4()),
        "amount": amount,
        "category": data["category"],
        "date": data["date"],
        "description": data.get("description", ""),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=expense)

    return response(201, expense)


def list_expenses():
    result = table.query(KeyConditionExpression=Key("userid").eq("test-user"))

    expenses = result["Items"]

    return response(200, expenses)

def delete_expense(event):
    data = json.loads(event.get("body") or "{}")

    if "expenseid" not in data:
        return response(400, {"error": "Missing field: expenseid"})

    table.delete_item(Key={"userid": "test-user", "expenseid": data["expenseid"]})

    return response(200, {"message": "Expense deleted"})

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=float),
    }
