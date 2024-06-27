from pydantic import ValidationError
from datetime import datetime
from typing import Optional, Set


# Assuming the models are in a file named models.py
from models import Direction, account, primaryKey, Trade

accountIDs = 1
class ModelsTest:
    def __init__(self):
        self.accounts: Set[int] = set()  # Using a set to store account IDs
        self.trades = Set[str] = set()  # Using a set to store trade IDs]
        self.accountIDs = 1  # Initializing accountID counter



    def create_account(self, account_id: int, account_name: str):
        newAccount = account(accountId=account_id, accountName=account_name)
        self.accounts.append(newAccount.account_id)

    def create_trade(self, account_id: Optional[int], account_name: Optional[str], trade_id: str, ticker: str, direction: Direction, quantity: int, executed_price: float, executed_user: str, executed_time: datetime):
        if account_id is None and account_name is not None:
            self.create_account(accountIDs, account_name)
            accountIDs+=1
        elif account_id is not None and account_name is not None and account_id not in self.accounts:
            self.create_account(account_id, account_name)
        acc = self.accounts.get(account_id)
        pk = primaryKey(account=acc, tradeId=trade_id)
        trade = Trade(
            primaryKey=pk,
            ticker=ticker,
            direction=direction,
            quantity=quantity,
            executedPrice=executed_price,
            executedUser=executed_user,
            executedTime=executed_time
        )
        return trade

    def run_tests(self):
        try:
            # Test account creation
            acc = self.create_account("123", "Test Account")
            print(f"Account created: {acc}")

            # Test trade creation
            trade = self.create_trade(
                "123", "Test Account", "T001", "AAPL", Direction.BUY, 100, 150.25, "user1", datetime.now()
            )
            print(f"Trade created: {trade}")

        except ValidationError as e:
            print(f"Validation error: {e}")

# Example usage
if __name__ == "__main__":
    tester = ModelsTest()
    tester.run_tests()
