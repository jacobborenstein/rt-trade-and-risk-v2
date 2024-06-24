from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Literal, List

class Direction(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class account(BaseModel):
    account_id: str = Field(..., alias="accountId")
    account_name: str = Field(..., alias="accountName")
    trades: List['Trade'] = []
    def get_account_id(self) -> str:
        return self.account_id

    def get_account_name(self) -> str:
        return self.account_name

class primaryKey(BaseModel):
    account: account
    trade_id: str = Field(..., alias="tradeId")

class Trade(BaseModel):
    primaryKey: primaryKey
    ticker: str
    direction: Direction
    quantity: int
    executed_price: float = Field(..., alias="executedPrice")
    executed_user: str = Field(..., alias="executedUser")
    executed_time: datetime = Field(..., alias="executedTime")