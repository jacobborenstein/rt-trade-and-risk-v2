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
to_track = st.text_input("What ticker(s) would you like to track? (seperate with spaces)").split(" ")
master = st.container(height=17858)
containter = master.empty()
containter.table(df)
while True:
    try:
        r = redis.Redis(host='redis', port=6379)
        pubsub = r.pubsub()
        r.ping()
        pubsub.subscribe("prices_and_values")
        logger.info("Subscribed to channel: prices_and_values")
        logger.info("Waiting for messages...")
        if r.get("latest_time") is not None and r.get(r.get("latest_time")) is not None:
            snapshot = {}
            full_snap = json.loads(r.get(r.get("latest_time")))
            for t in to_track:
                    snapshot[t] = dict(full_snap).get(t)
            df = pd.DataFrame.from_dict(snapshot, orient='index')
            containter.empty()
            containter.table(df)
        for message in pubsub.listen():
            logger.info(1)
            if message['type'] == 'message':
                logger.info(2)
                dic_json = message['data']
                full_dic = json.loads(dic_json)
                latest = time.time()
                r.set("latest_time", latest)
                r.set(latest, dic_json)
                dic = {}
                logger.info("gotem")
                for t in to_track:
                    dic[t] = dict(full_dic).get(t)
                df = pd.DataFrame.from_dict((dic), orient='index')
                containter.empty()
                containter.table(df)
     
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(5)  # Wait before retrying

    