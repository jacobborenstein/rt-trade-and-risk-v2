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

def add_trade_to_account(account: Account, trade: Trade):
    """Function to add a trade to the account's trades list."""
    account.trades.append(trade)

def create_position(account: Account, ticker: str, trades: List[Trade]) -> Position:
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
    avg_price = total_price / quantity if quantity != 0 else 0.0
    position_type = "LONG" if quantity > 0 else "SHORT"  
    return Position(
        account=account,
        ticker=ticker,
        quantity=quantity,
        positionType=position_type,
        avgPrice=avg_price,
        lastUpdated=datetime.now()
    )

def main():
    r = redis.Redis(host='localhost', port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe('trades-from-mongo')
    while True:
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    trade_data = json.loads(message['data'])
                    logger.info(f"1) Received trade data: {trade_data}")
                    
                    account_dict = trade_data['primaryKey']['account']
                    account = Account(accountId=account_dict['accountId'], accountName=account_dict['accountName'])
                    primary_key = PrimaryKey(account=account, tradeId=trade_data['primaryKey']['tradeId'])
                    
                    trade = Trade(
                        primaryKey=primary_key,
                        ticker=trade_data['ticker'],
                        direction=Direction(trade_data['direction']),
                        quantity=trade_data['quantity'],
                        executedPrice=trade_data['executedPrice'],
                        executedUser=trade_data['executedUser'],
                        executedTime=datetime.fromisoformat(trade_data['executedTime'])
                    )
                    logger.info(f"2) Processed trade: {trade}")

                    trades = [trade]
                    position = create_position(account, trade.ticker, trades)
                    logger.info(f"3) Created position: {position}")
                
                    position_data = position.model_dump(by_alias=True)
                    position_data['lastUpdated'] = position_data['lastUpdated'].isoformat()
                    r.publish('positions', json.dumps(position_data))
                    logger.info(f"4) Updated position: {position}")
        except Exception as e:
            logger.info(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
