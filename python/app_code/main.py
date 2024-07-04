import redis
from fastapi import FastAPI
from app_code.models.models import Trade, Account, PrimaryKey, Direction
import json
from datetime import datetime
import logging
import uuid
import random
from app_code.mongo.database import account_collection, trade_collection, position_collection
from app_code.mongo.crud import get_random_account, get_account, get_recent_position

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
    return {"status": "Created new  account: " + account.account_id}

@app.post("/publish/trade")
async def publish_trade():
    logger.info("main-1) Publishing trade...")
    trade = await generate_trade()
    logger.info(f"main-2) created trade")
    trade_data = trade.model_dump(by_alias=True)
    trade_data['executedTime'] = trade_data['executedTime'].isoformat()  # Convert datetime to string
    r.publish('trades-to-mongo', json.dumps(trade_data))
    logger.info(f"main-3) published trade: {trade_data}")
    return {"status": "Trade Sent"}

@app.post("/publish/trade/{account_id}")
async def publish_trade_for_account(account_id: str):
    logger.info("main-1) Publishing trade...")
    trade = await generate_trade(account_id)
    logger.info(f"main-2) created trade")
    trade_data = trade.model_dump(by_alias=True)
    trade_data['executedTime'] = trade_data['executedTime'].isoformat()
    r.publish('trades-to-mongo', json.dumps(trade_data))
    logger.info(f"main-3) published trade: {trade_data}")
    return {"status": "Trade Sent"}
    
@app.post("/publish/trade/{account_id}/{ticker}")
async def publish_trade_for_account(account_id: str, ticker: str):
    logger.info("main-1) Publishing trade...")
    trade = await generate_trade(account_id, ticker)
    logger.info(f"main-2) created trade")
    trade_data = trade.model_dump(by_alias=True)
    trade_data['executedTime'] = trade_data['executedTime'].isoformat()
    r.publish('trades-to-mongo', json.dumps(trade_data))
    logger.info(f"main-3) published trade: {trade_data}")
    return {"status": "Trade Sent"}

@app.post("/publish/trade/{account_id}/{ticker}/{quantity}")
async def publish_trade_for_account(account_id: str, ticker: str, quantity: int):
    logger.info("main-1) Publishing trade...")
    trade = await generate_trade(account_id, ticker, quantity)
    logger.info(f"main-2) created trade")
    trade_data = trade.model_dump(by_alias=True)
    trade_data['executedTime'] = trade_data['executedTime'].isoformat()
    r.publish('trades-to-mongo', json.dumps(trade_data))
    logger.info(f"main-3) published trade: {trade_data}")
    return {"status": "Trade Sent"}

@app.get("/get/position/{account_id}/{ticker}")
async def get_position(account_id: str, ticker: str):
    position = await get_recent_position(account_id, ticker)
    return position


async def generate_trade(account_id: str = None, ticker: str = None, quantity: int = None) -> Trade:
    logger.info("Generating trade...")
    tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    trade_ticker = ticker if ticker is not None else random.choice(tickers)
    # choose a random account from MongoDB unless an account_id is provided
    account_data = await get_random_account() if account_id is None else await get_account(account_id)
    logger.info(f"got random account from mongo")

    # Map MongoDB fields to Pydantic model fields
    account_data['accountId'] = account_data.pop('account_id')
    account_data['accountName'] = account_data.pop('account_name')
    account = Account(**account_data)

    primaryKey = PrimaryKey(accountId=account.account_id, tradeId=generate_trade_id(trade_ticker))
    quantity = random.randint(1, 10) if quantity is None else quantity
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
