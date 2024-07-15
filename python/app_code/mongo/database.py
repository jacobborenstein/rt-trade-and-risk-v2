from motor.motor_asyncio import AsyncIOMotorClient

# Connection stream to MongoDB server
MONGO_DETAILS = "mongodb://mongo:27017"

# Create a client instance of the motor library
client = AsyncIOMotorClient(MONGO_DETAILS)

# Create a database instance
database = client['traderDB']

# define the collections
account_collection = database.get_collection('accounts')
trade_collection = database.get_collection('trades')
position_collection = database.get_collection('positions')
price_collection = database.get_collection('ticker_prices')
user_collection = database.get_collection('users')
