import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio
from app_code.models.models import Trade, Account, Position, TickerPrice
from app_code.mongo.crud import add_account, get_account, get_random_account, add_trade, add_position, get_trades_by_account_by_ticker, get_recent_position, add_ticker_price, get_price_for_ticker
import redis
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

channels = ['accounts', 'trades-to-mongo', 'positions', 'prices', 'prices_and_values']

async def main():
    r = redis.Redis(host='redis', port=6379)
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
        r.publish('trade-collection-from-mongo', trades_json)
        logger.info(f"mongo-6) Published trades for ticker {trade.ticker} to Position Aggregator")
        
        # create single trade json to send to redis db
        single_trade_json = json.dumps([{
            **trade.model_dump(by_alias=True),
            'executedTime': trade.executed_time.isoformat()  # Convert datetime to string
        }])
        r.publish('trades-from-mongo', single_trade_json)
        logger.info(f"mongo: Published new trade for ticker {trade.ticker} to redis db")

    elif channel == 'positions':
        position_dict = json.loads(data)
        logger.info(f"mongo-7) Received position data: {position_dict}")
        position = Position(**position_dict)
        last_position_data = await get_recent_position(position.account_id, position.ticker)

        if last_position_data:
            logger.info(f"mongo-8) Last position data: {last_position_data}")
            last_updated_str = last_position_data['last_updated']
            if isinstance(last_updated_str, datetime):
                last_updated_dt = last_updated_str
            else:
                last_updated_dt = datetime.fromisoformat(last_updated_str)
            last_time_sent_to_mongo = last_updated_dt.timestamp()
            logger.info(f"mongo-9) Last time sent to mongo: {last_time_sent_to_mongo}")
        else:
            last_time_sent_to_mongo = 0

        current_time = position.last_updated.timestamp()
        logger.info(f"mongo-10) Current time: {current_time}")
        time_difference = current_time - last_time_sent_to_mongo
        logger.info(f"mongo-11) Time difference: {time_difference}")

        if time_difference >= 600:
            result = await add_position(position)
            logger.info(f"mongo-12) Added position: {result}")
        else:
            logger.info(f"mongo-13) Position data not sent to MongoDB. Already sent within 10 minutes.")

    elif channel == 'prices_and_values':
        price_dict = json.loads(data)
        # logger.info(f"mongo-7) Received price data: {price_dict}")
        
        ticker_price = TickerPrice(**price_dict)
        # logger.info(f"mongo-7.5) Parsed TickerPrice: {ticker_price}")
        
        last_tickerprice_data = await get_price_for_ticker(ticker_price.ticker)
        if last_tickerprice_data:
            last_updated_str = last_tickerprice_data['time']
            # logger.info(f"mongo-7.6) Last updated string from Mongo: {last_updated_str}")

            if isinstance(last_updated_str, datetime):
                last_updated_dt = last_updated_str
            else:
                last_updated_dt = datetime.fromisoformat(last_updated_str)
            
            last_time_sent_to_mongo = last_updated_dt.timestamp()
            # logger.info(f"mongo-8) Last time sent to mongo (timestamp): {last_time_sent_to_mongo}")
            # logger.info(f"mongo-8.1) Last time sent to mongo (datetime): {last_updated_dt}")
        else:
            last_time_sent_to_mongo = 0
            logger.info("mongo-8) No previous price data found in MongoDB for this ticker.")

        current_time = ticker_price.time.timestamp()
        time_difference = current_time - last_time_sent_to_mongo

        # logger.info(f"mongo-11) Current time (timestamp): {current_time}")
        # logger.info(f"mongo-11.1) Current time (datetime): {datetime.fromtimestamp(current_time)}")
        # logger.info(f"mongo-11.2) Time since last sent to mongo: {time_difference} seconds ({time_difference / 60} minutes)")

        if time_difference >= 600:
            result = await add_ticker_price(ticker_price)
            # logger.info(f"mongo-12) Added price data for ticker: {ticker_price.ticker} and price: {ticker_price.price} to MongoDB")
        # else:
            # logger.info(f"mongo-13) TickerPrice data not sent to MongoDB. Already sent within 10 minutes.")

if __name__ == "__main__":
    asyncio.run(main())
