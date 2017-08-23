import json
from SchedulerController import *
import logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

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

    # url = event['url']
    url = "someurl"
    try:
        logger.info("Attempting to run inputxml")
        response = controller.inputxml(payload, url)
    except Exception as e:
        logger.error(e)

    try:
        if response['statusCode'] == '400':
            logger.error(response)
            return respond(None, response)
        else:
            logger.info(response)
            return respond(None, response)
    except Exception as e:
        logger.error(e)
        return respond(ValueError('Error: "{}"'.format(e)))