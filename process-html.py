
# This script takes all files in the html-files folder and extracts the summarised listing data into a dataframe, 1 row per listing. It is meant as a PoC to show how the listing data can be utilised. There is much richer data in the HTML which can be further extracted.

import json
import pandas as pd
from bs4 import BeautifulSoup
import os
from tqdm import tqdm


page_data_ls = []
for file in tqdm(os.listdir('html-files')):
    if '.html' in file:
        with open('html-files//'+file, 'r', encoding='utf-8') as file_data:
            html = file_data.read()
            
    soup = BeautifulSoup(html, 'html.parser')
    script_tags = soup.find_all('script') # PropGuru preforms the JS script containing the listing data that will be displayed on the page. The summary data is stored as textual JS.
    
    for script in script_tags:
        if 'guruApp.listingResultsWidget' in str(script): # This is the section containing our listings
            raw = script
            raw_str = raw.text # Needed to extract the listings as strings


    # Since the entire dictionary is a string, we need to recreate the dict
    start = raw_str.index('{')
    end = raw_str.rfind('}')
    raw_text = raw_str[start:end+1]
    raw_text = raw_text.replace('\'gaECListings\'','\"gaECListings\"')
    json_obj = json.loads(raw_text)
    
    # Go through each listing format all data into a df
    df_ls = []
    for item in json_obj['gaECListings']:
        productData = item['productData']
        df_ls.append(pd.DataFrame.from_dict(productData, orient='index').T)
    page_data = pd.concat(df_ls)
    page_data_ls.append(page_data)

final_df = pd.concat(page_data_ls)
final_df.to_csv('processed-df//'+ file[0:16]+'df.csv') # Save compiled df with timestamp to identify the run.