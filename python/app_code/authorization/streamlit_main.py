import os
import sys
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
from app_code.models.models import Trade, Position
from app_code.redis_cache.cache_database import retrieve_trade_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state variables
if 'token' not in st.session_state:
    st.session_state['token'] = None

if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

st.set_page_config(page_title="Trading Dashboard", page_icon=":chart_with_upwards_trend:", layout="wide")

refresh_rate = 10


# round robin load balancing function
def get_backend_url():
    urls = [
        "http://main0:8000",
        "http://main1:8001",
        "http://main2:8002",
        "http://main3:8003",
        "http://main4:8004",
        "http://main5:8005",
        "http://main6:8006",
        "http://main7:8007",
        "http://main8:8008",
        "http://main9:8009",
    ]
    return urls[int(time.time()) % len(urls)]
# backend_url = "http://18.214.165.102/backend"
# backend_url = "http://localhost:8000"


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
            logger.info(f"Attempting to create user: {username}")
            response = requests.post(f"{get_backend_url()}/users/new", json={
                "username": username,
                "email": email,
                "full_name": full_name,
                "password": password
            })
            logger.info(f"Response from server: {response.status_code} - {response.text}")
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
            logger.info(f"Attempting to login user: {username}")
            response = requests.post(f"{get_backend_url()}/token", data={
                "username": username,
                "password": password
            })
            logger.info(f"Response from server: {response.status_code} - {response.text}")
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
    max_retries = 3
    retries = 0
    success = False
    while retries < max_retries and not success:
        try:
            response = requests.get(f"{get_backend_url()}/users/accountIds", headers=headers)
            response.raise_for_status()
            accounts = response.json()
            return accounts["can_write"]
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error(f"Error fetching account IDs: {e}. Retrying {retries}/{max_retries}")
            time.sleep(1)  # Wait before retrying
            if retries == max_retries:
                st.error(f"Error fetching account IDs after {max_retries} attempts: {e}")
                return []

def get_accounts():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    max_retries = 3
    retries = 0
    success = False
    while retries < max_retries and not success:
        try:
            response = requests.get(f"{get_backend_url()}/users/accounts", headers=headers)
            response.raise_for_status()
            accounts = response.json()
            return accounts
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error(f"Error fetching accounts: {e}. Retrying {retries}/{max_retries}")
            time.sleep(1)  # Wait before retrying
            if retries == max_retries:
                st.error(f"Error fetching accounts after {max_retries} attempts: {e}")
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

# Fetch All Positions and Prices
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
            #logger.error(f"No position data found for ticker: {ticker}")
            pass
    
    return pd.DataFrame(positions)


# Retrieve Price Data
def retrieve_price_data(redis_server, ticker):
    price_data_json = redis_server.get(f"price:{ticker}")
    if price_data_json:
        try:
            price = json.loads(price_data_json)
            if isinstance(price, (int, float)):
                return price
            else:
                logger.error(f"Invalid price data for ticker {ticker}: {price}")
                raise ValueError(f"Invalid price data for ticker {ticker}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding price data for ticker {ticker}: {e}")
            raise ValueError(f"Error decoding price data for ticker {ticker}")
    else:
        logger.error(f"No price data found for ticker {ticker}")
        raise ValueError(f"No price data found for ticker {ticker}")

# Read Tickers from File
def read_tickers_from_file():
    tickers_path = '/app/python/tickers.txt'
    tickers_path_development = 'python/tickers.txt'
    try:
        with open(tickers_path, 'r') as file:
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


def fetch_trade_keys_by_account(redis_server, account_id):
    trade_keys = redis_server.lrange(f"account:{account_id}:trades", 0, -1)
    return [key.decode('utf-8') for key in trade_keys]

def fetch_trade_data_by_account(redis_server, account_id):
    trade_keys = fetch_trade_keys_by_account(redis_server, account_id)
    trades = []
    for key in trade_keys:
        trade = retrieve_trade_data(redis_server, key)
        if trade is not None:
            trades.append(trade.model_dump())
        else:
            logger.error(f"Trade data for key {key} could not be retrieved.")
    return trades


