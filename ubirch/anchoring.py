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


def set_arguments(service):
    parser = argparse.ArgumentParser(description="Ubirch " + service + " anchoring service")

    parser.add_argument('-s', '--server', help='Choice between KAFKA or SQS, please use capslock',
                        metavar='SQS OR KAFKA', type=str, default=None)
    parser.add_argument('-ll', '--loglevel', help="log level", metavar="LOGLEVEL", default="DEBUG")

    parser.add_argument('-ni', '--networkinfo', help="human readable blockchain network info", metavar="NETWORKINFO", required=True)

    parser.add_argument('-nt', '--networktype', help="blockchain network type: mainnet|testnet", metavar="NETWORKTYPE", default="testnet")


    if service == "ethereum":
        parser.add_argument('-pwd', '--pwd', help="password used to decrypt the Keystore File", metavar="PASSWORD",
                            type=str, default=None)

        parser.add_argument('-kf', '--keyfile', help='location of your keyfile', metavar='PATH TO KEYFILE', type=str,
                            default=None)

        parser.add_argument('-n', '--node', help='Eth node url to connect to', metavar='ETH NODE URL', type=str,
                            default="http://localhost:8545")

        parser.add_argument('-a', '--address', help='Ethereum address used for anchoring', metavar='ETHEREUM ADDRESS',
                            type=str,
                            default='0x31c2CC8b7f15F0A9e7efFdd5Fa02e37E66257744')

    elif service == "IOTA":
        parser.add_argument('-a', '--address', help='IOTA address used for anchoring', metavar='IOTA ADDRESS',
                            type=str,
                            default='9E99GKDY9BYDQ9PGOHHMUWJLBDREMK9BVHUFRHVXCVUIFXLNTZMXRM9TDXJKZDAKIGZIMCJSH9Q9V9GKW')
        parser.add_argument('-d', '--depth', help='depth', metavar='DEPTH', type=int, default=6)

        parser.add_argument('-uri', '--uri', help='URI of the IOTA node', metavar='IOTA NODE URI', type=str,
                            default='https://nodes.devnet.iota.org:443')

        parser.add_argument('-seed', '--seed', help='IOTA seed, default is None', metavar='IOTA SEED',
                            type=str, default=None)

    elif service == "multichain":
        parser.add_argument('-chain', '--chain', help='Name of the multichain blockchain', metavar='CHAIN NAME',
                            type=str, default="ubirch-multichain")

        parser.add_argument('-path', '--path', help='Path to the multichain-cli',
                            metavar='PATH TO MULTICHAIN CLI', type=str, default="/usr/local/bin/multichain-cli")

        parser.add_argument('-key', '--key', help='Key used to publish data on a stream', metavar='KEY',
                            type=str, default=None)

        parser.add_argument('-stream', '--stream', help='Name of the multichain stream used to publish the data', metavar='STREAM NAME',
                            type=str, default=None)

    # SQS queues & Kafka topics

    parser.add_argument('-i', '--input', help='Kafka topic receiving input messages not anchored yet',
                        metavar='INPUT', default='input')

    parser.add_argument('-o', '--output', help='Kafka topic receiving'
                                               'JSON documents: {status:added, message:m, tx_hash: txid} ',
                        metavar='OUTPUT', default='output')

    parser.add_argument('-e', '--errors', help='Kafka topic receiving error messages',
                        metavar='ERRORS', default='errors')

    # KAFKA config

    parser.add_argument('-bs', '--bootstrap_server',
                        help="host:port for kafka consumer/producer, default is localhost:9092",
                        metavar="KAFKA_BOOTSTRAP_SERVER", default='localhost:9092')
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
    """

    Explicit name, used to detect errors in to be sent hashes

    """
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


# FOR SQS ONLY

def connect_sqs(url, region, aws_secret_access_key, aws_access_key_id):
    """

    Connects to the SQS server related to the credentials in parameters

    """
    client = boto3.resource('sqs',
                            endpoint_url=url,
                            region_name=region,
                            aws_secret_access_key=aws_secret_access_key,
                            aws_access_key_id=aws_access_key_id,
                            use_ssl=False)
    return client


def get_queue(queue_name, url, region, aws_secret_access_key, aws_access_key_id):
    """

    :return: Returns the queue with the name: queue_name of the SQS server identified by the other parameters

    """
    client = connect_sqs(url, region, aws_secret_access_key, aws_access_key_id)
    queue = client.get_queue_by_name(QueueName=queue_name)
    return queue


# TRANSACTION SENDING PROCESS

def send(message, server, queue=None, topic=None, producer=None):
    """
    Sends a message to the queue or topic passed as arguments

    :param message: Message to be sent in the kafka topic or the sqs queue
    :param server: Specified whether an SQS server (e.g: elasticMQ) or an Apache Kafka server will be used
    :param queue: SQS queue in which to send the message (if server='SQS')
    :param topic: Apache Kafka topic in which to send the message (if server='KAFKA')
    :param producer: Apache KAFKA producer, = None is not specified

    """

    if server == 'SQS':
        return queue.send_message(
            MessageBody=message
        )
    elif server == 'KAFKA':
        message_bytes = bytes(message.encode('utf-8'))
        if type(topic) == bytes:
            topic = topic.decode('utf-8')
        producer.send(topic, message_bytes)
        producer.flush()


def process_message(message, server, error_messages, output_messages, store_function, producer):
    """
    Anchors the message m in a DLT specified by the store_function parameter.
        Sends error (non hex message and timeouts) in the errorQueue.
        Sends JSON docs containing the txid and the input data in queue2 if the anchoring was successful
        Storefunction should always return either False is the string is non-hex or a dict containing
        {'txid': hash, 'hash': string}

    :param message: message to anchor in the blockchain or tangle
    :param server: choice between 'SQS' or 'KAFKA' : the choice of the messaging service
    :param error_messages: SQS queue or KAFKA topic, depending on the server choice
    :param output_messages: SQS queue or KAFKA topic, depending on the server choice
    :param store_function: function depending on the blockchain or tangle used (IOTA, Multichain, Ethereum)
    :param producer: Kafka producer used to 'produce' messages in a topic

    """

    storing_result = store_function(message)
    if not storing_result:
        json_error = json.dumps({"Not a hash": message})
        send(json_error, server, queue=error_messages, topic=error_messages, producer=producer)

    elif storing_result['status'] == 'timeout':  # For Ethereum
        json_error = json.dumps(storing_result)
        send(json_error, server, queue=error_messages, topic=error_messages, producer=producer)

    else:
        json_data = json.dumps(storing_result)
        send(json_data, server, queue=output_messages, topic=output_messages, producer=producer)


def poll(input_messages, error_messages, output_messages, store_function, server, producer):
    """
    Polls input_messages (kafka topic or SQS queue, depending on the server parameter) and process its messages

    :param input_messages: SQS queue or KAFKA topic, depending on the server choice
    :param error_messages: SQS queue or KAFKA topic, depending on the server choice
    :param output_messages: SQS queue or KAFKA topic, depending on the server choice

    :param store_function: Choice of the type of service between IOTA, MultiChain or Ethereum
    :param server: choice betweeen 'SQS' or 'KAFKA' : the choice of the messaging service
    :param producer: Kafka producer used to 'produce' messages in a topic

    """
    if server == 'SQS':
        messages = input_messages.receive_messages()
        for m in messages:
            message = m.body
            process_message(message, server, error_messages, output_messages, store_function, producer)
            m.delete()

    elif server == 'KAFKA':
        for m in input_messages:
            message = m.value.decode('utf-8')
            process_message(message, server, error_messages, output_messages, store_function, producer)


