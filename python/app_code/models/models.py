from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Literal, List

class Direction(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class PositionType(str, Enum):
    LONG = 'LONG'
    SHORT = 'SHORT'

class Account(BaseModel):
    account_id: str = Field(..., alias="accountId")
    account_name: str = Field(..., alias="accountName")

class PrimaryKey(BaseModel):
    account_id: str = Field(..., alias="accountId")
    trade_id: str = Field(..., alias="tradeId")

class Trade(BaseModel):
    primaryKey: PrimaryKey
    ticker: str
    direction: Direction
    quantity: int
    executed_price: float = Field(..., alias="executedPrice")
    executed_user: str = Field(..., alias="executedUser")
    executed_time: datetime = Field(..., alias="executedTime")

class Position(BaseModel):
    account_id: str = Field(..., alias="accountId")    
    ticker: str
    quantity: int
    position_type: PositionType = Field(..., alias="positionType")
    avg_price: float = Field(..., alias="avgPrice")
    last_updated: datetime = Field(..., alias="lastUpdated")

class TickerPrice(BaseModel):
    ticker: str
    price: float
    time: datetime
