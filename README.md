# ubirch library for ubirch anchoring services

This library contains several useful tools used to connect to a SQS server and anchor messages retrieved from a queue to the IOTA Tangle or the Ethereum Blockchain.
 
## Usage

### Configuration, connection to a SQS server and retrieving queues.

To set up the different arguments needed to connect to the SQS Server and to access the ETH Wallet.
```python
from ubirch.anchoring import *

args = set_arguments(servicetype='ethereum') # Or 'iota"

#To access the SQS Queue
url = args.url
region = args.region
aws_secret_access_key = args.accesskey
aws_access_key_id = args.keyid

#To unlock your wallet
password = args.pwd
keyfile = args.keyfile

queue1 = getQueue('queue1', url, region, aws_secret_access_key, aws_access_key_id)

```

### Testing

Unit tests are added to test the functionality of all objects provided in this library.

```bash
python3 -m unittest discover
``` 

# License 

The protocol and its implementation are publicized under the [Apache License 2.0](LICENSE).