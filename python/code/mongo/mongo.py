import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from code.models.models import Trade, Account, Position
from code.mongo.crud import add_account, get_account, get_random_account, add_trade, add_position, get_trades_by_account_by_ticker
import redis
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

channels = ['accounts', 'trades-to-mongo', 'positions']

async def main():
    r = redis.Redis(host='localhost', port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe(channels)
    while True:
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    await handle_message(r, message)
        except Exception as e:
            logger.error(f"Error: {e}")
            await asyncio.sleep(5)

async def handle_message(r, message):
    channel = message['channel'].decode('utf-8')
    data = message['data']
    logger.info(f"mongo-1) Received data on {channel} channel")
                    
    if channel == 'accounts':
        account_dict = json.loads(data)
        logger.info(f"mongo-2) Received account data: {account_dict}")
        account = Account(**account_dict)
        result = await add_account(account)
        logger.info(f"mongo-3) Added account: {result}")
                    
    elif channel == 'trades-to-mongo':
        trade_dict = json.loads(data)
        logger.info(f"mongo-4) Received trade data: {trade_dict}")
        trade = Trade(**trade_dict)
        result = await add_trade(trade)
        logger.info(f"mongo-5) Added trade: {result}")
        trades = await get_trades_by_account_by_ticker(trade.primaryKey.account_id, trade.ticker)
        # Convert trades to JSON serializable format
        trades_json = json.dumps([{
            **trade.model_dump(by_alias=True),
            'executedTime': trade.executed_time.isoformat()  # Convert datetime to string
        } for trade in trades])
        r.publish('trades-from-mongo', trades_json)
        logger.info(f"mongo-6) Published trades for ticker {trade.ticker} to Position Aggregator")
                    
    elif channel == 'positions':
        position_dict = json.loads(data)
        logger.info(f"mongo-7) Received position data: {position_dict}")
        position = Position(**position_dict)
        result = await add_position(position)
        logger.info(f"mongo-8) Added position: {result}")

if __name__ == "__main__":
    asyncio.run(main())
