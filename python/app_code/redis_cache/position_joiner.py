import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pydantic import Field
from models.models import Position, PositionType
from datetime import datetime
from redis_cache.cache_database import retrieve_position_data
import redis
import json
import time
import asyncio

try:
    print("Connecting to Redis...")
    r = redis.Redis(host='redis', port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe('P_&_L','risk_calculation')
    print("Subscribed to channels")
except Exception as e:
    print(f"Error connecting to Redis: {e}")


def retrieve_position_full_data(r, key):
    position_full_data_json = r.get(key)
    position_full_data_dic = json.loads(position_full_data_json)

    return position_full_data_dic



async def handle_pnl_message(data):
    account_id = data['account']
    ticker = data['ticker']
    key = f"combine:{account_id}:{ticker}"

    # Store PnL data in Redis hash then delete it after 10 seconds
    r.hset(key, "pnl", json.dumps(data))
    r.expire(key, 10)
    
    # Check if both PnL and risk data are present
    if r.hexists(key, "risk"):
        await combine_and_process_data(account_id, ticker)

async def handle_risk_message(data):
    account_id = data['account']
    ticker = data['ticker']
    key = f"combine:{account_id}:{ticker}"
   

    # Store risk data in Redis hash then delete it after 10 seconds
    r.hset(key, "risk", json.dumps(data))
    r.expire(key, 10)
    print("Risk data stored")
    # Check if both PnL and risk data are present
    if r.hexists(key, "pnl"):
        
        await combine_and_process_data(account_id, ticker)

async def combine_and_process_data(account_id, ticker):
    key = f"combine:{account_id}:{ticker}"

    # Retrieve both PnL and risk data
    pnl_data = json.loads(r.hget(key, "pnl"))
    risk_data = json.loads(r.hget(key, "risk"))

    position_raw = retrieve_position_data(r, account_id, ticker)

    combined_data_dic = {
        'account': account_id,
        'ticker': ticker,

        'quantity': position_raw.quantity,
        'position type': position_raw.position_type,
        'avg price': position_raw.avg_price,


        'realized pnl': pnl_data['realized_pnl'],
        'unrealized pnl': pnl_data['unrealized_pnl'],
        'unrealized pnl today': pnl_data['unrealized_pnl_today'],
        'realized pnl today': pnl_data['realized_pnl_today'],
        'total pnl': pnl_data['total_pnl'],
        'total pnl today': pnl_data['total_pnl_today'],
        
        'standard deviation': risk_data['standard_deviation'],
        'sharpe ratio': risk_data['sharpe_ratio'],
        'alpha': risk_data['alpha'],
        'beta': risk_data['beta'],
        'r squared': risk_data['r_squared'],
        
        'last updated': datetime.now().isoformat()
        
    }
    
    print(f"Combined Data: {combined_data_dic}")
    
    r.delete(key)
    
    k = f"combined:{account_id}:{ticker}"
    r.set(k, json.dumps(combined_data_dic))
    r.publish('position_full_key', k)



async def messages(message):
    data = json.loads(message['data'])
    channel = message['channel'].decode()

    if channel == 'P_&_L':
        
        await handle_pnl_message(data)

    elif channel == 'risk_calculation':

        await handle_risk_message(data)

async def channels():
    while True:
        message = pubsub.get_message()
        
        if message and message['type'] == 'message':
            print(message)    
            await messages(message)
        await asyncio.sleep(0.01)

def main():
   print("Starting the position joiner...")
   asyncio.run(channels())

if __name__ == "__main__": 
    main()