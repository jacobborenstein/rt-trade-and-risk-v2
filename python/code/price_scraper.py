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
    req = requests#.Session()
    url = "https://www.slickcharts.com/sp500"
    page = req.get(url,headers=headers, verify=False, cookies={'_ga': 'GA1.1.942504165.1719341093', '_ga_MWXZ0FBF55':'GS1.1.1719856034.2.0.1719856034.0.0.0', '_hjSessionUser_845487' : 'eyJpZCI6ImJjOGM5MzJmLTViNjctNTIxOC1hZDA5LWIzODc4ZDY5ZTA5MSIsImNyZWF0ZWQiOjE3MTkzNDEwOTg0MzQsImV4aXN0aW5nIjpmYWxzZX0=', 'cf_clearance':'SuXJ4vR1M_VjmXI5XWMdLsdQWiBBZoFuNPBfgrauKKc-1719856033-1.0.1.1-9o2TVBJtzERcD5IFRXLEBVjAUIvaUkr6m5MO3btrXhf.tsRcM1ZtcrnK3v7U9uBnz3vGciNw71.9o3hIEehCmA'}) 
    try:
        soup = BeautifulSoup(page.text,'html.parser') 
        page_txt = list(soup.stripped_strings) 
        #page_txt = list(soup.stripped_strings)
        for index, s in enumerate(page_txt):
            if s.isupper():
                dic[s] = {"price":page_txt[index + 2], "time":str(datetime.now())}
    except AttributeError: 
        print("Change the Element id")
    return(dic)