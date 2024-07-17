import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from turtle import pos
from click import get_current_context
from app_code.redis_cache.cache_database import retrieve_position_data, PositionKey
from app_code.mongo.crud import get_trades_by_account_by_ticker
import redis
import json
import time
from datetime import datetime
from python.app_code.models.models import Direction
from python.app_code.mongo import crud


class PnLService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.r = redis.Redis(host=redis_host, port=6379)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe('position-keys')
        #self.pubsub.subscribe('prices_and_values')

    def run(self):
        while True:
            try:
                for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        position_key_data = message['data']
                        position_key_dict = json.loads(position_key_data)
                        position_key = PositionKey(**position_key_dict)
                        position = retrieve_position_data(self.r, position_key.account_id, position_key.ticker)
                        self.calculate_pnl(position)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def calculate_pnl(self, position):
        current_price = self.get_current_price(position.ticker)
        realized_pnl = self.calculate_realized_pnl_all_time(position)
        unrealized_pnl = self.calculate_unrealized_pnl_all_time(position, current_price)

        pnl_measures = {
            'account': position.account_id,
            'ticker': position.ticker,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': realized_pnl + unrealized_pnl,
            'last_updated': datetime.now().isoformat()
        }

        print(f"Calculated PnL measures: {pnl_measures}")
        self.r.publish('P_&_L', json.dumps(pnl_measures))
        # Optionally, publish or store the PnL measures
    #returns the current price of the ticker
    def get_current_price(self, ticker):
        price = 0
        for message in self.pubsub.listen():
             if message['type'] == 'message':
                        price_data = message['data']
                        price_data_dict = json.loads(price_data)
                        if price_data_dict['ticker'] is not None and price_data_dict['ticker'] == ticker:
                             price = price_data_dict['price']
                             return price
        return price

    def calculate_realized_pnl_all_time(self, position):
        # Implement a method to calculate realized PnL
        # Realized PnL typically involves summing the profits/losses of closed trades
        #total trades * (sell - buy)
        spent = 0
        earned = 0
        trades = crud.get_trades_by_account_by_ticker(position.accountID, position.ticker)
        for trade in trades:
            if trade.direction == Direction.BUY:
                spent += trade.quantity * trade.executed_price
            else:
                 earned += trade.quantity * trade.executed_price
        return earned - spent  

    def calculate_unrealized_pnl_all_time(self, position, current_price):
        # Unrealized PnL = (Current Price - Average Price) * Quantity
        unrealized_pnl = (current_price - position.avg_price) * position.quantity
        return unrealized_pnl
    
    def calculate_realized_pnl_today(self, position):
        today = datetime.now().date()
        spent = 0
        earned = 0
        trades = crud.get_trades_by_account_by_ticker(position.account_id, position.ticker)
        for trade in trades:
            if trade.executed_time.date() == today:
                if trade.direction == Direction.BUY:
                    spent += trade.quantity * trade.executed_price
                else:
                    earned += trade.quantity * trade.executed_price
        return earned - spent
    
    def calculate_unrealized_pnl_today(self, position, current_price):
        price_day_start = 0


         

if __name__ == "__main__":
    pnl_service = PnLService()
    pnl_service.run()
