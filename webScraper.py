# -*- coding: utf-8 
from bs4 import BeautifulSoup
import requests
import pandas as pd

df = pd.DataFrame(
    {
        "Word": [],
        "PartOfSpeech": [],
        "SubPartOfSpeech": [],
        "EnglishTranslation": [],
        "LinkToAudio": [],
        "ExampleTable": [],
    }
)

URL = 'https://penobscot-dictionary.appspot.com/entry'
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')

# These are the top-level letter indexes of the dictionary
topLetters = soup.find(class_='nav nav-tabs')
topLetters = topLetters.find_all('a')

for link in topLetters:

    subURL = URL[0:-6] + link.get('href')
    subpage = requests.get(subURL)

    subSoup = BeautifulSoup(subpage.content, 'html.parser')

    # Each letter has multiple pages
    pages = subSoup.find(class_='pagination')
    pageLinks = pages.find_all('a')

    # ignore first and last as they aren't specific pages
    for subLink in pageLinks[1:-2]:

        pageURL = URL[0:-6] + subLink.get('href')
        letterPage = requests.get(pageURL)

        letterSoup = BeautifulSoup(letterPage.content, 'html.parser')

        rows = letterSoup.find_all(class_='row')

        for row in rows:
            # word = row.find_all(class_='col-md-2')
            # wordLinks = word.find_all('a')
            wordLinks = row.find_all('a')

            for entry in wordLinks:
                wordURL = URL[0:-6] + entry.get('href')
                wordPage = requests.get(wordURL)

                wordSoup = BeautifulSoup(wordPage.content, 'html.parser')

                # word in Penobscot in heading
                penobWord = wordSoup.find(class_='panel-heading')
                penobWord = penobWord.find('h1')

                detailRows = wordSoup.find_all(class_="row")

                addDict = {
                    "Word": penobWord.get_text(),
                    "PartOfSpeech": [],
                    "SubPartOfSpeech": [],
                    "EnglishTranslation": [],
                    "LinkToAudio": [],
                    "ExampleTable": [],
                }

                audioDict = {}
                i = 1

                # Pandas has method to parse table straight to df
                try:
                    exampleTable = pd.read_html(wordURL)
                    addDict["ExampleTable"] = exampleTable[0]["Examples"].to_dict()
                except ValueError:
                    pass

                for detailRow in detailRows:
                    detail = detailRow.find('p')

                    # if no <p>, then either audio or empty row
                    if detail is not None:
                        category = detail.find('strong').get_text()
                        detail = detail.get_text()

                        if category == "Part of Speech : ":
                            addDict["PartOfSpeech"] = detail[17:].strip()
                        elif category == "Sub Part of Speech : ":
                            addDict["SubPartOfSpeech"] = detail[21:].strip()
                        elif category == "English Translation : ":
                            addDict["EnglishTranslation"] = detail[21:].strip()
                    else:
                        audio = detailRow.find('source')

                        # Some words lack Sub Parts of Speech, so ignore those empty rows
                        if audio is not None:
                            audioDict[str(i)] = audio['src']
                            i += 1

                addDict["LinkToAudio"] = audioDict
                print(addDict)
                df = df.append(addDict, ignore_index=True)


