import redis
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from app_code.models.models import Trade, TradeRequest, Account, PrimaryKey, Direction, UserInDB, Token, User, UserCreate, AccountType
import json
from datetime import datetime, timedelta
import logging
import uuid
import random
from app_code.mongo.crud import get_user_write_accounts, get_user_accounts, update_user_permissions, get_recent_position, create_user, check_user_exists
from app_code.authorization.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from app_code.redis_cache.cache_database import retrieve_price_data


# Define constants
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
r = redis.Redis(host='redis', port=6379)
r.ping()


@app.post("/publish/account/new")
async def publish_account(account_name: str = Body(..., embed=True), current_user: User = Depends(get_current_user)):
    account_id = "ACC_" + str(uuid.uuid4())
    current_user.can_write = current_user.can_write if current_user.can_write is not None else []
    current_user.can_write.append(account_id)
    await update_user_permissions(current_user.username, current_user.can_read, current_user.can_write)
    

    account = Account(accountId=account_id, accountName=account_name, accountType=AccountType.TRADER)
    r.publish('accounts', account.model_dump_json(by_alias=True))
    return {"status": "Created new account: " + account.account_id}

@app.post("/publish/trade")
async def publish_trade(trade_request: TradeRequest, current_user: User = Depends(get_current_user)):
    account_id = trade_request.account_id
    ticker = trade_request.ticker
    quantity = trade_request.quantity
    direction = trade_request.direction

    logger.info(f"Current user: {current_user}")
    if current_user.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is missing"
        )

    if (current_user.can_write is not None and account_id not in current_user.can_write) or current_user.can_write is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User can not create trades for this account"
        )

    logger.info("main-1) Publishing trade...")
    trade = await generate_trade(account_id, current_user.user_id, ticker, quantity, direction)
    logger.info(f"main-2) created trade")

    trade_data = trade.model_dump(by_alias=True)
    trade_data['executedTime'] = trade_data['executedTime'].isoformat()  # Convert datetime to string
    r.publish('trades-to-mongo', json.dumps(trade_data))
    logger.info(f"main-3) published trade: {trade_data}")
    return {"status": "Trade Sent"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await authenticate_user(form_data.username, form_data.password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the server"
        )
     
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/new", response_model=User)
async def create_new_user(user: UserCreate):
    try:
        user_exists = await check_user_exists(user.username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the server"
        )
    
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    user_id = f"{user.username}_{str(uuid.uuid4())}_{str(datetime.utcnow().timestamp())}"
    user_in_db = UserInDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        user_id=user_id,
        disabled=False,
        can_read=[],
        can_write=[]
    )
    created_user = await create_user(user_in_db)
    return created_user

@app.get("/users/accountIds")
async def get_user_account(current_user: User = Depends(get_current_user)):
    return await get_user_accounts(current_user.username)

@app.get("/users/accounts")
async def get_user_write_account(current_user: User = Depends(get_current_user)):
    accounts = await get_user_write_accounts(current_user.username)
    return [account.dict() for account in accounts]
    
    

async def generate_trade(account_id: str, user_id: str, ticker: str, quantity: int, direction: Direction) -> Trade:
    logger.info(f"account_id: {account_id}, user_id: {user_id}, ticker: {ticker}, quantity: {quantity}")
    logger.info("Generating trade...")


    primaryKey = PrimaryKey(accountId=account_id, tradeId=generate_trade_id(ticker))
    # executed_price = retrieve_price_data(r, ticker)
    executed_price = retrieve_price_data(r, ticker)
    if executed_price is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve price data for the ticker")
    logger.info(f"Creating trade with executedUser: {user_id}")

    return Trade(
        primaryKey=primaryKey,
        ticker=ticker,
        direction=direction,
        quantity=quantity,
        executedPrice=executed_price,
        executedUser=user_id,
        executedTime=datetime.now()
    )

def generate_trade_id(ticker: str) -> str:
    return ticker + "_" + str(uuid.uuid4()) + "_" + str(datetime.now().timestamp())