# Display Table of Trade Data
@st.experimental_fragment(run_every=timedelta(seconds=refresh_rate))
def trade_view():
    st.header("Trade View")
    account_ids = fetch_account_ids()
    if account_ids:
        accounts = get_accounts()
        account_names = [account["account_name"] for account in accounts if account]
        account_name = st.selectbox("Account", account_names, key="trade_view_account_id")
        selected_account = next(account for account in accounts if account and account["account_name"] == account_name)
        account_id = selected_account["account_id"]
        redis_server = get_redis_connection()
        if redis_server:
            trade_data = fetch_trade_data_by_account(redis_server, account_id)
            user_response = requests.get(f"{get_backend_url()}/users/me", headers={"Authorization": f"Bearer {st.session_state['token']}"})
            user_data = user_response.json()
            username = user_data.get("username", "Unknown")
            if trade_data:
                # Format data
                for trade in trade_data:
                    trade['executed_time'] = pd.to_datetime(trade['executed_time']).strftime('%Y-%m-%d %H:%M')
                    trade['executed_price'] = f"${float(trade['executed_price']):,.2f}"
                    trade['total_price'] = f"${trade['quantity'] * float(trade['executed_price'][1:].replace(',', '')):,.2f}"
                    trade['primaryKey'] = f"{trade['primaryKey']['account_id']} - {trade['primaryKey']['trade_id']}"
                    trade['executed_user'] = username

                # Create a DataFrame with selected columns
                trade_df = pd.DataFrame(trade_data)
                trade_df = trade_df.rename(columns={
                    'executed_time': 'Time',
                    'ticker': 'Ticker',
                    'direction': 'Direction',
                    'quantity': 'Quantity',
                    'total_price': 'Total Price',
                    'executed_price': 'Executed Price',
                    'executed_user': 'Executed User',
                    'primaryKey': 'Primary Key'
                })
                trade_df = trade_df[['Time', 'Ticker', 'Direction', 'Quantity', 'Total Price', 'Executed Price', 'Executed User', 'Primary Key']]

                # Add a column for the row numbers starting from 1
                trade_df.insert(0, 'No.', range(1, len(trade_df) + 1))

                # Display the DataFrame without the default index
                st.dataframe(trade_df.set_index('No.'))

            else:
                st.write("No trade data available for this account.")
        else:
            st.error("Unable to connect to Redis.")
    else:
        st.error("No account IDs available.")


# Display Table of Position Data
@st.experimental_fragment(run_every=timedelta(seconds=refresh_rate))
def position_view():
    st.header("Position View")
    account_ids = fetch_account_ids()
    if account_ids:
        accounts = get_accounts()
        account_names = [account["account_name"] for account in accounts if account]
        account_name = st.selectbox("Account", account_names, key="position_view_account_id")
        selected_account = next(account for account in accounts if account and account["account_name"] == account_name)
        account_id = selected_account["account_id"]
        redis_server = get_redis_connection()
        ps = redis_server.pubsub()
        ps.subscribe('position_full_key')
        if redis_server:
            tickers = read_tickers_from_file()
            logger.info(tickers)
            if tickers:
                position_df = fetch_all_positions_and_prices(redis_server, account_id, tickers)
                if position_df.empty:
                    st.write("There are no positions for this account. Please check back after making some trades.")
                else:
                    #order = ['last_updated', 'account_id', 'ticker', 'quantity', 'position_type', 'avg_price']
                    #sorted_df = position_df.sort_values(by='last_updated', ascending=False)
                    #sorted_df.drop(columns=['last_updated'])
                    #sorted_df.columns = ['Account ID', 'Ticker', 'Quantity', 'Position Type', 'Avg. Price', 'last_updated' ,'']
                    #st.dataframe(sorted_df.drop(columns=['Account ID', 'last_updated','']))
                    used_tickers = position_df['ticker']
                    full_dict = {}
                    expanded = True
                    if expanded:
                        for ticker in used_tickers:
                            key = f"combined:{account_id}:{ticker}"
                            json_data = redis_server.get(key)
                            if json_data is not None:
                                data = json.loads(json_data)
                                #dict(data).pop('ticker')
                                full_dict[ticker] = data
                                #dict(data).pop('last updated')
                        columns = ['Account','Ticker', 'Quantity', 'Position Type', 'Avg. Price', 'Realized PnL','Unrealized PnL', 'Realized PnL Today','Total PnL','Total PnL Today','Standart Deviation','Sharpe Ratio','Alpha','Beta','R^2','Last Updated' ,'']
                        df = pd.DataFrame.from_dict(full_dict, orient='index')
                        #df.drop(columns=["ticker"])
                        df.columns = columns
                        df = df.drop(columns=['Ticker'])
                        df['Avg. Price'] = df['Avg. Price'].apply(lambda x: f"${x:,.2f}")
                        df['Realized PnL'] = df['Realized PnL'].apply(lambda x: f"${x:,.2f}")
                        df['Unrealized PnL'] = df['Unrealized PnL'].apply(lambda x: f"${x:,.2f}")
                        df['Realized PnL Today'] = df['Realized PnL Today'].apply(lambda x: f"${x:,.2f}")
                        df['Total PnL Today'] = df['Total PnL Today'].apply(lambda x: f"${x:,.2f}")
                        df['Total PnL'] = df['Total PnL'].apply(lambda x: f"${x:,.2f}")
                        st.dataframe(df)
                        #full_data = retrieve_position_full_data(redis_server, expanded)
                        #st.write(full_data)

            else:
                st.error("No tickers available.")
        else:
            st.error("Unable to connect to Redis.")
    else:
        st.error("No account IDs available.")




