import os
import json
import boto3
from botocore.vendored import requests

def lambda_handler(event, context):
    # TODO implement
    print(event)
    event_body = json.loads(event['Records'][0]["body"])
    if event_body["LifecycleTransition"] != "autoscaling:EC2_INSTANCE_TERMINATING":
        print("Not a terminating condition return")
        return
    ec2_instance_id = event_body["EC2InstanceId"]
    instance_id = ec2_instance_id
    ec2 = boto3.resource('ec2')
    ec2_instance = ec2.Instance(instance_id)
    ip = ec2_instance.private_ip_address
    for i in range(3):
        try:
            url = 'http://{}:8080/v1/info/state'.format(ip)
            payload = "\"SHUTTING_DOWN\""
            headers = {
                'Content-Type': "application/json",
                'cache-control': "no-cache"
            }
        
            response = requests.request("PUT", url, data=payload, headers=headers)
            print(response.text)
        except Exception as e:
            pass
    print(ip)
    queue_url = os.getenv('QUEUE_URL')
    print(queue_url)
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(event_body)
    )
    print(response)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
