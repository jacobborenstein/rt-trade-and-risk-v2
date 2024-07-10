import datetime
import finnhub
import time

api_key = 'cq240mpr01ql95ncha8gcq240mpr01ql95ncha90'
finnhub_client = finnhub.Client(api_key)

def get_price(ticker):
    try:
        # Fetch current price
        quote = finnhub_client.quote(ticker)
        price = quote['c']  # Current price
        return price
    except Exception as e:
        print(f'Error fetching price for {ticker}: {e}')
        return ''

def get_with_data(ticker):
    price_dict = {}
    price_dict["ticker"] = ticker
    price_dict['price'] = get_price(ticker)
    price_dict['time'] = str(datetime.datetime.today())
    return price_dict
#if __name__ == '__main__':
    # Example usage
   # print(get_price('AAPL'))
    #print(get_price('NVDA'))
 #   l = ['AAPL', 'NVDA']
  #  print(get_bulk(l))
