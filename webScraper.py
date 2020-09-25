# -*- coding: utf-8 
from bs4 import BeautifulSoup
import requests

URL = 'https://penobscot-dictionary.appspot.com/entry'
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')

topLetters = soup.find(class_='nav nav-tabs')

topLetters = topLetters.find_all('a')

for link in topLetters:
    subURL = URL[0:-6] + link.get('href')
    subpage = requests.get(subURL)
    
    subSoup = BeautifulSoup(subpage.content,'html.parser')
    
    print(subSoup.prettify())

##print(topLetters)