from email.errors import MultipartInvariantViolationDefect
import redis
import logging
import time
import streamlit as st
import pandas as pd
import json
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dic = {"foo":{"bar":"bar", "barry":"barry"}}
df = pd.DataFrame.from_dict((dic), orient='index')
master = st.container(height=17858)
containter = master.empty()
containter.table(df)
while True:
    try:
        r = redis.Redis(host='localhost', port=6379)
        pubsub = r.pubsub()
        r.ping()
        pubsub.subscribe("prices_and_values")
        logger.info("Subscribed to channel: prices_and_values")
        logger.info("Waiting for messages...")
        for message in pubsub.listen():
            logger.info(1)
            if message['type'] == 'message':
                logger.info(2)
                dic = json.loads(message['data'])
                logger.info(dic["NVDA"])
                logger.info("gotem")
                df = pd.DataFrame.from_dict((dic), orient='index')
                containter.empty()
                containter.table(df)
     
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(5)  # Wait before retrying

    