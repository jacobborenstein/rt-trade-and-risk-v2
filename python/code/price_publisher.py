import time
from fastapi import FastAPI, Request
from httpx import get
from numpy import fromfile
import redis
import price_scraper
import json

app = FastAPI()

r = redis.Redis(host='redis', port=6379)
r.ping()
@app.post("/publish/{ticker}")
async def publish_single_ticker(request: Request, ticker: str):
    while True:
        time.sleep(5)
        r.publish(ticker, price_scraper.get_price(ticker))
        print("status : Sent")

@app.post("/publish/bulk/s&p500")
async def publish_500():
    while True:
        dic = price_scraper.get_s_and_p()
        data = json.dumps(dic)
        print(data)
        r.publish("prices_and_values", data)
        print("status : Sent " + data)

        time.sleep(30)
