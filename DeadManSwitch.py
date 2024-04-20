#!/usr/bin/env python3
import botocore
import os
from pathlib import Path
import time
import re
import traceback
import secrets
import string
import boto3

alphabet = string.ascii_letters + string.digits
bucketrnd = ''.join(secrets.choice(alphabet) for i in range(20))
lambdabucketrnd = ''.join(secrets.choice(alphabet) for i in range(20))
DMSBUCKET = str('dmsmails' + bucketrnd.lower())
LAMBDABUCKET = str('dmslambda' + lambdabucketrnd.lower())

HOME = str(Path.home()) + os.sep
CWD = str(os.getcwd()) + os.sep
fileCheck = Path(HOME +'.aws/credentials')

def aws_cred():
    try:
        if fileCheck.exists ():
            file = open(HOME +'.aws/credentials')
            allLines = file.readlines()
            accessKeyTemp = (allLines[1])
            accessKey = accessKeyTemp[18:38]
            secretTemp = (allLines[2])
            secret = secretTemp[22:62]
            file.close()
            answer1 = input ('\nWelcome to the Dead Man Switch generator for AWS.\n\nINFO: Found AWS default credentials.' + '\n\nPlease enter Y/n to confirm the use of these credentials: ').upper()
            if answer1 == 'Y':
                user_question()
            elif answer1 == 'N':
                custom_credentials()
            else:
                print('\nSorry, the answer is invalid, please use just Y or n.\n')
                aws_cred()
        else:
            print('\n***ERROR***\nI can\'t find any AWS credentials, please download AWS cli and configure the tool with an existing user.')
    except IOError:
        exiterror = input ('\nFile not accessible.\n*************The program will exit,press a key*************')

def custom_credentials():
        answer2 = input ('\nWould you like to enter the acces key and secret manually now? ').upper()
        if answer2 == 'N':
            program_end()
        elif answer2 == 'Y':
            accessKeyTemp = input ('\nPlease enter your access key: ')
            secretTemp = input ('\nPlease enter your secret: ')
            accessKey = str(accessKeyTemp)
            secret = str(secretTemp)
            user_question()
        else:
            print('\nSorry, the answer is invalid, please use just Y or n.\n')
            aws_cred()

