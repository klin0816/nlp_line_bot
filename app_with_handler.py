# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
'''from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent,
)'''
from linebot.models import *

import json
from snownlp import SnowNLP
# snownlp github: https://github.com/isnowfy/snownlp
from collections import OrderedDict
from multiprocessing import Pool
import socket
import time
import random
import key

##CKIP
target_host = "140.116.245.151"
target_port = 2001

Attraction = ["附近","周圍","景點","周邊"]
Food = ["美食","吃","好吃","食物"]

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
#channel_secret = os.getenv('LINE_CHANNEL_SECRET','2b7d9859ceced4df8b4a55b367a2f8a2')
#channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'BwaoWOUlEHd8jMTsZdgSgg78hs8JmJunlZolSEHgOhY6aNec43pRAney/8Us2vYCd9mYlFQO1YdbD9iR5XDeYK7G9PORoGm9yrcVsvP83ElL/iDkS8n8bpspgoGMbnMfr0bdj9cPBHvdSKTMpTSvlQdB04t89/1O/w1cDnyilFU=')
channel_secret, channel_access_token = key.get_key()
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def seg(sentence):
    # create socket
    # AF_INET 代表使用標準 IPv4 位址或主機名稱
    # SOCK_STREAM 代表這會是一個 TCP client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client 建立連線
    client.connect((target_host, target_port))
    # 傳送資料給 target
    data = "seg@@" + str(sentence)
    client.send(data.encode("utf-8"))
    
    # 回收結果信息
    data = bytes()
    while True:
        request = client.recv(8)
        if request:
            data += request
            begin = time.time()
        else:
            break

    WSResult = []
    response = data
    if(response is not None or response != ''):
        response = response.decode('utf-8').split()
        for resp in response:
            resp = resp.strip()
            resp = resp[0:len(resp)-1]
            temp = resp.split('(')
            word = temp[0]
            pos = temp[1]
            WSResult.append((word,pos))

    return WSResult

def cal_BM25(data, segment_list):
    question_list = []
    ## make a quesion only list from json
    for i in range(0, len(data)):
        question_list.append(data[i]['question'])

    question_word = []
    ## send every question in CKIP and save result in question_word
    for question in question_list:
        question_temp = []
        result = seg(question) # send to CKIP
        for words in result:
            question_temp.append(words[0]) # result save in question_temp
        question_word.append(question_temp) # save result of every question in question_word
    #print(question_word)
    ## calculate the BM25
    s = SnowNLP(question_word)
    s.tf
    s.idf
    #print(segment_list)   ##debugger
    return s.sim(segment_list)

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)
    data = json.load(open('data/database.json', 'r')) #load json to read
    print("message_text")
    #state = 0 = introduction
    #state = 1 = attraction
    #state = 2 = food
    #state = 3 = line
    state = 0

    segment_list = [i[0] for i in seg(event.message.text)] # send input line in CKIP and save result in segment_list
    print(segment_list)
    for segment in segment_list:
        if segment in Food:
            state = 2
        elif segment in Attraction:
            state = 1
        else:
            state = 0

    rand = random.randint(0,1)

    BM25 = cal_BM25(data, segment_list) # calculate the acc score between segment_list with every question(question_word)
    BM25_max= BM25.index(max(BM25)) # find the index of list which acc score is the best
    if state == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='介紹： ' + data[BM25_max]['introduce'])
        )
    elif state == 1:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='景點： ' + data[BM25_max]['attraction'][rand])
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='地址： ' + data[BM25_max]['a_address'][rand])
        )
    elif state == 2:
        a = str(data[BM25_max]['f_image'][0])
        b = str(data[BM25_max]['f_image'][1])
        carousel_template = CarouselTemplate(columns=[
	    CarouselColumn(thumbnail_image_url=a, text=' ', title=data[BM25_max]['food'][0], actions=[
                URIAction(label='Google Maps', uri=data[BM25_max]['f_link'][0]),
            ]),
            CarouselColumn(thumbnail_image_url=b, text=' ', title=data[BM25_max]['food'][1], actions=[
                URIAction(label='Google Maps', uri=data[BM25_max]['f_link'][1]),
            ]),
        ])
        template_message = TemplateSendMessage(
            alt_text='Carousel alt text', template=carousel_template)
        line_bot_api.reply_message(event.reply_token, template_message)   
        
        '''line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='美食： ' + data[BM25_max]['food'][rand])
        )'''

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
