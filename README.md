# ubirch library for ubirch anchoring services

This library contains several useful tools used to connect to a SQS server and anchor messages retrieved from a queue to the IOTA Tangle or the Ethereum Blockchain.
 
## Usage

### Configuration, connection to a SQS server and retrieving queues.

To set up the different arguments needed to connect to the SQS Server and to access the ETH Wallet.
```python
from ubirch.anchoring import *

args = set_arguments(servicetype='ethereum') # Or 'IOTA or 'MultiChain'

#To access the Kafka server
port = args.port

#To unlock your wallet (if servicename=='ethereum')
password = args.pwd
keyfile = args.keyfile

queue1 = getQueue('queue1', url, region, aws_secret_access_key, aws_access_key_id)

```
### Polling a queue and processing its messages

Please see [ubirch-ethereum-service](https://github.com/ubirch/ubirch-ethereum-service/blob/master/ethereumService.py) or [ubirch-iota-service](https://github.com/ubirch/ubirch-iota-service/blob/master/iotaService.py) to how this library is put into action. 

### Testing

Unit tests are added to test the functionality of all objects provided in this library.

```bash
python3 -m unittest discover
``` 

# License 

This library is publicized under the [Apache License 2.0](LICENSE).