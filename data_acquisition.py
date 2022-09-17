import urllib3
from tqdm import tqdm
from article_scraper import download_pdf, get_article_metadata
from preprocess.data2table import create_metadata_table
from preprocess.pdf2text import pdf_to_text, get_dkey
import numpy as np
import fitz
import requests
from csv import writer
import os


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    metadata_save_path = 'data/tables/metadata_table.csv'
    np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    num_lines = sum(1 for line in open('polish_articles_urls.txt', 'r'))

    meta_url_suffix = '?show=full'
    save_raw_data_path = 'data/raw_text/'
    metadata_table_path = 'data/tables/metadata_table.csv'
    metadata_list = []
    autosave = 0
    line = 0

    if not os.path.exists(metadata_table_path):
        create_metadata_table().to_csv(metadata_table_path, encoding='utf-8-sig')
    else:
        input("Metadata already exist - stop the program or press Enter to continue...")

    with open("polish_articles_urls.txt", "r") as articles_urls:

        for url in tqdm(articles_urls, total=num_lines):
            line += 1
            url = url[:-1]

            try:
                pdf_raw = download_pdf(url)
            except (requests.exceptions.ConnectionError, ConnectionAbortedError, urllib3.exceptions.ProtocolError) as e:
                open('data_logs/error_logs/url_error_logs.txt', "a", encoding='utf-8-sig').write(
                    "Connection stoped on url: " + url + '\n')
                input("Wait for connection and press Enter to try again...")
                pdf_raw = download_pdf(url)
            except:
                open('data_logs/error_logs/url_error_logs.txt', "a", encoding='utf-8-sig').write(
                    "Problem encountered while downloading pdf from: " + url + '\n')
                continue

            try:
                text_data, _ = pdf_to_text(pdf_raw, margins=True, margin_size=[0,0,20,20])
            except fitz.fitz.FileDataError:
                open('data_logs/error_logs/url_error_logs.txt', "a", encoding='utf-8-sig').write(
                    'Broken pdf or non-pdf file error: ' + url + '\n')
                continue

            if not text_data or len(" ".join(text_data.split())) < 5000:
                open('data_logs/error_logs/url_error_logs.txt', "a", encoding='utf-8-sig').write('Empty/Unreadable pdf file: ' + url + '\n')
                continue
            else:
                dkey = get_dkey(text_data)
                # save raw text
                open(save_raw_data_path+dkey+'.txt', "a",encoding='utf-8-sig').write(text_data)
                # Add data to metadata table
                title, authors, source, doc_type, keywords = get_article_metadata(url + meta_url_suffix)
                metadata_list.append([dkey,title, authors, source, doc_type, keywords, url])

            if autosave == 200:
                with open(metadata_table_path, 'a+', newline='', encoding='utf-8-sig') as write_obj:
                    # Create a writer object from csv module
                    csv_writer = writer(write_obj)
                    # Add contents of list as last row in the csv file
                    for elem in metadata_list:
                        csv_writer.writerow(elem)
                    metadata_list = []
                open('data_logs/update_logs/update_logs.txt', "a", encoding='utf-8-sig').write(
                    'Last url in update: ' + url + '. On line: ' + str(line) + '\n')

                autosave = 0

            autosave += 1
