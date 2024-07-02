from bson import ObjectId
from code.models.models import Account, Trade, Position, PrimaryKey, Direction
from code.mongo.database import account_collection, trade_collection, position_collection
from datetime import datetime
import redis
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = redis.Redis(host='localhost', port=6379)
r.ping()

# Helper function to convert a Pydantic model to a dict suitable for MongoDB
def account_helper(account: Account) -> dict:
    return {
        "account_id": account.account_id,
        "account_name": account.account_name,
    }

# Add Account
async def add_account(account: Account) -> dict:
    account_data = account_helper(account)
    result = await account_collection.insert_one(account_data)
    account = await account_collection.find_one({"_id": result.inserted_id})
    return account

# Get Account
async def get_account(account_id: str) -> dict:
    account = await account_collection.find_one({"account_id": account_id})
    if account:
        return account
    return None

# Get a Random Account
async def get_random_account() -> dict:
    account_list = await account_collection.aggregate([{ "$sample": { "size": 1 } }]).to_list(1)
    if account_list:
        return account_list[0]
    return None

def trade_helper(trade: Trade) -> dict:
    return {
        "primary_key": {
            "account_id": trade.primaryKey.account_id,
            "trade_id": trade.primaryKey.trade_id
        },
        "ticker": trade.ticker,
        "direction": trade.direction,
        "quantity": trade.quantity,
        "executed_price": trade.executed_price,
        "executed_user": trade.executed_user,
        "executed_time": trade.executed_time
    }

# Add Trade
async def add_trade(trade: Trade) -> dict:
    trade_data = trade_helper(trade)
    logger.info(f"crud-1) Adding trade...")
    result = await trade_collection.insert_one(trade_data)
    trade = await trade_collection.find_one({"_id": result.inserted_id})
    logger.info(f"crud-2) Trade added: {trade}")
    return trade

# Get trades by account ID and ticker
async def get_trades_by_account_by_ticker(account_id: str, ticker: str) -> list:
    trades = await trade_collection.find({
        "primary_key.account_id": account_id,
        "ticker": ticker
    }).to_list(length=None)
    # Convert MongoDB data to Pydantic models
    return [Trade(
        primaryKey=PrimaryKey(
            accountId=trade['primary_key']['account_id'],
            tradeId=trade['primary_key']['trade_id']
        ),
        ticker=trade['ticker'],
        direction=trade['direction'],
        quantity=trade['quantity'],
        executedPrice=trade['executed_price'],
        executedUser=trade['executed_user'],
        executedTime=trade['executed_time']
    ) for trade in trades]

def position_helper(position: Position) -> dict:
    return {
        "account_id": position.account_id,
        "ticker": position.ticker,
        "quantity": position.quantity,
        "position_type": position.position_type,
        "avg_price": position.avg_price,
        "last_updated": position.last_updated
    }

# Add Position
async def add_position(position: Position) -> dict:
    position_data = position_helper(position)
    result = await position_collection.insert_one(position_data)
    position = await position_collection.find_one({"_id": result.inserted_id})
    return position
