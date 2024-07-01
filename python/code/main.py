import redis
from fastapi import FastAPI
from code.models.models import Trade, Account, PrimaryKey, Direction
import json
from datetime import datetime
import logging
import uuid
import random
from code.mongo.database import account_collection, trade_collection, position_collection
from code.mongo.crud import get_random_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
r = redis.Redis(host='localhost', port=6379)
r.ping()

@app.post("/publish/account/new/{name}")
async def publish_account(account: Account, name: str):
    account.account_name = name
    account.account_id = "ACC_" + str(uuid.uuid4())
    r.publish('accounts', account.model_dump_json(by_alias=True))
    return {"status": "Sent " + account.account_id}

@app.post("/publish/trade")
async def publish_trade():
    logger.info("Publishing trade...")
    trade = await generate_trade()
    logger.info(f"created trade")
    trade_data = trade.model_dump(by_alias=True)
    trade_data['executedTime'] = trade_data['executedTime'].isoformat()  # Convert datetime to string
    r.publish('trades-to-mongo', json.dumps(trade_data))
    logger.info(f"published trade: {trade_data}")
    return {"status": "Trade Sent"}

async def generate_trade() -> Trade:
    logger.info("Generating trade...")
    tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    trade_ticker = random.choice(tickers)
    account_data = await get_random_account()
    logger.info(f"got random account from mongo")

    # Map MongoDB fields to Pydantic model fields
    account_data['accountId'] = account_data.pop('account_id')
    account_data['accountName'] = account_data.pop('account_name')
    account = Account(**account_data)

    primaryKey = PrimaryKey(account=account, tradeId=generate_trade_id(trade_ticker))
    quantity = random.randint(1, 10)
    executed_price = random.randint(100, 200)
    return Trade(
        primaryKey=primaryKey,
        ticker=trade_ticker,
        direction=Direction.BUY,
        quantity=quantity,
        executedPrice=executed_price,
        executedUser="user1",
        executedTime=datetime.now()
    )


def generate_trade_id(ticker: str) -> str:
    return ticker + "_" + str(uuid.uuid4()) + "_" + str(datetime.now().timestamp())
