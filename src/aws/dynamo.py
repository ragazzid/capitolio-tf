import boto3
import json
import logging
import os
from datetime import datetime

dynamodb_client = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')

logging.basicConfig()
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)


def create_table(table_name: str):
    dynamodb_client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'InstanceId',
                'AttributeType': 'S'
            },
        ],
        KeySchema=[
            {
                'AttributeName': 'InstanceId',
                'KeyType': 'HASH'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 4,
            'WriteCapacityUnits': 4
        }
    )
    table = dynamodb_resource.Table(table_name)
    table.wait_until_exists()


def setup():
    tables = dynamodb_client.list_tables()
    table_name = os.environ['DYNAMO_TABLE'] if 'DYNAMO_TABLE' in os.environ else 'RagazziD_Capitolio_Dns'
    if table_name in tables['TableNames']:
        logger.info('DynamoDB table already exists')
    else:
        create_table(table_name)
    return dynamodb_resource.Table(table_name)


def add_record(table: str, instance: str):
    instance_dump = json.dumps(instance, default=json_serial)
    instance_attributes = json.loads(instance_dump)
    try:
        table.put_item(
            Item={
                'InstanceId': instance['Instances'][0]['InstanceId'],
                'InstanceAttributes': instance_attributes
            }
        )
        logger.info("Added succesfully")
    except BaseException as e:
        logger.error("Error while trying to add record to Dynamo table {}".format(e))


def remove_record(table: str, instance_id: str):
    try:
        table.delete_item(
            Key={
                'InstanceId': instance_id
            }
        )
    except BaseException as e:
        logger.error("Failed to delete: {}".format(e))


def json_serial(obj: object):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def get_record(table: str, instance_id: str):
    try:
        response = table.get_item(
            Key={
                'InstanceId': instance_id
            }
        )
        return response
    except BaseException as e:
        logger.error('Couldn\'t find the item in dynamo table for: {}'.format(instance_id))
        return False
