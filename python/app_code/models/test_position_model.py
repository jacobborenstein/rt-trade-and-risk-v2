from models import Direction, Account, PrimaryKey, Trade, Position
from datetime import datetime

def test_position_model():
    # Create a test account
    account = Account(accountId="1", accountName="Test Account")

    # Create a test primary key
    primary_key = PrimaryKey(account=account, tradeId="T001")

    # Create a test trade
    trade = Trade(
        primaryKey=primary_key,
        ticker="AAPL",
        direction=Direction.BUY,
        quantity=100,
        executedPrice=150.25,
        executedUser="user1",
        executedTime=datetime(2023, 6, 24, 15, 30, 0)
    )

    # Create a test position
    position = Position(
        account=account,
        ticker="AAPL",
        quantity=100,
        avgPrice=150.25,
        lastUpdated=datetime.now()
    )

    # Print the position object
    print(position)

    # Print the position dictionary with aliases
    position_dict = position.model_dump(by_alias=True)
    print(position_dict)

if __name__ == "__main__":
    test_position_model()
