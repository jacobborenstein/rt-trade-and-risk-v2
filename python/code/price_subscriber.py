import redis
import logging
import time
import streamlit as st
import pandas as pd
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ticker_list = open("s&p_500_tickers.txt").read().splitlines()
dic = {}
for t in ticker_list:
    dic.setdefault(t, 0)
df = pd.DataFrame(list(dic.items()), columns=['Tickers', 'Prices'])
master = st.container(height=17858)
containter = master.empty()
containter.table(df)
counter = 0
# Connect to Redis
while True:
    try:
        r = redis.Redis(host='localhost', port=6379)
        pubsub = r.pubsub()
        for t in ticker_list:
            pubsub.subscribe(t)
            logger.info("Subscribed to channel: " + t)
        logger.info("Waiting for messages...")
        for message in pubsub.listen():
            if message['type'] == 'message':
                dic[message['channel'].decode('utf-8')] = message['data'].decode('utf-8')
                logger.info("gotem")
                df = pd.DataFrame(list(dic.items()), columns=['Tickers', 'Prices'])
                counter += 1
                if counter > 500:
                    containter.empty()
                    containter.table(df)
                    counter = 0
     
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(5)  # Wait before retrying