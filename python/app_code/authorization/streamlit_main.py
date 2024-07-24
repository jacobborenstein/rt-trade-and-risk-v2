import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import requests
import pandas as pd
import re
import redis
import json
import time 
from datetime import timedelta
from pydantic import BaseModel
import logging
from app_code.models.models import Position

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


st.set_page_config(page_title="Trading Dashboard", page_icon=":chart_with_upwards_trend:", layout="wide")

refresh_rate = 10

backend_url = "http://localhost:8000"

#class Position(BaseModel):
 #   accountId: str = Field(..., alias="accountId")
  #  ticker: str
   # quantity: int
    #position_type: PositionType = Field(..., alias="positionType")
    #avg_price: float = Field(..., alias="avgPrice")
    #last_updated: datetime = Field(..., alias="lastUpdated")



# Homepage
def homepage():
    st.title("Trading System")
    st.write("Welcome to the Trading System")

    if st.button("Login"):
        st.session_state["page"] = "login"
        st.experimental_rerun()
    if st.button("Sign Up"):
        st.session_state["page"] = "signup"
        st.experimental_rerun()

# Signup Page
def signup():
    st.title("Sign Up")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    full_name = st.text_input("Full Name")

    if st.button("Sign Up"):
        if username and email and full_name and password:
            response = requests.post(f"{backend_url}/users/new", json={
                "username": username,
                "email": email,
                "full_name": full_name,
                "password": password
            })
            if response.status_code == 200:
                st.success("User created successfully!")
                st.session_state["page"] = "login"
                st.experimental_rerun()
            elif response.status_code == 400:
                st.error("Username already exists")
            else:
                st.error("Error creating user")
    if st.button("Back"):
        st.session_state["page"] = "home"
        st.experimental_rerun()

