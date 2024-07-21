import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import requests
import pandas as pd
import redis
import json
from pydantic import BaseModel
from datetime import timedelta
from app_code.mongo.crud import get_account

backend_url = "http://main:8000"

class Position(BaseModel):
    account: dict
    ticker: str
    quantity: int
    average_price: float

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
        st.write(f"Accounts: {accounts}")
        return accounts
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching accounts: {e}")
        return []

    
# Retrieve Position Data
def retrieve_position_data(redis_server, account_id, ticker):
    position_data_json = redis_server.get(f"position:{account_id}:{ticker}")
    if position_data_json:
        position_dict = json.loads(position_data_json)
        return Position(**position_dict)
    return None

# Retrieve Price Data
def retrieve_price_data(redis_server, ticker):
    price_data_json = redis_server.get(f"price:{ticker}")
    if price_data_json:
        return json.loads(price_data_json)
    return None

# Read Tickers from File
def read_tickers_from_file():
    try:
        with open('tickers.txt', 'r') as file:
            tickers = file.read().splitlines()
        return tickers
    except Exception as e:
        st.error(f"Error reading tickers from file: {e}")
        return []

# Get Redis Connection
def get_redis_connection():
    try:
        r = redis.Redis(host='redis', port=6379)
        return r
    except Exception as e:
        st.error(f"Error connecting to Redis: {e}")
        return None

# Fetch All Positions and Prices
def fetch_all_positions_and_prices(redis_server, account_id, tickers):
    positions = []
    for ticker in tickers:
        position = retrieve_position_data(redis_server, account_id, ticker)
        price = retrieve_price_data(redis_server, ticker)
        if position:
            position_data = position.dict()
            position_data['current_price'] = price if price else "N/A"
            positions.append(position_data)
    return pd.DataFrame(positions)


# Trading Dashboard
def trading_dashboard():
    st.title("Trading Dashboard")

    tabs = st.tabs(["Trade View", "Position View", "Bulk Booking", "Single Trade", "Account Manager"])

    with tabs[0]:
        st.header("Trade View")
        trade_data = [
            {"Trade ID": 1, "Symbol": "AAPL", "Quantity": 10, "Price": 150},
            {"Trade ID": 2, "Symbol": "GOOGL", "Quantity": 15, "Price": 1200},
            {"Trade ID": 3, "Symbol": "MSFT", "Quantity": 20, "Price": 210}
        ]
        trade_df = pd.DataFrame(trade_data)
        st.dataframe(trade_df)

    with tabs[1]:
        st.header("Position View")
        account_ids = fetch_account_ids()
        if account_ids:
            account_id = st.selectbox("Select Account ID", account_ids, key="position_view_account_id")
            redis_server = get_redis_connection()
            if redis_server:
                tickers = read_tickers_from_file()
                if tickers:
                    position_df = fetch_all_positions_and_prices(redis_server, account_id, tickers)
                    st.dataframe(position_df)
                else:
                    st.error("No tickers available.")
            else:
                st.error("Unable to connect to Redis.")
        else:
            st.error("No account IDs available.")

    with tabs[2]:
        st.header("Bulk Booking Parameters")
        bulk_booking_data = [
            {"Parameter": "Param1", "Value": "Value1"},
            {"Parameter": "Param2", "Value": "Value2"},
            {"Parameter": "Param3", "Value": "Value3"}
        ]
        bulk_booking_df = pd.DataFrame(bulk_booking_data)
        st.dataframe(bulk_booking_df)

        st.subheader("Execute Bulk Booking")
        param1 = st.selectbox("Parameter 1", ["Option 1", "Option 2", "Option 3"], key="bulk_booking_param1")
        param2 = st.selectbox("Parameter 2", ["Option A", "Option B", "Option C"], key="bulk_booking_param2")
        param3 = st.selectbox("Parameter 3", ["Value X", "Value Y", "Value Z"], key="bulk_booking_param3")

        account_ids = fetch_account_ids()
        if account_ids:
            account_id = st.selectbox("Account ID", account_ids, key="bulk_booking_account_id")
            ticker = st.text_input("Ticker", key="bulk_booking_ticker")
            quantity = st.number_input("Quantity", min_value=1, step=1, key="bulk_booking_quantity")
            direction = st.selectbox("Direction", ["BUY", "SELL"], key="bulk_booking_direction")

            if st.button("Book", key="bulk_booking_book"):
                trade_request = {
                    "account_id": account_id,
                    "ticker": ticker,
                    "quantity": quantity,
                    "direction": direction
                }

                response = requests.post(f"{backend_url}/publish/trade", json=trade_request)
                
                if response.status_code == 200:
                    st.success("Bulk booking executed successfully!")
                else:
                    st.error(f"Failed to execute bulk booking: {response.text}")
                st.experimental_rerun()
        else:
            st.error("No account IDs available.")

    with tabs[3]:
        st.header("Single trade")

        account_ids = fetch_account_ids()
        if account_ids:
            accounts = get_accounts()
            account_names = []
            for account in accounts:
                if account:
                    account_names.append(account["account_name"])
            account_name = st.selectbox("Account", account_names, key="single_trade_account_id")
            ticker = st.text_input("Ticker", key="single_trade_ticker")
            quantity = st.number_input("Quantity", min_value=1, step=1, key="single_trade_quantity")
            direction = st.selectbox("Direction", ["BUY", "SELL"], key="single_trade_direction")

            if st.button("Book", key="single_trade_submit"):
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
                        st.success("Trade submitted successfully!")
                    elif response.status_code == 401:
                        st.error("User cannot create trades for this account")
                    else:
                        st.error(f"Error submitting trade")
                        st.experimental_rerun()
        else:
            st.error("No account IDs available.")
    
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
                st.experimental_rerun()
            else:
                st.error("Error creating account")
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
