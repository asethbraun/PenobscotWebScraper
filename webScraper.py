# -*- coding: utf-8 
from bs4 import BeautifulSoup
import requests

URL = 'https://penobscot-dictionary.appspot.com/entry'
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')

## These are the top-level letter indexes of the dictionary
topLetters = soup.find(class_ = 'nav nav-tabs')
topLetters = topLetters.find_all('a')

for link in topLetters:
    
    subURL = URL[0:-6] + link.get('href')
    subpage = requests.get(subURL)
    
    subSoup = BeautifulSoup(subpage.content,'html.parser')
    
    ##Each letter has multiple pages
    pages = subSoup.find(class_ = 'pagination')
    pageLinks = pages.find_all('a')
    
    #ignore first and last as they aren't specific pages
    for subLink in pageLinks[1:-2]:
        
        pageURL = URL[0:-6] + subLink.get('href')
        letterPage = requests.get(pageURL)
        
        letterSoup = BeautifulSoup(letterPage.content, 'html.parser')
        
        rows = letterSoup.find(class_ = 'row')
        
        word = rows.find(class_ = 'col-md-2')
        wordLinks = word.find_all('a')
        
        for entry in wordLinks:
            
            wordURL = URL[0:-6] + entry.get('href')
            wordPage = requests.get(wordURL)
            
            wordSoup = BeautifulSoup(wordPage.content,'html.parser')
            
            ##word in Penobscot in heading
            penobWord = wordSoup.find(class_ = 'panel-heading')
            penobWord = penobWord.find_all('h1')
            
            #partOfSpeech = 
            
            ##English Translation
            #engTrans = 
            
            print(wordSoup.prettify())
        
        
    # print(subSoup.prettify())

##print(topLetters)