def single_trade():
    st.header("Single trade")
    account_ids = fetch_account_ids()
    if account_ids:
        st.session_state.pop("accounts", None)
        accounts = get_accounts()
        account_names = [account["account_name"] for account in accounts if account]
        account_name = st.selectbox("Account", account_names, key="single_trade_account_id")
        tickers = read_tickers_from_file()
        ticker = st.selectbox("Ticker", tickers, key="single_trade_ticker")
        quantity = st.number_input("Quantity", min_value=1, step=1, key="single_trade_quantity")
        direction = st.selectbox("Direction", ["BUY", "SELL"], key="single_trade_direction")
        current_price = retrieve_price_data(get_redis_connection(), ticker)

        if current_price is not None:
            button_label = f"Book: ${current_price * quantity:.2f}"
        else:
            button_label = "Book: Price not available"

        if st.button(button_label, key="single_trade_submit"):
            if current_price is None:
                st.error("Current price is not available. Please try again later.")
                return

            if account_name and ticker and quantity:
                selected_account = next(account for account in accounts if account and account["account_name"] == account_name)
                account_id = selected_account["account_id"]
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.post(f"{get_backend_url()}/publish/trade", json={
                    "account_id": account_id,
                    "ticker": ticker,
                    "quantity": quantity,
                    "direction": direction
                }, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Response data: {response_data}")
                    st.success(f"Trade submitted successfully! Total price: ${response_data.get('total_price', 'Unknown'):.2f}")
                elif response.status_code == 401:
                    st.error("User cannot create trades for this account")
                else:
                    st.error(f"Error submitting trade: {response.text}")
                time.sleep(5)
                st.experimental_rerun()
    else:
        st.error("User has no accounts")


def parse_bulk_input(bulk_input):
    # Updated regex to allow periods in tickers
    trade_pattern = re.compile(r'([A-Z\.]+)\s*,\s*(\d+)\s*,\s*([BS])\s*')
    trades = trade_pattern.findall(bulk_input)
    if not trades:
        raise ValueError("No valid trades found in the input. Ensure the format is 'TICKER, QUANTITY, DIRECTION'.")

    parsed_trades = []
    for t in trades:
        ticker, quantity, direction = t
        quantity = int(quantity)
        direction = "BUY" if direction == "B" else "SELL"
        parsed_trades.append({"ticker": ticker, "quantity": quantity, "direction": direction})

    return parsed_trades

def fetch_account_ids():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{get_backend_url()}/users/accountIds", headers=headers)
            response.raise_for_status()
            accounts = response.json()
            return accounts["can_write"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching account IDs (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(1)  # Backoff before retrying
    st.error("Failed to fetch account IDs after multiple attempts.")
    return []

def get_accounts():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{get_backend_url()}/users/accounts", headers=headers)
            response.raise_for_status()
            accounts = response.json()
            return accounts
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching accounts (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(1)  # Backoff before retrying
    st.error("Failed to fetch accounts after multiple attempts.")
    return []

def bulk_book():
    st.header("Bulk Booking")
    account_ids = fetch_account_ids()
    if account_ids:
        st.session_state.pop("accounts", None)
        accounts = get_accounts()
        account_names = [account["account_name"] for account in accounts if account]
        account_name = st.selectbox("Account", account_names, key="multi_trade_account_id")

        tickers = read_tickers_from_file()

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

        bulk_input = st.text_area("Or enter all trades in the following format: AAPL, 24, B. MSFT, 8, S. NVDA, 11, B. C, 1000, S.")

        if st.button("Submit All Trades"):
            if account_name:
                selected_account = next(account for account in accounts if account and account["account_name"] == account_name)
                account_id = selected_account["account_id"]
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}

                all_trades_successful = True
                trades_to_submit = st.session_state.multi_trade_data

                if bulk_input:
                    try:
                        trades_to_submit = parse_bulk_input(bulk_input)
                        invalid_tickers = [trade["ticker"] for trade in trades_to_submit if trade["ticker"] not in tickers]
                        if invalid_tickers:
                            st.error(f"Invalid tickers found: {', '.join(invalid_tickers)}")
                            all_trades_successful = False
                    except ValueError as e:
                        st.error(str(e))
                        all_trades_successful = False
                
                # progress_bar = st.progress(0)
                # progress_step = 100 / len(trades_to_submit)
                with st.spinner("Submitting trades..."):
                    max_retries = 3
                    for i, trade in enumerate(trades_to_submit):
                        retries = 0
                        success = False
                        while retries < max_retries and not success:
                            response = requests.post(f"{get_backend_url()}/publish/trade", json={
                                "account_id": account_id,
                                "ticker": trade["ticker"],
                                "quantity": trade["quantity"],
                                "direction": trade["direction"]
                            }, headers=headers)

                            if response.status_code == 200:
                                response_data = response.json()
                                success = True
                            else:
                                retries += 1
                                logger.error(f"Error submitting trade for {trade['ticker']}: {response.text}")
                                time.sleep(1)  # Backoff before retrying

                        if not success:
                            all_trades_successful = False
                            st.error(f"Failed to submit trade for {trade['ticker']} after {max_retries} attempts.")
                            break

                        # progress_bar.progress(int((i + 1)) * progress_step)

                if all_trades_successful:
                    st.success("All trades submitted successfully!")
                    st.balloons()
                    time.sleep(5)
                    st.session_state.multi_trade_data = []
                else:
                    st.error("One or more trades failed to submit.")
                
                # progress_bar.empty()

                time.sleep(5)
                st.experimental_rerun()
    else:
        st.error("User has no accounts")

# Trading Dashboard
def trading_dashboard():
    st.title("Trading Dashboard")

    st.sidebar.title("Trading Dashboard Settings")
    refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)

    tabs = st.tabs(["Trade View", "Position View", "Bulk Booking", "Single Trade", "Account Manager"])

    with tabs[0]:
        trade_view()

    with tabs[1]:
        position_view()

    with tabs[2]:
        bulk_book()

    with tabs[3]:
        single_trade()

    with tabs[4]:
        st.header("Account Manager")

        account_name = st.text_input("Account Name", key="create_account_account_name")
        if st.button("Create Account", key="create_account_button") and account_name:
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            response = requests.post(f"http://main10:8010/publish/account/new", json={
                "account_name": account_name
            }, headers=headers)
            if response.status_code == 200:
                st.success("Account created successfully!")
                time.sleep(5)
                # Force a reload of accounts in session state
                st.session_state.pop("accounts", None)
                st.rerun()
            else:
                st.error("Error creating account: " + str(response.status_code))
                time.sleep(3)
                st.experimental_rerun()
        if st.button("Logout"):
            st.session_state["token"] = None
            st.experimental_rerun()

# Main Function
def main():
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
