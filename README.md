## Table of contents
* [General info](#general-info)
* [Requirements](#requirements)
* [Setup](#setup)
* [Notes](#notes)
* [To Do](#ToDo)
* [Contributing](#contributing)

## General info
Dead Mand Switch project (V 1.0) is an interactive cross-platform python script that will create an AWS lambda function that will monitor periodically cloudtrails for your console logins. Each run will send you a task notification (success/failed) and in case of missing login for the specified time range the dead man switch will activate and send the messages to the chosen recipients.
	
## Requirements

* Python 3
* boto3
* regex
* pip3
* A valid AWS account
* A personal email
* Most email providers won't allow "from and to" with the same recipients so a functional email recipient for regular task reports is strongly advised
* AWS validated email recipients
	
## Setup
To run this project please clone the repository and cd into it:

```
$ pip3 install -r requirements.txt
$ python3 DeadManSwitch.py
```
## Notes
The purpose of this script is to secure the transfer of important information to our loved ones in case of departure. The content of the emails should be short and simple with only the necessary informations. All the emails are stored on AWS S3 with ecrytion at rest. Security realated to encryption in flight or under computation is striclty reserved to the user. I take no responsibility for the effectiveness of this script or the security of your messages.Keep in mind you must validate the recipients 24 hours before AWS SES will send the confirmation. For more experienced cloud engineers there's a serverless version on my github under Automation/Cloudformation/Serverless. Enjoy.

## To Do
* Add the possibility to use your own SMTP
* Add KMS option
* Add fancy GUI
* Add DynamoDb logs
* Add possibility to modify content of mails
* Add possibility to add and remove mails

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
