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

def set_arguments(servicetype):
    parser = argparse.ArgumentParser(description="Ubirch " + servicetype + " anchoring service")

    parser.add_argument('-s', '--server', help='Choice between KAFKA or SQS, please use capslock', metavar='SQS OR KAFKA', type=str)

    if servicetype == "MultiChain":
        parser.add_argument('-rpcuser', help="For multichain API calls", metavar="RPC USER",
                            type=str, default='multichainrpc')
        parser.add_argument('-rpcpasswd', help="For multichain API calls", metavar="RPC PASSWORD",
                            type=str, default='YoUrLoNgRpCpAsSwOrD')
        parser.add_argument('-rpchost', help="For multichain API calls", metavar="RPC HOST",
                            type=str, default='localhost')
        parser.add_argument('-rpcport', help="For multichain API calls", metavar="RPC PORT",
                            type=str, default='4770')
        parser.add_argument('-chainname', help="For multichain API calls", metavar="CHAIN NAME",
                            type=str, default='ubirch-multichain')

    if servicetype == "ethereum":
        parser.add_argument('-pwd', '--pwd', help="password used to decrypt the Keystore File", metavar="PASSWORD",
                            type=str)
        parser.add_argument('-kf', '--keyfile', help='location of your keyfile', metavar='PATH TO KEYFILE', type=str)

    # KAFKA config
    parser.add_argument('-p', '--port',
                        help="port of the producer or consumer, default is 9092",
                        metavar="KAFKA PORT", type=list, default=['localhost:9092'])
    # SQS config
    parser.add_argument('-u', '--url',
                        help="endpoint url of the sqs server, input localhost:9324 for local connection (default)",
                        metavar="URL", type=str, default="http://localhost:9324")
    parser.add_argument('-r', '--region', help="region name of sqs server, (default : 'elasticmq' for local)",
                        metavar="REGION", type=str, default="elasticmq")
    parser.add_argument('-ak', '--accesskey', help="AWS secret access key, input 'x'for local connection (default)",
                        metavar="SECRETACCESSKEY", type=str, default="x")
    parser.add_argument('-ki', '--keyid', help="AWS access key id, input 'x' for local connection (default)",
                        metavar="KEYID", type=str, default="x")

    return parser.parse_args()

def is_hex(s):
    """Explicit name, used to detect errors in to be sent hashes"""
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

# FOR SQS ONLY
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


# SENDING PROCESS
def send(message, server, queue=None, topic=None, producer=None):
    if server == 'SQS':
        """ Sends a message to the queue, return a SQS.Message element"""
        return queue.send_message(
            MessageBody=message
        )
    elif server == 'KAFKA':
        """ Sends a message to the topic via the producer and then flushes"""
        message_bytes = bytes(message.encode('utf-8'))
        if type(topic) == bytes:
            topic = topic.decode('utf-8')
        producer.send(topic, message_bytes)
        producer.flush()


"""Anchors the message m in a DLT specified by the storefunction parameter.
    Sends error (non hex message and timeouts) in the errorQueue.
    Sends JSON docs containing the txid and the input data in queue2 if the anchoring was successful
    Storefunction should always return either False is the string is non-hex or a dict containing {'txid': hash, 'hash': string}"""


def process_message(message, server, errorQueue, queue2, storefunction, producer):
        storingResult = storefunction(message)
        if storingResult == False:
            json_error = json.dumps({"Not a hash": message})
            send(json_error, server, queue=errorQueue, topic='errorQueue', producer=producer)
            if server == 'SQS':
                message.delete()

        elif storingResult['status'] == 'timeout':  # For Ethereum
            json_error = json.dumps(storingResult)
            send(json_error, server, queue=errorQueue, topic='errorQueue', producer=producer)
            if server == 'SQS':
                message.delete()

        else:
            json_data = json.dumps(storingResult)
            send(json_data, server, queue=queue2, topic='queue2', producer=producer)
            if server == 'SQS':
                message.delete()



def poll(queue1, errorQueue, queue2, storefunction, server, producer):
    """Process messages received from queue1"""
    if server == 'SQS':
        messages = queue1.receive_messages()  # Note: MaxNumberOfMessages default is 1.
        for m in messages:
            message = m.body
            print('pollling message : ', message)
            process_message(message, server, errorQueue, queue2, storefunction, producer)
    elif server == 'KAFKA':
        for m in queue1:
            message = m.value.decode('utf-8')
            process_message(message, server, errorQueue, queue2, storefunction, producer)


