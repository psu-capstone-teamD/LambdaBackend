import json
from SchedulerController import *

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
    payload = event['body']
    response = controller.inputxml(payload)

    try:
        return respond(None, response.content)
    except Exception as e:
        return respond(ValueError('Error: "{}"'.format(response)))
