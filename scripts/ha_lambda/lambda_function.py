import json
import boto3
import http.client
import time
import os

def detach_eni_instance(eniAttachmentId):
    client = boto3.client('ec2')
    print("detaching eni {}".format(eniAttachmentId))
    response = client.detach_network_interface(
        AttachmentId = eniAttachmentId,
        Force = True
    )
    time.sleep(5)
    print(response)
    print("ENI detached")
    
def attach_eni_instance(instanceId, eni_id):
    client = boto3.client('ec2')
    print("attaching eni {} to instance {}".format(eni_id, instanceId))
    response = client.attach_network_interface(
        DeviceIndex=1,
        InstanceId = instanceId,
        NetworkInterfaceId = eni_id,
    )
    return response

def instance_health(instanceId):
    client = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=[
            instanceId
        ]
    )
    print("checking health for instance {}".format(instanceId))
    try:
        conn = http.client.HTTPConnection(response['Reservations'][0]['Instances'][0]['PrivateIpAddress'], 8080)
        conn.request("GET", "/v1/info")
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        data = json.loads(r1.read().decode('utf-8').replace("'", '"'))
    except Exception as e:
        print("AN EXCEPTION OCCURED", str(e))
        data = {
            "starting": True
        }
    return data
    # return response
    
def attach_eni(eni_id):
    client = boto3.client('ec2')
    response = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:presto:opensource:identification:role',
                'Values': [
                    'presto:coordinator'
                ]
            },
            {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [
                    os.environ['STACK_NAME']
                ]
            }
        ]
    )
    for j in range(len(response['Reservations'])):
        for i in range(len(response['Reservations'][j]['Instances'])):
            if response['Reservations'][j]['Instances'][i]['State']['Name'] != 'running':
                continue
            privateIpAddress = response['Reservations'][j]['Instances'][i]['PrivateIpAddress']
            instanceId = response['Reservations'][j]['Instances'][i]['InstanceId']
            print("Found instance to attach {}, {}".format(privateIpAddress, instanceId))
            try:
                conn = http.client.HTTPConnection(privateIpAddress, 8080)
                conn.request("GET", "/v1/info")
                r1 = conn.getresponse()
                print(privateIpAddress, r1.status, r1.reason)
                data = json.loads(r1.read().decode('utf-8').replace("'", '"'))
            except Exception as e:
                print("AN EXCEPTION OCCURED", str(e))
                data = {
                    "starting": True
                }
            if not data['starting']:
                print("Instance {} is healthy | Attaching ENI to Instance".format(instanceId))
                print(attach_eni_instance(instanceId, eni_id))
                break
            else:
                print(instanceId + "Instance is unhealthy ...")

def lambda_handler(event, context):
    client = boto3.resource('ec2')
    network_interface = client.NetworkInterface(os.environ['ENI_ID'])
    print("Network ENI status: ", network_interface.status)
    if network_interface.status == "available":
        print("ENI not attached to any coordinator | Looking for suitable coordinator")
        attach_eni(os.environ['ENI_ID'])
    else:
        print("ENI is attached | Checking health of the coordinator")
        data = instance_health(network_interface.attachment['InstanceId'])
        # data = instance_health("i-0b9a126690a1fe099")
        if not data['starting']:
            print("Coordinator is healthy | EXITING")
        else:
            print("Coordinator is unhealthy | REPLACING")
            detach_eni_instance(network_interface.attachment['AttachmentId'])
            attach_eni(os.environ['ENI_ID'])

