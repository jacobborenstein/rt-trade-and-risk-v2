import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from code.models.models import Trade, Account, Position
from code.mongo.crud import add_account, get_account, get_random_account, add_trade, add_position
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
    logger.info(f"1) Received data on {channel} channel")
                    
    if channel == 'accounts':
        account_dict = json.loads(data)
        logger.info(f"2) Received account data: {account_dict}")
        account = Account(**account_dict)
        result = await add_account(account)
        logger.info(f"3) Added account: {result}")
                    
    elif channel == 'trades-to-mongo':
        trade_dict = json.loads(data)
        logger.info(f"2) Received trade data: {trade_dict}")
        trade = Trade(**trade_dict)
        result = await add_trade(trade)
        logger.info(f"3) Added trade: {result}")
        r.publish('trades-from-mongo', json.dumps(trade_dict))
        logger.info(f"4) Published trade data to trades-from-mongo channel")
                    
    elif channel == 'positions':
        pass


if __name__ == "__main__":
    asyncio.run(main())
