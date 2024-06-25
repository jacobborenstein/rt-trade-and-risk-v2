from typing import List
import time
import pydantic, datetime
from models import Direction, Account, primaryKey, Trade, Position
import redis


accounts: List['Account'] = []

def create_position(account: Account, ticker: str):
    # gets all the trades from this account
    trades = account.trades
    quantity = 0
    avg_price = 0
    for trade in trades:
        # calculate current position for this ticker
        if trade.ticker == ticker:
            if trade.direction == Direction.BUY:
                quantity += trade.quantity
                avg_price += trade.executed_price
            elif trade.direction == Direction.SELL:
                quantity -= trade.quantity
                avg_price -= trade.executed_price
    return Position(account=account, ticker=ticker, quantity=quantity, avg_price=avg_price/quantity, last_updated=datetime.now())

while True:
    try:
        r = redis.Redis(host='localhost', port=6379)
        pubsub = r.pubsub()
        # listen to trades channel
        pubsub.subscribe('trades')
        for message in pubsub.listen():
            if message['type'] == 'message':
                # convert json message to Trade object
                trade = Trade.model_validate_json(message['data'])
                account = accounts.get(trade.primaryKey.account.account_id)
                if account is None:
                    accounts.append(trade.primaryKey.account)
                position = create_position(account, trade.ticker)
                r.publish('positions', position.model_dump_json())
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)  # Wait before retrying
                