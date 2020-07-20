import json
import boto3
import os
from botocore.vendored import requests

def lambda_handler(event, context):
    # TODO implement

    def enqueue_message(event_body):
        queue_url = os.getenv('QUEUE_URL')
        print(queue_url)
        sqs = boto3.client('sqs')
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_body),
            DelaySeconds=60
        )
        print(response)

    def complete_lifecycle(event_body):
        res = autoscaling.complete_lifecycle_action(
            LifecycleHookName=event_body["LifecycleHookName"],
            AutoScalingGroupName=event_body["AutoScalingGroupName"],
            LifecycleActionToken=event_body["LifecycleActionToken"],
            LifecycleActionResult='CONTINUE'
        )
        print(res)

    event_body = json.loads(event['Records'][0]["body"])
    if event_body["LifecycleTransition"] != "autoscaling:EC2_INSTANCE_TERMINATING":
        print("Not a terminating condition return")
        return
    ec2_instance_id = event_body["EC2InstanceId"]
    ec2 = boto3.resource("ec2")
    autoscaling = boto3.client('autoscaling')
    ec2_instance = ec2.Instance(ec2_instance_id)
    ip = ec2_instance.private_ip_address
    print(ec2_instance_id)
    request_url = "http://{ip}:8080/v1/task".format(ip=ip, node_id=ec2_instance_id)
    try:
        print(request_url)
        worker_tasks = requests.get(request_url)
        worker_tasks = worker_tasks.json()
        print(len(worker_tasks))
        for task in worker_tasks:
            if task['taskStatus']['state'] == 'RUNNING':
                print('RUNNING QUEURIES FOUND')
                enqueue_message(event_body)
                return

        print('NO_QUERIES')
        complete_lifecycle(event_body)
        return
    except Exception as e:
        print(str(e))
        print("Terminating instance because worker not responding")
        complete_lifecycle(event_body)
        return
