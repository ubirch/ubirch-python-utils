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

# def producerInstance(port):
#     """Creates an instance of a producer """
#     producer_instance = KafkaProducer(bootstrap_servers=port)
#     return producer_instance


# def consumerInstance(topics, port):
#     """Creates an instance of consumer of a defined topic """
#     consumer_instance = KafkaConsumer(topics, bootstrap_servers=port)
#     return consumer_instance


def set_arguments(servicetype):
    parser = argparse.ArgumentParser(description="Ubirch " + servicetype + " anchoring service using Kafka")
    parser.add_argument('-p', '--port',
                        help="port of the producer or consumer, default is 9092",
                        metavar="KAFKA PORT", type=list, default=['localhost:9092'])


    if servicetype == "MultiChain":
        parser.add_argument('-rpcuser', help="For multichain API calls", metavar="RPC USER",
                            type=str, default = 'multichainrpc')
        parser.add_argument('-rpcpasswd', help="For multichain API calls", metavar="RPC PASSWORD",
                            type=str, default = 'YoUrLoNgRpCpAsSwOrD')
        parser.add_argument('-rpchost', help="For multichain API calls", metavar="RPC HOST",
                            type=str, default = 'localhost')
        parser.add_argument('-rpcport', help="For multichain API calls", metavar="RPC PORT",
                            type=str, default = '4770')
        parser.add_argument('-chainname', help="For multichain API calls", metavar="CHAIN NAME",
                            type=str, default = 'ubirch-multichain')

    if servicetype == "ethereum":
        parser.add_argument('-pwd', '--pwd', help="password used to decrypt the Keystore File", metavar="PASSWORD", type=str)
        parser.add_argument('-kf', '--keyfile', help='location of your keyfile', metavar='PATH TO KEYFILE', type=str)

    return parser.parse_args()


def send(producer, topic, message):
    """ Sends a message to the topic via the producer and then flushes"""
    message_bytes = bytes(message.encode('utf-8'))
    if type(topic) == bytes:
        topic = topic.decode('utf-8')
    producer.send(topic, message_bytes)
    producer.flush()


def is_hex(s):
    """Tests if the string s is hex (True) or not (False)"""
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


# storefunction should always return either False is the string is non-hex or a dict containing {'txid': hash, 'hash': string}
def process_message(message, errorQueue, queue2, storefunction, producer):
    """Anchors the message m in a DLT specified by the storefunction parameter.
    Sends error (non hex message and timeouts) in the errorQueue.
    Sends JSON docs containing the txid and the input data in queue2 if the anchoring was successful"""
    storingResult = storefunction(message) #Anchoring of the message body
    if storingResult == False:
        json_error = json.dumps({"Not a hash": message})
        send(producer, errorQueue, json_error)

    elif storingResult['status'] == 'timeout': #For Ethereum
        json_error = json.dumps(storingResult)
        send(producer, errorQueue, json_error)

    else:
        json_data = json.dumps(storingResult)
        send(producer, queue2, json_data)


def poll(queue1, errorQueue, queue2, storefunction, producer):
    """Process messages received from queue1"""
    for m in queue1:
        message = m.value.decode('utf-8')
        process_message(message, errorQueue, queue2, storefunction, producer)

