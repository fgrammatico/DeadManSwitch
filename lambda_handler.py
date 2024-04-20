import os
import json
from datetime import datetime , timedelta
import boto3
import traceback

NDAYS = int(os.environ['NDAYS'])
REGION = os.environ['REGION']
AWSUSER = os.environ['AWSUSER']
DMSBUCKET = os.environ['DMSBUCKET']
fromaddress = os.environ['fromaddress']
dmsaddress = os.environ['dmsaddress']

DELTA = datetime.now() - timedelta(days = NDAYS)
DATENOW = datetime.now()
# Notification settings
status = 'success'
defaultbody = 'Dead Man Switch Job ran ' ' @ ' + str(DATENOW)
defaultsubject = 'Dead Man Switch Notification'

# You can change the temp folder to test it locally or on AWS
TEMP = '/tmp/'

def lambda_handler(event, context):
    '''
    This function will query cloudtrail for all console login in the expected region and delta from time of now
    and "NDAYS" days.
    '''
    try:
        print ('Starting lambda handler')
        client = boto3.client('cloudtrail',REGION)
        response = client.lookup_events(
        LookupAttributes=[
            {
                'AttributeKey': 'EventName',
                'AttributeValue': 'ConsoleLogin'
            },
        ],
        StartTime=DELTA,
        EndTime=datetime.now(),
        MaxResults=1
        )
        returnuser = response['Events'][0]['Username']
        logindate = response['Events'][0]['EventTime']
        print ('"User found ' + returnuser + ' and logindate ' + str(logindate) + '"')
        if str(returnuser) == str(AWSUSER):
            msg = defaultbody + ' with ' + status + ' status'
            toaddress = dmsaddress
            mailer_func(fromaddress,toaddress,msg,status)
        else:
            deadman_switch()
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def error_func(errdescr):
    '''
    This function will handle the errors by setting a status and compiling a message
    '''
    try:
        status = 'failed'
        msg = defaultbody + ' with ' + status + ' status and error ' + errdescr
        mailer_func(fromaddress,toaddress,msg,status)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def deadman_switch():
    '''
    This function will trigger the dead man switch by grabbing each text files on the specified BUCKET
    and read its content.
    '''
    try:
        print ('"Dead man switch logger started"')
        s3_resource = boto3.resource('s3')
        dmsbucket = s3_resource.Bucket(DMSBUCKET)
        for s3_object in dmsbucket.objects.all():
            msg = ''
            filename = s3_object.key
            dmsbucket.download_file(s3_object.key,TEMP + filename)
            file = open(TEMP + filename,'r')
            line = file.read()
            file.close()
            status = '\n*******'
            msg = line + status
            toaddress = filename
            os.remove(TEMP + filename)
            mailer_func(fromaddress,toaddress,msg,status)
            print(fromaddress,toaddress,msg,status)
        exit_func()
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def mailer_func(fromaddress,toaddress,msg,status):
    '''
    This function will produce an email
    '''
    try:
        print ('"Starting the mailer"')
        client = boto3.client('ses','eu-central-1')
        response = client.send_email(
            Source= fromaddress,
            Destination={
                'ToAddresses': [
                    toaddress,
                ]
            },
            Message={
                'Subject': {
                    'Data': defaultsubject,
                },
                'Body': {
                    'Text': {
                        'Data': msg,
                    }
                }
            }
        )
        print(response)
        print ('Mailer completed')
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def exit_func():
    '''
    This function is just to exit the lambda script
    '''
    return {'statusCode': 200,'body': json.dumps(status)}


# test lambda locally removing the comment below
#lambda_handler('RequestId: 371258a2-1392-478e-9125-c918b4d33182','RequestId: 371258a2-1392-478e-9125-c918b4d33182')