# Login Page
def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username and password:
            response = requests.post(f"{backend_url}/token", data={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                st.success("Login successful!")
                st.session_state["token"] = response.json()["access_token"]
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "dashboard"
                st.experimental_rerun()
            elif response.status_code == 401:
                st.error("Incorrect username or password")
            else:
                st.error("Error logging in")
    if st.button("Back"):
        st.session_state["page"] = "home"
        st.experimental_rerun()

# Fetch Account IDs
def fetch_account_ids():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.get(f"{backend_url}/users/accountIds", headers=headers)
        response.raise_for_status()
        accounts = response.json()
        return accounts["can_write"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching account IDs: {e}")
        return []
    
def get_accounts():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.get(f"{backend_url}/users/accounts", headers=headers)
        response.raise_for_status()
        accounts = response.json()
        return accounts
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching accounts: {e}")
        return []

    
# Retrieve Position Data
def retrieve_position_data(redis_server, account_id, ticker):
    position_data_json = redis_server.get(f"position:{account_id}:{ticker}")
    if position_data_json:
        position_dict = json.loads(position_data_json)
        # Ensure all required fields are present
        required_fields = ["accountId", "ticker", "quantity", "positionType", "avgPrice", "lastUpdated"]
        for field in required_fields:
            if field not in position_dict:
                raise ValueError(f"Missing field {field} in position data")
        return position_dict
    return None

# Retrieve Price Data
def retrieve_price_data(redis_server, ticker):
    price_data_json = redis_server.get(f"price:{ticker}")
    if price_data_json:
        return json.loads(price_data_json)
    return None

# Read Tickers from File
def read_tickers_from_file():
    tickers_path = '/app/python/tickers.txt'
    tickers_path_development = 'python/tickers.txt'
    try:
        with open(tickers_path_development, 'r') as file:
            tickers = file.read().splitlines()
        return tickers
    except Exception as e:
        st.error(f"Error reading tickers from file: {e}")
        return []

# Get Redis Connection
def get_redis_connection():
    try:
        r = redis.Redis(host='localhost', port=6379)
        return r
    except Exception as e:
        st.error(f"Error connecting to Redis: {e}")
        return None

# Fetch All Positions and Prices
import pandas as pd

def fetch_all_positions_and_prices(redis_server, account_id, tickers):
    positions = []
    for ticker in tickers:
        position_dict = retrieve_position_data(redis_server, account_id, ticker)
        if position_dict:
            try:
                # Convert lastUpdated to datetime
                position_dict['lastUpdated'] = pd.to_datetime(position_dict['lastUpdated'])
                # Create Position instance aka the problem child
                position = Position(**position_dict)
                # Retrieve current price data
                price = retrieve_price_data(redis_server, ticker)
                
                # Prepare position data for DataFrame
                position_data = position.model_dump()
                position_data['current_price'] = price if price else "N/A"
                positions.append(position_data)
            except ValueError as e:
                logger.error(f"Error creating Position: {e}")
        else:
            logger.error(f"No position data found for ticker: {ticker}")
    
    return pd.DataFrame(positions)

# Display Table of Trade Data
@st.experimental_fragment(run_every=timedelta(seconds=refresh_rate))
def trade_view():
    st.header("Trade View")
    redis_server = get_redis_connection()
    trade_data = []
    tickers = read_tickers_from_file()
    for i, ticker in enumerate(tickers):
        trade_data.append({"Trade ID": i+1, "Symbol": ticker, "Quantity": 1, "Price": retrieve_price_data(redis_server, ticker)})
    trade_df = pd.DataFrame(trade_data)
    st.dataframe(trade_df)

# Display Table of Position Data
@st.experimental_fragment(run_every=timedelta(seconds=refresh_rate))
def position_view():
    st.header("Position View")
    account_ids = fetch_account_ids()
    if account_ids:
        account_id = st.selectbox("Select Account ID", account_ids, key="position_view_account_id")
        redis_server = get_redis_connection()
        if redis_server:
            tickers = read_tickers_from_file()
            logger.info(tickers)
            if tickers:
                position_df = fetch_all_positions_and_prices(redis_server, account_id, tickers)
                st.dataframe(position_df.drop(columns=['last_updated']))
            else:
                st.error("No tickers available.")
        else:
            st.error("Unable to connect to Redis.")
    else:
        st.error("No account IDs available.")



# Trading Dashboard
def trading_dashboard():
    st.title("Trading Dashboard")
    
    st.sidebar.title("Trading Dashboard Settings")
    refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)
    
    tabs = st.tabs(["Trade View", "Position View", "Bulk Booking", "Single Trade", "Account Manager", "PNL", "Risk"])

    with tabs[0]:
        trade_view()

    with tabs[1]:
        position_view()

    with tabs[2]:

        st.header("Bulk Booking")
        account_ids = fetch_account_ids()
        if account_ids:
            st.session_state.pop("accounts", None)
            accounts = get_accounts()
            account_names = [account["account_name"] for account in accounts if account]
            account_name = st.selectbox("Account", account_names, key="multi_trade_account_id")
            
            tickers_path = '/app/python/tickers.txt'
            tickers_path_dev = 'python/tickers.txt'
            try:
                with open(tickers_path_dev, 'r') as file:
                    tickers = file.read().splitlines()
            except Exception as e:
                st.error(f"Error reading tickers from file: {e}")

            if "multi_trade_data" not in st.session_state:
                st.session_state.multi_trade_data = []

            def add_booking():
                st.session_state.multi_trade_data.append({"ticker": "", "quantity": 1, "direction": "BUY"})

            def update_trade(index, key, value):
                st.session_state.multi_trade_data[index][key] = value

            if st.button("Add Booking"):
                add_booking()

            for i, trade in enumerate(st.session_state.multi_trade_data):
                ticker = st.selectbox("Ticker", tickers, key=f"multi_trade_ticker_{i}", index=0 if trade["ticker"] == "" else tickers.index(trade["ticker"]))
                quantity = st.number_input("Quantity", min_value=1, step=1, key=f"multi_trade_quantity_{i}", value=trade["quantity"])
                direction = st.selectbox("Direction", ["BUY", "SELL"], key=f"multi_trade_direction_{i}", index=0 if trade["direction"] == "BUY" else 1)
                
                update_trade(i, "ticker", ticker)
                update_trade(i, "quantity", quantity)
                update_trade(i, "direction", direction)

            bulk_input = st.text_area("Or enter all trades in the following format: IMB, 1000, B. MSFT, 2000, S. AMZN, 300, S.")
            
            def parse_bulk_input(bulk_input):
                # Regular expression to parse input
                trade_pattern = re.compile(r'(\w+),\s*(\d+),\s*([BS])')
                trades = trade_pattern.findall(bulk_input)
                return [{"ticker": t[0], "quantity": int(t[1]), "direction": "BUY" if t[2] == "B" else "SELL"} for t in trades]

            if st.button("Submit All Trades"):
                if account_name:
                    selected_account = next(account for account in accounts if account and account["account_name"] == account_name)
                    account_id = selected_account["account_id"]
                    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                    
                    all_trades_successful = True
                    trades_to_submit = st.session_state.multi_trade_data
                    
                    if bulk_input:
                        trades_to_submit += parse_bulk_input(bulk_input)

                    # Validate trades
                    invalid_tickers = [trade["ticker"] for trade in trades_to_submit if trade["ticker"] not in tickers]
                    if invalid_tickers:
                        st.error(f"Invalid tickers found: {', '.join(invalid_tickers)}")
                        all_trades_successful = False

                    if all_trades_successful:
                        for trade in trades_to_submit:
                            response = requests.post(f"{backend_url}/publish/trade", json={
                                "account_id": account_id,
                                "ticker": trade["ticker"],
                                "quantity": trade["quantity"],
                                "direction": trade["direction"]
                            }, headers=headers)

                            if response.status_code != 200:
                                all_trades_successful = False
                                st.error(f"Error submitting trade for {trade['ticker']}: {response.text}")
                                break

                    if all_trades_successful:
                        st.success("All trades submitted successfully!")
                        st.session_state.multi_trade_data = []
                    else:
                        st.error("One or more trades failed to submit.")
                    
                    time.sleep(5)
                    st.experimental_rerun()
        else:
            st.error("User has no accounts")

    with tabs[3]:
        st.header("Single trade")

        account_ids = fetch_account_ids()
        if account_ids:
            st.session_state.pop("accounts", None)
        
            accounts = get_accounts()
            account_names = [account["account_name"] for account in accounts if account]
            account_name = st.selectbox("Account", account_names, key="single_trade_account_id")
            
            tickers_path = '/app/python/tickers.txt'
            # tickers_path_development = '/app/python/tickers.txt'

            try:
                with open(tickers_path_dev, 'r') as file:
                    tickers = file.read().splitlines()
            except Exception as e:
                st.error(f"Error reading tickers from file: {e}")
            
            ticker = st.selectbox("Ticker", tickers, key="single_trade_ticker")
            quantity = st.number_input("Quantity", min_value=1, step=1, key="single_trade_quantity")
            direction = st.selectbox("Direction", ["BUY", "SELL"], key="single_trade_direction")
            current_price = retrieve_price_data(get_redis_connection(), ticker)
            if st.button(f"Book: ${current_price * quantity:.2f}", key="single_trade_submit"):
                if account_name and ticker and quantity:
                    selected_account = next(account for account in accounts if account and account["account_name"] == account_name)
                    account_id = selected_account["account_id"]
                    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                    response = requests.post(f"{backend_url}/publish/trade", json={
                    "account_id": account_id,
                    "ticker": ticker,
                    "quantity": quantity,
                    "direction": direction
                    }, headers=headers)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        total_price = response_data.get('total_price', 'Unknown')
                        st.success(f"Trade submitted successfully! Total price: ${total_price:.2f}")                   
                    elif response.status_code == 401:
                        st.error("User cannot create trades for this account")
                    else:
                        st.error(f"Error submitting trade: {response.text}")

                    time.sleep(5)
                    st.experimental_rerun()
        else:
            st.error("User has no accounts")
    
    with tabs[4]:
        st.header("Account Manager")
        st.write("account manager")

        account_name = st.text_input("Account Name", key="create_account_account_name")
        if st.button("Create Account", key="create_account_button"):
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            response = requests.post(f"{backend_url}/publish/account/new", json={
                "account_name": account_name
            }, headers=headers)
            if response.status_code == 200:
                st.success("Account created successfully!")
                # Force a reload of accounts in session state
                st.session_state.pop("accounts", None)
                st.experimental_rerun()
            else:
                st.error("Error creating account")
                st.experimental_rerun()
        if st.button("Logout"):
            st.session_state["token"] = None
            st.experimental_rerun()

# Main Function
def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    if "token" not in st.session_state:
        st.session_state["token"] = None

    if st.session_state["token"] is None:
        if st.session_state["page"] == "signup":
            signup()
        elif st.session_state["page"] == "login":
            login()
        else:
            homepage()
    else:
        trading_dashboard()

if __name__ == "__main__":
    main()
