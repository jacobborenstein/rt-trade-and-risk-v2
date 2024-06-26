import json
import time
from typing import List
from datetime import datetime
from models import Direction, Account, PrimaryKey, Trade, Position
import redis

accounts: List[Account] = []

def add_trade_to_account(account: Account, trade: Trade):
    """Function to add a trade to the account's trades list."""
    account.trades.append(trade)

def create_position(account: Account, ticker: str) -> Position:
    """Function to create/update the position for a given ticker."""
    trades = account.trades
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
    print(f"Creating position: account={account}, ticker={ticker}, quantity={quantity}, avg_price={avg_price}, last_updated={datetime.now()}")  # Debug print
    
    # Create a shallow copy of the account object without trades to avoid circular reference
    # will delete this after incorporating a mongoDB and removing trades[] from Account model
    account_copy = account.model_copy()
    account_copy.trades = []
    
    return Position(
        account=account_copy,
        ticker=ticker,
        quantity=quantity,
        avgPrice=avg_price,
        lastUpdated=datetime.now()
    )

def main():
    r = redis.Redis(host='localhost', port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe('trades')
    while True:
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    trade_data = message['data']
                    print(f"Received trade data: {trade_data}")
                    trade_dict = json.loads(trade_data)
                    print(f"Parsed trade dictionary: {trade_dict}")

                    # Create the Trade object directly using the parsed dictionary
                    trade = Trade.model_validate(trade_dict)

                    account = next((acc for acc in accounts if acc.get_account_id() == trade.primaryKey.account.get_account_id()), None)
                    if account is None:
                        accounts.append(trade.primaryKey.account)
                        account = trade.primaryKey.account

                    add_trade_to_account(account, trade)
                    position = create_position(account, trade.ticker)

                    print(f"Position object: {position}")  # Debug print

                    # Convert Position to a dictionary and adjust field names for Redis
                    position_dict = position.model_dump(by_alias=True)
                    
                    # Convert datetime to string
                    position_dict['lastUpdated'] = position_dict['lastUpdated'].isoformat()
                    print(f"Position dictionary: {position_dict}")  # Debug print

                    r.publish('positions', json.dumps(position_dict))
                    print(f"Processed trade: {trade}")
                    print(f"Updated position: {position}")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
