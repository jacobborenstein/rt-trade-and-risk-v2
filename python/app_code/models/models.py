from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Literal, List, Optional

class Direction(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class PositionType(str, Enum):
    LONG = 'LONG'
    SHORT = 'SHORT'

class AccountType(str, Enum):
    TRADER = 'TRADER'
    
class Account(BaseModel):
    account_id: Optional[str] = Field(..., alias="accountId")
    account_name: str = Field(..., alias="accountName")
    # account_type: AccountType = Field(..., alias="accountType")



class PrimaryKey(BaseModel):
    account_id: str = Field(..., alias="accountId")
    trade_id: str = Field(..., alias="tradeId")

class TradeRequest(BaseModel):
    account_id: str
    ticker: str
    quantity: int
    direction: Direction


class Trade(BaseModel):
    primaryKey: PrimaryKey
    ticker: str
    direction: Direction
    quantity: int
    executed_price: float = Field(..., alias="executedPrice")
    executed_user: str = Field(..., alias="executedUser")
    executed_time: datetime = Field(..., alias="executedTime")

    def to_json(self):
    # Convert the object to a dictionary for json
        return {
            "primaryKey": self.primaryKey.model_dump(by_alias=True),
            "ticker": self.ticker,
            "direction": self.direction,
            "quantity": self.quantity,
            "executedPrice": self.executed_price,
            "executedUser": self.executed_user,
            "executedTime": self.executed_time.isoformat() if self.executed_time else None
        }

class Position(BaseModel):
    account_id: str = Field(..., alias="accountId")
    ticker: str
    quantity: int
    position_type: PositionType = Field(..., alias="positionType")
    avg_price: float = Field(..., alias="avgPrice")
    last_updated: datetime = Field(..., alias="lastUpdated")

    def to_json(self):
        # Convert the object to a dictionary for json
        return {
            "accountId": self.account_id,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "positionType" : self.position_type,
            "avgPrice": self.avg_price,
            "lastUpdated": self.last_updated.isoformat() if self.last_updated else None
        }

class TickerPrice(BaseModel):
    ticker: str
    price: float
    time: datetime

class User(BaseModel):
    username: str
    email: str
    full_name: str
    user_id: Optional[str] = None
    disabled: Optional[bool] = None
    can_read: Optional[List[str]] = None
    can_write: Optional[List[str]] = None

class UserInDB(User):
    hashed_password: str

class UserCreate(User):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