def user_question():
    try:
        AWSUSER = input ('\nPlease enter the AWS user you want to monitor as it appears in your console manager: ')
        confirm = input ('\nIs this correct "' + str(AWSUSER) + '" ?(Y/n): ')
        confirmUp = confirm.upper()
        if confirmUp == "Y":
            print('\nThank you for confirming, program resuming...')
            email_from(AWSUSER)
        elif confirmUp == "N":
            user_question()
        else:
            print('\nInvalid answer, please enter Y or n only.')
            user_question()
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def email_from(AWSUSER):
    questionAddress = input ('\nPlease enter your "from" address that you will use to send your notifications: ')
    fromaddress = questionAddress.lower()
    fromaddressTemp = re.search(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$',fromaddress)
    confirmAdd = input ('\nIs this correct "' + str(fromaddress) + '" ?(Y/n)').upper()
    if confirmAdd == "Y":
        if fromaddressTemp:
            email_dms(fromaddress,AWSUSER)
        else:
            print('\nYour email does not evaluate to a correct pattern, please retry.')
            email_from(AWSUSER)
    elif confirmAdd == "N":
        email_from(AWSUSER)
    else:
        print('\nYour answer is incorrect, please retry.')
        email_from(AWSUSER)

def email_dms(fromaddress,AWSUSER):
    questionAddress2 = input ('\nPlease enter a recipient address different than ' + fromaddress + ' for service notifications: ')
    dmsaddress = questionAddress2.lower()
    dmsaddressTemp = re.search(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$',dmsaddress)
    confirmAdd = input ('\nIs this correct "' + str(dmsaddress) + '" ?(Y/n)').upper()
    if confirmAdd == "Y":
        if dmsaddressTemp and str(dmsaddress) != str(fromaddress):
            region_question(dmsaddress,fromaddress,AWSUSER)
        else:
            print('\nThe recipient does not evaluate to a correct pattern or is identical to your "from address", please retry.')
            email_dms(fromaddress,AWSUSER)
    elif confirmAdd == "N":
        email_dms(fromaddress,AWSUSER)
    else:
        print('\nYour answer is incorrect, please retry.')
        email_dms(fromaddress,AWSUSER)
    
def region_question(dmsaddress,fromaddress,AWSUSER):
    try:
        REGION = input ('\nWhich AWS Availability Zone do you want to use to deploy your Dead Man Switch (leave empty for eu-central-1)? ')
        if REGION == '':
            REGION = 'eu-central-1'
        checkRegionPattern= re.search(r'\w{2}-\w{4,7}-\d{1}',REGION)
        if checkRegionPattern:
            print('\n*****************A verification request to your address is now sent and must be accepted before 24 hours!*****************')
            client = boto3.client('ses',REGION)
            response = client.verify_email_address(
            EmailAddress = fromaddress
            )
            days_func(dmsaddress,fromaddress,AWSUSER,REGION)
        else:
            print('\nYour region does not evaluate to a correct patter, please retry')
            region_question(dmsaddress,fromaddress,AWSUSER)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def days_func(dmsaddress,fromaddress,AWSUSER,REGION):
    try:
        NDAYS = int(input ('\nPlease define how many days back you want to check for your logins (min 10 max 89): '))
        if isinstance(NDAYS, int) == True and NDAYS <= 89 and NDAYS >= 10:
            create_role(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS)
        else:
            print('\nInvalid number!')
            days_func(dmsaddress,fromaddress,AWSUSER,REGION)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def create_role(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS):
    try:
        print('\nINFO: Creating AWS Role "dmslambda"')
        client = boto3.client('iam')
        response = client.create_role(
            RoleName='dmslambda',
            AssumeRolePolicyDocument='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":["lambda.amazonaws.com"]},"Action":["sts:AssumeRole"]}]}',
            Description='Dead Man Switch Role',
            MaxSessionDuration=3600,
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'DMS'
                },
            ]
        )

        print('\nINFO: Attaching policies')

        time.sleep(3) 
        response = client.put_role_policy(
            PolicyDocument='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":"*"},{"Effect":"Allow","Action":"cloudwatch:*","Resource":"*"},{"Effect":"Allow","Action":"cloudtrail:*","Resource":"*"},{"Effect":"Allow","Action":"lambda:*","Resource":"*"},{"Effect":"Allow","Action":"events:*","Resource":"*"},{"Effect":"Allow","Action":"sns:*","Resource":"*"},{"Effect":"Allow","Action":"SES:*","Resource":"*"}]}',
            PolicyName='dmspolicy',
            RoleName='dmslambda',
        )
        print('\nINFO: Role successfully created')
        create_bucket(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def create_bucket(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS):
    try:
        client = boto3.client('s3')
        print('\nINFO: Creating S3 mail bucket')

        response = client.create_bucket(
        ACL='private',
        Bucket=DMSBUCKET,
        CreateBucketConfiguration={
            'LocationConstraint': REGION,
            },
        )

        response = client.put_bucket_encryption(
            Bucket=DMSBUCKET,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    },
                ]
            }
        )

        print('\nINFO: S3 mail bucket created')

        print('\nINFO: Creating S3 lambda mail bucket')

        response = client.create_bucket(
        ACL='private',
        Bucket=LAMBDABUCKET,
        CreateBucketConfiguration={
            'LocationConstraint': REGION
        },
        )
        response = client.put_bucket_encryption(
            Bucket=LAMBDABUCKET,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    },
                ]
            }
        )
        response = client.put_bucket_acl(
        ACL='private',
        Bucket=DMSBUCKET
        )
        print('\nINFO: S3 lambda bucket created')
        upload_lambda(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def upload_lambda(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET):
        print('\nINFO: Uploading the lamda function to S3.')
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(CWD + 'lambda_handler.zip', LAMBDABUCKET, 'lambda_handler.zip')
        print('\nINFO: Package uploaded and encrypted on server side.')
        mail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET)

