import redis
from fastapi import FastAPI, Request
from models import Trade

app = FastAPI()

r = redis.Redis(host='localhost', port=6379)
r.ping()

@app.post("/publish/trade")
async def publish_trade(trade: Trade):
    r.publish('trades', trade.model_dump_json(by_alias=True))
    return {"status": "Sent"}