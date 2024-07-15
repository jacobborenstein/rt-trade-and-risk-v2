import datetime
import finnhub
import time

eggman_key = 'cq240mpr01ql95ncha8gcq240mpr01ql95ncha90'
eggman_client = finnhub.Client(eggman_key)
ben_porat_key = 'cq8n0b1r01qnitievo80cq8n0b1r01qnitievo8g'
ben_porat_client = finnhub.Client(ben_porat_key)
ish_tam_key = 'cq1d6j1r01qjh3d5itq0cq1d6j1r01qjh3d5itqg'
ish_tam_client = finnhub.Client(ish_tam_key)
dont_have_a_second_joke_for_jacob_key = 'cq8opq9r01qnitif1950cq8opq9r01qnitif195g'
dont_have_a_second_joke_for_jacob_client = finnhub.Client(dont_have_a_second_joke_for_jacob_key)
hamalach_key = 'cq9pkh1r01qlu7f3bhpgcq9pkh1r01qlu7f3bhq0'
hamalach_client = finnhub.Client(hamalach_key)

clients = [eggman_client, ben_porat_client, ish_tam_client, dont_have_a_second_joke_for_jacob_client, hamalach_client]

def get_price(ticker, api):
    try:
        finnhub_client = clients[api]
        # Fetch current price
        quote = finnhub_client.quote(ticker)
        price = quote['c']  # Current price
        return price
    except Exception as e:
        print(f'Error fetching price for {ticker}: {e}')
        return ''

def get_with_data(ticker, num):
    price_dict = {}
    price_dict["ticker"] = ticker
    
    price_dict['price'] = get_price(ticker, num)
    price_dict['time'] = str(datetime.datetime.today())
    return price_dict
#if __name__ == '__main__':
    # Example usage
   # print(get_price('AAPL'))
    #print(get_price('NVDA'))
 #   l = ['AAPL', 'NVDA']
  #  print(get_bulk(l))
