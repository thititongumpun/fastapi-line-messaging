import os
from typing import List, Optional, Text

from fastapi import APIRouter, HTTPException, Header, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerMessage, \
    StickerSendMessage, FlexSendMessage
from pydantic import BaseModel
from time import time
import httpx
import json

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

URL = os.getenv('SENTIMENT_API')

router = APIRouter(
    prefix="/webhooks",
    tags=["chatbot"],
    responses={404: {"description": "Not found"}},
)

class Line(BaseModel):
    destination: str
    events: List[Optional[None]]

async def request(client):
    params = {'sentimentText': 'ห่วยแตก'}
    response = await client.get(URL, params=params)
    return response.json()

async def task():
    async with httpx.AsyncClient() as client:        
        result = await request(client)
        return result        

@router.get("/test")
async def get_predict():
    start = time()
    res = await task()
    resStr = json.dumps(res['Predict'])
    print(resStr)
    print(f"time: {time()-start}")
    return res

@router.post("/line")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="chatbot handle body error.")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    print("!!!!!!!!!!!!!!!!!!!!!!")
    print(f'text: {event.message.text}')
    print("!!!!!!!!!!!!!!!!!!!!!!")

    params = {'sentimentText': event.message.text}
    r = httpx.get(URL, params=params)
    sentiment = r.json()['Sentiment']
    predict = r.json()['Predict']
    serviceType = r.json()['Service Type']
    textLine = f'Text: {sentiment}'
    textSecondLine = f'Predict: {predict}'
    textThirdLine = f'Service Type: {serviceType}'

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
        alt_text='hello',
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "Sentiment Service Prediction",
                    "weight": "bold",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": textLine,
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": textSecondLine,
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": textThirdLine,
                    "size": "xs"
                }
                ]
            }
            }
        )
    )

@handler.add(MessageEvent, message=StickerMessage)
def sticker_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(package_id='6136', sticker_id='10551379')
    )