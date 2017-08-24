[![Build Status](https://travis-ci.org/psu-capstone-teamD/LambdaBackend.svg?branch=master)](https://travis-ci.org/psu-capstone-teamD/LambdaBackend) [![Coverage Status](https://coveralls.io/repos/github/psu-capstone-teamD/LambdaBackend/badge.svg?branch=master)](https://coveralls.io/github/psu-capstone-teamD/LambdaBackend?branch=master)
# LambdaBackend
LambdaBackend is a serverless application for creating live stream playlists that can be scheduled and updated according to the users preference.

# Getting Started
In order to start developing you will need the following Python 2.7, PIP package manageer for dependencys, an Amazon Web Services Account, AWS S3, AWS Api Gateway, and AWS lambda. 

# Installing
Install dependencys via PIP the python package manage

`pip install -r requirements.txt`

# Deploying to Lambda

Create a AWS Lambda function in the AWS console, and upload the repository as a zip file to the lambda function you created. 

# Setting up Api Gateway

Create an Api in AWS api Gateaway and for each api endpoint link the lambda function you created in AWS Lambda and deploy the api. 

# Running Tests
This repository uses pythons unittest library. and you can run all the tests by running

`python -m unittest discover Tests`
