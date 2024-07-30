import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app_code.models.models import Direction
from app_code.mongo.crud import get_prices_from_datetime
from app_code.mongo.crud import get_trades_by_account_by_ticker
from app_code.authorization.streamlit_main import get_backend_url
from app_code.redis_cache.cache_database import retrieve_position_data, PositionKey, retrieve_price_data
import asyncio
import json
import time
from datetime import datetime, timedelta
import redis
import logging
import requests





logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = redis.Redis(host='redis', port=6379)
pubsub = r.pubsub()
pubsub.subscribe('position-keys')
r.ping()
logger.info("connected to redis succesfulyly")


def calculate_pnl(position):
    current_price = get_current_price(position.ticker)

    # Get the event loop
    loop = asyncio.get_event_loop()

    # Run the asynchronous function to calculate realized PnL
    realized_pnl = loop.run_until_complete(
        calculate_realized_pnl_all_time(position))

    loop = asyncio.get_event_loop()

    # Run the asynchronous function to calculate realized PnL
    realized_pnl_today = loop.run_until_complete(
        calculate_realized_pnl_today(position))

    # Calculate the unrealized PnL synchronously
    unrealized_pnl = calculate_unrealized_pnl_all_time(position, current_price)

    loop = asyncio.get_event_loop()

    unrealized_pnl_today = loop.run_until_complete(calculate_unrealized_pnl_today(position, current_price))

    loop = asyncio.get_event_loop()

    # Log the PnL values
    # logger.info(f"Current Price: {current_price}, Realized PnL: {realized_pnl}, Unrealized PnL: {unrealized_pnl}")

    # Prepare PnL measures
    pnl_measures = {
        'account': position.account_id,
        'ticker': position.ticker,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'unrealized_pnl_today': unrealized_pnl_today,
        'realized_pnl_today': realized_pnl_today,
        'total_pnl': realized_pnl + unrealized_pnl,
        'total_pnl_today': realized_pnl_today + unrealized_pnl_today,
        'last_updated': datetime.now().isoformat()
    }

    # Print and publish the PnL measures
    print(f"Calculated PnL measures: {pnl_measures}")
    r.publish('P_&_L', json.dumps(pnl_measures))


def get_current_price(ticker):
    return retrieve_price_data(r, ticker)


async def calculate_realized_pnl_all_time(position):
    spent = 0
    earned = 0
    trades = await get_trades_by_account_by_ticker(position.account_id, position.ticker)
    for trade in trades:
        if trade.direction == Direction.BUY:
            spent += trade.quantity * trade.executed_price
        else:
            earned += trade.quantity * trade.executed_price
    return earned - spent


def calculate_unrealized_pnl_all_time(position, current_price):
    unrealized_pnl = (current_price - position.avg_price) * position.quantity
    return unrealized_pnl


async def calculate_realized_pnl_today(position):
    today = datetime.now().date()
    spent = 0
    earned = 0
    trades = await get_trades_by_account_by_ticker(position.account_id, position.ticker)
    for trade in trades:
        if trade.executed_time.date() == today:
            if trade.direction == Direction.BUY:
                spent += trade.quantity * trade.executed_price
            else:
                earned += trade.quantity * trade.executed_price
    return earned - spent


async def calculate_unrealized_pnl_today(position, current_price):
    backend_url = get_backend_url()
    response = requests.get(f"http://main10:8010/prices/{position.ticker}")
    if response.status_code == 200:
        prices = response.json()
    logger.info(prices[0])
    return (current_price - prices[0]['price']) * position.quantity


def main():
    while True:
        try:
            for message in pubsub.listen():
                logger.info("gottem")
                if message['type'] == 'message':
                    position_key_data = message['data']
                    position_key_dict = json.loads(position_key_data)
                    position_key = PositionKey(**position_key_dict)
                    position = retrieve_position_data(
                        r, position_key.account_id, position_key.ticker)
                    calculate_pnl(position)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()