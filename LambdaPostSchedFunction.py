import json
from SchedulerController import SchedulerController

print('Loading function')
controller = SchedulerController()

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To make a POST, pass in the payload to the controller as a JSON body.
    '''
    #print("Received event: " + json.dumps(event, indent=2))

    operations = {
        'POST': lambda controller, x: controller.inputxml(**x),
    }

    operation =event['httpMethod']
    if operation in operations:
        payload = json.loads(event['body'])
        return respond(None, operations[operation](controller, payload))
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))
