from bson import ObjectId
from code.models.models import Account, Trade, Position, PrimaryKey, Direction
from code.mongo.database import account_collection, trade_collection, position_collection
from datetime import datetime
import redis
import logging
import random
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
        "trades": [trade.model_dump() for trade in account.trades],
        "positions": [position.model_dump() for position in account.positions]
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
            "account": {
                "account_id": trade.primaryKey.account.account_id,
                "account_name": trade.primaryKey.account.account_name
            },
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
    logger.info(f"Adding trade...")
    result = await trade_collection.insert_one(trade_data)
    trade = await trade_collection.find_one({"_id": result.inserted_id})
    logger.info(f"Trade added: {trade}")
    return trade

# Embed Trade in Account
async def add_trade_to_account(account_id: str, trade: Trade) -> dict:
    pass


def position_helper(position: Position) -> dict:
    pass

# Add Position
async def add_position(position: Position) -> dict:
    pass

# Embed Position in Account
async def add_position_to_account(account_id: str, position: Position) -> dict:
    pass