def mail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET):
    try:
        questionAddress2 = input ('\nPlease enter the recipient where you will send your message: ')
        toaddress = questionAddress2.lower()
        toaddressTemp = re.search(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$',toaddress)
        confirmAdd = input ('\nIs this correct "' + str(toaddress) + '" ?(Y/n)').upper()
        if confirmAdd == "Y":
            if toaddressTemp:
                mail_body(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress)
            else:
                print('\nYour email does not evaluate to a correct pattern, please retry.')
                mail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET)
        elif confirmAdd == "N":
            mail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET)
        else:
            print('\nYour answer is incorrect, please retry.')
            mail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def mail_body(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress):
    try:
        subjectText = 'Dead Man Switch Notification'
        mailBody = input ('\nPlease enter the message content for this recipient in a single string, pushing enter will end the message: ')
        msg = '\nSubject: ' + subjectText + '\n\n' + mailBody
        print (msg)
        confirmMailTemp = input ('\nIs this correct (Y/n)? ')
        confirmMail = confirmMailTemp.upper()
        if confirmMail == "Y":
            upload_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress,subjectText,mailBody)
        elif confirmMail == "N":
            mail_body(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress)
        else:
            print('\nYour answer is incorrect, please retry.')
            mail_body(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def upload_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress,subjectText,mailBody):
    try:
        fileMail = open (CWD + toaddress,"w+")
        fileMail.write(mailBody)
        fileMail.close()
        print('\nINFO: Uploading your message to S3.')
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(CWD + toaddress, DMSBUCKET, toaddress)
        os.remove(CWD + toaddress)
        print('\nINFO: Message uploaded and encrypted on server side')
        moreEmail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress,subjectText,mailBody)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def moreEmail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress,subjectText,mailBody):
    try:
        print('\n*****************A verification request to this recipient address is now sent and must be accepted before 24 hours!*****************')
        client = boto3.client('ses',REGION)
        response = client.verify_email_address(
        EmailAddress = toaddress
        )
        anotherMessageTemp = input ('\nDo you want to create another message?: ')
        anotherMessage = anotherMessageTemp.upper()
        if anotherMessage == "Y":
            mail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET)
        elif anotherMessage == "N":
            build_handler(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress)
        else:
           print('\nInvalid answer, please enter Y or n only.')
           moreEmail_func(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress,subjectText,mailBody)
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)

def build_handler(dmsaddress,fromaddress,AWSUSER,REGION,NDAYS,DMSBUCKET,LAMBDABUCKET,toaddress):
    try:
        client = boto3.client('lambda',REGION)
        response = client.create_function(
        FunctionName='DeadManSwitch',
        Runtime='python3.8',
        Role='arn:aws:iam::040805337628:role/dmslambda',
        Handler='lambda_handler.lambda_handler',
        Code={
            'S3Bucket': LAMBDABUCKET,
            'S3Key': 'lambda_handler.zip'
        },
        Description='Send your last wishes to your loved ones',
        Timeout=6,
        MemorySize=128,
        Publish=True,
        Environment={
            'Variables': {
                'NDAYS': str(NDAYS),
                'AWSUSER': AWSUSER,
                'fromaddress': fromaddress,
                'dmsaddress' : dmsaddress,
                'REGION': REGION,
                'LAMBDABUCKET': LAMBDABUCKET,
                'DMSBUCKET': DMSBUCKET
            }
        }
        )
        fn_arn = response['FunctionArn']
        frequency = 'rate('+ str(NDAYS) + ' days)'

        events_client = boto3.client('events',REGION)
        rule_response = events_client.put_rule(
            Name="DeadManSwitch-Trigger",
            ScheduleExpression=frequency,
            State='ENABLED',
        )

        client.add_permission(
            FunctionName='DeadManSwitch',
            StatementId="DeadManSwitch-Event",
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_response['RuleArn'],
        )

        events_client.put_targets(
            Rule="DeadManSwitch-Trigger",
            Targets=[
                {
                    'Id': "1",
                    'Arn': fn_arn,
                },
            ]
        )
        program_end()
    except Exception as error:
        errdescr = type(error).__name__ + '\n' + traceback.format_exc()
        print(errdescr)
        program_end()

def program_end():
    final = input ('\nEnd of program\n\nPress any key\n')
    result = 'Stop'

aws_cred()
