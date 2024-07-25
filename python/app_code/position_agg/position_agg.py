import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from typing import List
from datetime import datetime
from models.models import Direction, Account, PrimaryKey, Trade, Position
import redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_position(account_id: str, ticker: str, trades: List[Trade]) -> Position:
    quantity = 0
    total_price = 0.0
    for trade in trades:
        if trade.ticker == ticker:
            if trade.direction == Direction.BUY:
                quantity += trade.quantity
                total_price += trade.quantity * trade.executed_price
            elif trade.direction == Direction.SELL:
                quantity -= trade.quantity
                total_price -= trade.quantity * trade.executed_price
    avg_price = round(total_price / quantity, 2) if quantity != 0 else 0.0
    position_type = "LONG" if quantity > 0 else "SHORT"
    return Position(
        accountId=account_id,
        ticker=ticker,
        quantity=quantity,
        positionType=position_type,
        avgPrice=avg_price,
        lastUpdated=datetime.now()
    )
    

def main():
    r = redis.Redis(host='redis', port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe('trade-collection-from-mongo')
    while True:
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    trades_data = json.loads(message['data'])
                    trades = [Trade(**trade_dict) for trade_dict in trades_data]

                    if trades:
                        logger.info(f"1) Received trades: {trades}")
                        account_id = trades[0].primaryKey.account_id
                        ticker = trades[0].ticker
                        trade = max(trades, key=lambda t: t.executed_time)
                        position = create_position(account_id, ticker, trades)
                        logger.info(f"2) Created position: {position}")
                        trade.executed_time = trade.executed_time.isoformat()
                        # send most recent trade to redis cache
                        r.publish('trades-from-position_agg', json.dumps(trade.model_dump(by_alias=True)))

                    position_data = position.model_dump(by_alias=True)
                    position_data['lastUpdated'] = position_data['lastUpdated'].isoformat()
                    r.publish('positions', json.dumps(position_data))
                    logger.info(f"3) Updated position: {position}")
        except Exception as e:
            logger.info(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()