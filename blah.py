import boto3
import json
from SchedulerController import SchedulerController

print('Loading function')
controller = SchedulerController()


def lambda_handler(event, context):
    operations = {
        'GET': lambda controller, x: controller.loadBXFFile(**x),
        'POST': lambda controller, x: controller.inputxml(**x),
        'PUT': lambda controller, x: controller.inputxml(**x),
    }

    operation = event['httpMethod']
    if operation in operations:
        payload = event['queryStringParameters'] if operation == 'GET' else event['body']
        operations[operation](controller, payload)
        return 'Action Succeeded'
    else:
        return 'Action Failed'

