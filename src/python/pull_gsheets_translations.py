import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os

# Connect to Google Sheets API #
# follow https://medium.com/@CROSP/manage-google-spreadsheets-with-python-and-gspread-6530cc9f15d1
# Create credentials and dump into referenced file

# Initialize contstants
scope = ['https://spreadsheets.google.com/feeds',
       'https://www.googleapis.com/auth/drive']

CREDENTIALS_PATH = '../../../my_credentials/credentials.json'
TRANSLATION_SHEETS_REGEX = ' - Master Sheet'
TRANSLATION_SHEETS_REGEX_OLD = "(OLD)"
OUT_DIR = '../../docs/content/'
#OUT_DIR = 'translations/'
LANGUAGES_TO_PULL = ['English','Dutch (Netherlands)','Spanish','Italian','French','Russian']
LANGUAGE_LETTERS_DICT = {
    'English':'en',
    'Dutch':'nl',
    'Spanish':'es',
    'Italian':'it',
    'French':'fr',
    'Russian':'ru'
}

# Google sheets authorization

credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
gc = gspread.authorize(credentials)


# Get names of spreadsheets 
list_all_spreadsheets = gc.list_spreadsheet_files()
list_all_spreadsheets_name = [x['name'] for x in list_all_spreadsheets]

# Get names of translations
translation_sheet_names = [ x for x in list_all_spreadsheets_name if (TRANSLATION_SHEETS_REGEX in x) & (TRANSLATION_SHEETS_REGEX_OLD not in x)]
translation_sheet_names_select = [ x for x in translation_sheet_names for y in LANGUAGES_TO_PULL if y in x]
translation_sheets = {}

for name in translation_sheet_names_select:
    language = '_'.join(name.split(' ')).replace('/','_')
    translation_sheets[language] = gc.open(name).worksheets()

languages = [x for x in translation_sheets.keys()]
languages.sort()


"""
json structure
{
    "parentKey":{
        "childKey":{
            'fieldKey':['translatedValue'],
        }
    },
    "parentKey":{
        "childKey":{
            'fieldKey':['translatedValue'],
            'fieldKey':['translatedValue'],
        }
    }
    "parentKey":{
        "childKey":{
            'fieldKey':['translatedValue','translatedValue],
        }
    }
}
"""

for language in languages:
    locale_key = [x for x in LANGUAGE_LETTERS_DICT.keys() if x in language][0]
    locale = LANGUAGE_LETTERS_DICT[locale_key]
    language_wks = translation_sheets[language]
    wkDict = {}

    for wk in language_wks:
        wk_name = '_'.join(wk.title.split(' ')).replace('/','_')
        language_lists = wk.get_all_values()
        language_df = pd.DataFrame(language_lists[1:],columns=language_lists[0])
        language_df = language_df[language_df['parentKey']!='']
        
        
        # return a df with only the parentKey,fieldKey and translatedValue columns
        language_df = language_df[['parentKey','fieldKey','translatedValue','childKey']]

        parentKeyDict = {}
        childKeyDict = {}
        fieldKeyDict = {}
        
        # .iterrows returns a series of each row in the dataframe
        for index,row in language_df.iterrows():
            fieldKeyDict.setdefault(row['fieldKey'],[]).append(row['translatedValue'])
            childKeyDict[row['childKey']] = fieldKeyDict
            parentKeyDict[row['parentKey']] = childKeyDict

        wkDict.update(parentKeyDict)

        if not os.path.exists(OUT_DIR+locale):
            os.mkdir(OUT_DIR+locale)
            
        with open(OUT_DIR+locale+'/translation.json', 'w') as f:
            json.dump(wkDict, f)
    