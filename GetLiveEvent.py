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
    logger.info("Attempting to run getLiveEvent")
    response = controller.getLiveEventForFrontEnd()
    try:
        if(response['statusCode'] == '400'):
            logger.error(response)
            return response
        else:
            logger.info(response)
            return response
    except Exception as e:
        logger.error(e)
        return respond(ValueError('Error: "{}"'.format(response)))
