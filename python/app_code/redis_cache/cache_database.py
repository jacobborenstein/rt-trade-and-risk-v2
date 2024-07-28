
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.models import Position, Trade, PrimaryKey, Account
from pydantic import BaseModel, Field
import redis
import json
import time
from datetime import datetime




class PositionKey(BaseModel):
    account_id: str 
    ticker: str       

def cache_price_data(redis_server, ticker: str, price: float):
    #cache the price data in redis 

    #convert back into Json to stor in redis
    price_data_json = json.dumps(price)
    
    #Store it in redis under 'price' with the key.(to retrieve the data use .get('price:<ticker>'). exp: .get('price:APPL) 
    redis_server.set (f"price:{ticker}", price_data_json)

def retrieve_price_data(redis_server, ticker):
    price = None
    try:
        price_data_json = redis_server.get(f"price:{ticker}")
        if price_data_json:
            price = json.loads(price_data_json)
            if not isinstance(price, (int, float)):
                price = 0
        else:
            price = 0 
    except Exception as e:
        price = 0 
    return price

def cache_trade_data(redis_server, trade: Trade):
    trade_data_json = json.dumps(trade.to_json())
    primary_key_trade_id = trade.primaryKey.trade_id
    account_id = trade.primaryKey.account_id
    redis_server.set(f"trade:{primary_key_trade_id}", trade_data_json)
    redis_server.rpush(f"account:{account_id}:trades", primary_key_trade_id)

def retrieve_trade_data(redis_server, primary_key):
    trade_data_json = redis_server.get(f"trade:{primary_key}")
    if trade_data_json:
        trade_dict = json.loads(trade_data_json)
        return Trade(**trade_dict)
    return None


#method to cache the position data in redis DB
def cache_position_data(redis_server, position: Position):
    #cache the position data in redis 

    #convert back into Json to stor in redis
    position_data_json = json.dumps(position.to_json())
    
    #unique key for each position. accountID + ticker
    account_id = position.account_id 
    ticker = position.ticker

    #Store it in redis under 'position' with the key.(to retrieve the data use .get('position:<account_id>:<ticker>'). exp: .get('position:12345:APPL) 
    redis_server.set (f"position:{account_id}:{ticker}", position_data_json)


#method to retrieve the cached position data from redisDB
def retrieve_position_data(redis_server, account_id, ticker):

    #method to retrieve the cached position data from redis
    position_data_json = redis_server.get(f"position:{account_id}:{ticker}")
    
    #if data is found, parse it back into a dictionary
    if position_data_json:
        position_dict = json.loads(position_data_json)

    #return the position object
    return Position(**position_dict)





def main():
    
    #set up redis and susbsribe to 'positions' channel to get postions data
    try:
        print("Connecting to Redis...")
        r = redis.Redis(host='redis', port=6379)
        pubsub = r.pubsub()
        pubsub.subscribe('positions','trades-from-mongo','prices_and_values')
        print("Subscribed to channels")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return
   

    #create an infinte loop to constanlty listen for new messages
    while True:
        try: 
            for message in pubsub.listen():
                
                if message['type'] == 'message':
                    
                    #create a variable to see which channel the message is coming from
                    channel = message['channel'].decode()
                    
                    #if the channel is 'positions', do the necessary actions
                    if channel == 'positions':
                        
                        #get ths position data from the message as a Json string
                        position_data = message['data']
                        print(f"Received position data: {position_data}")
                        
                        #parse the Json string into a python dictionary          
                        position_dict = json.loads(position_data)
                        print(f"Parsed position dictionary: {position_dict}")

                        # Create the Position object directly using the parsed dictionary                 
                        position =  Position(**position_dict)
                        print(f"Created position: {position}")

                        #add to redis data base 
                        cache_position_data(r, position)

                        #have to publish the key to the 'position-keys' channel
                        r.publish('position-keys', json.dumps(PositionKey(account_id = position.account_id, ticker = position.ticker).model_dump(by_alias=True)))


                    #if the channel is 'trades', do the necessary actions
                    elif channel == 'trades-from-mongo':
                            
                        trade_data = message['data']
                        trade_list = json.loads(trade_data)
                        
                        for trade_dict in trade_list:
                            trade_dict['executedTime'] = datetime.fromisoformat(trade_dict['executedTime'])
                            trade = Trade(**trade_dict)
                            cache_trade_data(r, trade)
                            r.publish('trade-keys', json.dumps(trade.primaryKey.trade_id))



                    #if the channel is 'prices_and_values', do the necessary actions
                    elif channel == 'prices_and_values':
                            
                            #get the price data from the message as a Json string
                            price_data = message['data']
                            print(f"Received price data: {price_data}")
                            
                            #parse the Json string into a python dictionary          
                            price_dict = json.loads(price_data)
                            print(f"Parsed price dictionary: {price_dict}")
    
                            #cache the price data in redis 
                            cache_price_data(r, price_dict['ticker'], price_dict['price'])
    
                            #publish the key to the 'price-keys' channel
                            r.publish('price-keys', json.dumps(price_dict['ticker']))
                        
                    
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

