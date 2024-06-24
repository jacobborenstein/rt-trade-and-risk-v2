import time
from fastapi import FastAPI, Request
from httpx import get
from numpy import fromfile
import redis
import price_scraper

app = FastAPI()

r = redis.Redis(host='localhost', port=6379)
r.ping()
ticker_list = open("s&p_500_tickers.txt").read().splitlines()
print(ticker_list)
@app.post("/publish/{ticker}")
async def publish_single_ticker(request: Request, ticker: str):
    while True:
        time.sleep(5)
        r.publish(ticker, price_scraper.get_price(ticker))
        print("status : Sent")

@app.post("/publish//bulk/s&p500")
async def publish_500():
    while True:
        dic = price_scraper.get_s_and_p()
        for t in dic:
            r.publish(t, dic.get(t))
            print("status : Sent from ticker " + t)
        time.sleep(30)

