# -*- coding: utf-8
import os

from bs4 import BeautifulSoup
import requests
import pandas as pd
import sqlite3
from sqlite3 import Error


def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        # print('Connection to SQLite DB successful')
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        # print("Query executed successfully")
    except Error as e:
        print(f"The error'{e}' occurred")
    cursor.close()


def execute_dict_query(connection, query, sql_dict):
    cursor = connection.cursor()
    try:
        cursor.execute(query, sql_dict)
        connection.commit()
        # print("Dictionary Query executed successfully")
    except Error as e:
        print(f"The error'{e}' occurred")
    cursor.close()


def execute_audio_query(connection, query, audio_link, query_word):
    cursor = connection.cursor()
    try:
        cursor.execute(query, (audio_link, query_word))
        connection.commit()
        # print("Audio Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
    cursor.close()


def execute_example_query(connection, query, ex_list, query_word):
    cursor = connection.cursor()
    try:
        ex_list.append(query_word)
        cursor.execute(query, ex_list)
        connection.commit()
        # print("Example Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
    cursor.close()


dbDir = "./sql"
if not os.path.exists(dbDir):
    os.makedirs(dbDir)

sqlConnection = create_connection("./sql/penobscot.sqlite")

create_words_table = """
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Word TEXT,
    PartOfSpeech TEXT,
    SubPartOfSpeech TEXT,
    EnglishTranslation TEXT
);
"""

create_audio_table = """
CREATE TABLE IF NOT EXISTS audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    LinkToAudio TEXT,
    word_id INTEGER,
    FOREIGN KEY (word_id) REFERENCES words (id)
);
"""

create_example_table = """
CREATE TABLE IF NOT EXISTS examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    PenobscotForm TEXT,
    EnglishTranslation TEXT,
    PartOfSpeech TEXT,
    word_id INTEGER,
    FOREIGN KEY (word_id) REFERENCES words (id)
);
"""

execute_query(sqlConnection, create_words_table)
execute_query(sqlConnection, create_audio_table)
execute_query(sqlConnection, create_example_table)

# df = pd.DataFrame(
#     {
#         "Word": [],
#         "PartOfSpeech": [],
#         "SubPartOfSpeech": [],
#         "EnglishTranslation": [],
#         "LinkToAudio": [],
#         "ExampleTable": [],
#     }
# )

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
    for subLink in pageLinks[1:-1]:

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
                    "PartOfSpeech": "",
                    "SubPartOfSpeech": "",
                    "EnglishTranslation": "",
                    "LinkToAudio": "",
                    "ExampleTable": "",
                }

                audioDict = {}
                numAudioLinks = 0

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
                            numAudioLinks += 1
                            audioDict[str(numAudioLinks)] = audio['src']

                addDict["LinkToAudio"] = audioDict

                create_word = """
                    INSERT INTO words (word, PartOfSpeech, SubPartOfSpeech, EnglishTranslation)
                    VALUES (:Word, :PartOfSpeech, :SubPartOfSpeech, :EnglishTranslation);
                """
                execute_dict_query(sqlConnection, create_word, addDict)

                # Pandas has method to parse table straight to df
                try:
                    exampleTable = pd.read_html(wordURL)
                    try:
                        example_df = exampleTable[0]["Examples"]
                    except KeyError:
                        example_df = exampleTable[0]["Notes"]

                    for index in range(0, example_df.shape[0]):
                        create_example = f"""
                                            INSERT INTO examples (PenobscotForm, EnglishTranslation, PartOfSpeech, word_id)
                                            VALUES (?,?,?,(SELECT id FROM words WHERE Word=?));
                                        """
                        exampleList = example_df.iloc[index].tolist()
                        execute_example_query(sqlConnection, create_example,
                                              exampleList, addDict["Word"])
                except ValueError:
                    pass

                i = 1
                while i <= numAudioLinks:
                    create_audio = """
                        INSERT INTO audio (LinkToAudio, word_id)
                        VALUES (?,(SELECT id FROM words WHERE Word=?));
                    """
                    execute_audio_query(sqlConnection, create_audio,
                                        audioDict[str(i)], addDict["Word"])
                    i += 1

                # df = df.append(addDict, ignore_index=True)
