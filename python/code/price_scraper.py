import requests 
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup 
import pandas as pd 
import time
from datetime import datetime

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'} 

#urls = [
 #   'https://finance.yahoo.com/quote/NVDA/',
  #  'https://finance.yahoo.com/quote/AAPL/',
   # 'https://finance.yahoo.com/quote/TSLA/'
    #]
#prices = {}
def get_price(ticker):
    price = "" 
    url = 'https://finance.yahoo.com/quote/' + ticker + "/"
    page = requests.get(url,headers=headers, verify=False) 
    try:
        soup = BeautifulSoup(page.text,'html.parser') 
        price = soup.find('fin-streamer', {'class':'livePrice svelte-mgkamr'}).find_all('span')[0].text 
    except AttributeError: 
        print("Change the Element id")
    return(price)
    
def get_s_and_p():
    dic = {}
    req = requests.Session()
    url = "https://www.slickcharts.com/sp500"
    page = req.get(url,headers=headers, verify=False) 
    try:
        soup = BeautifulSoup(page.text,'html.parser') 
        page_txt = list(soup.stripped_strings)
        for index, s in enumerate(page_txt):
            if s.isupper():
                dic[s] = {"price":page_txt[index + 2], "time":str(datetime.now())}
        dic.pop("S&P 500")
    except AttributeError: 
        print("Change the Element id")
    return(dic)