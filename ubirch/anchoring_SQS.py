# coding: utf-8
#
# ubirch anchoring
#
# @author Victor Patrin
#
# Copyright (c) 2018 ubirch GmbH.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import argparse
import boto3


def connect(url, region, aws_secret_access_key, aws_access_key_id):
    """Connects to the SQS server related to those credentials."""
    client = boto3.resource('sqs',
                            endpoint_url=url,  #
                            region_name=region,  #
                            aws_secret_access_key=aws_secret_access_key,  # parameters passed as arguments
                            aws_access_key_id=aws_access_key_id,  #
                            use_ssl=False)
    return client


def getQueue(queue_name, url, region, aws_secret_access_key, aws_access_key_id):
    """Returns the queue with the name queue_name of the server identified by the other parameters"""
    client = connect(url, region, aws_secret_access_key, aws_access_key_id)
    queue = client.get_queue_by_name(QueueName=queue_name)
    print("The queue : " + queue_name + " has : " + queue.url + " for URL")
    return queue


def set_arguments(servicetype):
    """Set up the credentials of connection to be those of the elasticMQ Server if not specified otherwise"""

    parser = argparse.ArgumentParser(description="Ubirch " + servicetype + " anchoring service using SQS queues")
    parser.add_argument('-u', '--url',
                        help="endpoint url of the sqs server, input localhost:9324 for local connection (default)",
                        metavar="URL", type=str, default="http://localhost:9324")
    parser.add_argument('-r', '--region', help="region name of sqs server, (default : 'elasticmq' for local)",
                        metavar="REGION", type=str, default="elasticmq")
    parser.add_argument('-ak', '--accesskey', help="AWS secret access key, input 'x'for local connection (default)",
                        metavar="SECRETACCESSKEY", type=str, default="x")
    parser.add_argument('-ki', '--keyid', help="AWS access key id, input 'x' for local connection (default)",
                        metavar="KEYID", type=str, default="x")

    parser.add_argument('-p', '--pwd', help="password used to decrypt the Keystore File",
                        metavar="PASSWORD", type=str)
    parser.add_argument('-kf', '--keyfile', help='location of your keyfile', metavar='PATH TO KEYFILE', type=str)

    return parser.parse_args()


def send(queue, msg):
    """ Sends a message to the queue, return a SQS.Message element"""
    return queue.send_message(
        MessageBody=msg
    )


def is_hex(s):
    """Tests if the string s is hex (True) or not (False)"""
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


# storefunction should always return either False is the string is non-hex or a dict containing {'txid': hash, 'hash': string}
def process_message(m, errorQueue, queue2, storefunction):
    """Anchors the message m in a DLT specified by the storefunction parameter.
    Sends error (non hex message and timeouts) in the errorQueue.
    Sends JSON docs containing the txid and the input data in queue2 if the anchoring was successful"""
    storingResult = storefunction(m.body) #Anchoring of the message body
    if storingResult == False:
        json_error = json.dumps({"Not a hash": m.body})
        send(errorQueue, json_error)

    elif storingResult['status'] == 'timeout':
        json_error = json.dumps(storingResult)
        send(errorQueue, json_error)

    else:
        json_data = json.dumps(storingResult)
        send(queue2, json_data)

    m.delete()


def poll(queue1, errorQueue, queue2, storefunction):
    """Process messages received from queue1"""
    messages = queue1.receive_messages()  # Note: MaxNumberOfMessages default is 1.
    for m in messages:
        message = m.decode('utf-8')
        process_message(message, errorQueue, queue2, storefunction)


