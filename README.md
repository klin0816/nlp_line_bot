# NLP Line Bot

## Introduction
This is a final project for NLP_CSIE_1062_NCKU

## Execute
To install requirement.py
```
pip install -r requirement.txt
```

To execute this code
```
python3 app_with_handler.py --port <port>
```

Recommend run this with ngrok


## Key.py
the `key.py` that is in .gitognore is for `app_with_handler.py` get the line bot private key
sample code is in below
```
import os

def get_key():
        channel_secret = os.getenv('LINE_CHANNEL_SECRET',<your_LINE_CHANNEL_SECRET>)
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '<your_LINE_CHANNEL_ACCESS_TOKEN>')

        return channel_secret, channel_access_token
```
