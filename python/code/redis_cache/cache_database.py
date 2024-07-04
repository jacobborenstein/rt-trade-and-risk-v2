
import sys
sys.path.append('/Users/jacobborenstein/Documents/YuCs/Github/rt-trade-and-risk-v2/python/code')
from models.models import Position
from pydantic import BaseModel, Field
import redis
import json

import time




class PositionKey(BaseModel):
    account_id: str 
    ticker: str       

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
        r = redis.Redis(host='localhost', port=6379)
        pubsub = r.pubsub()
        pubsub.subscribe('positions')
        print("Subscribed to 'positions' channel")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return
   

    #create an infinte loop to constanlty listen for new messages
    while True:
        try: 
            for message in pubsub.listen():
                
                if message['type'] == 'message':
                    
                    #extract the position data from the message as a Json string
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

                    #have to publish the key to the channel
                
                    r.publish('position-keys', json.dumps(PositionKey(account_id = position.account_id, ticker = position.ticker).model_dump(by_alias=True)))



        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

