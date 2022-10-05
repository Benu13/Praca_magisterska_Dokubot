# Get url-s of articles from ceon database, only for articles writen in Polish language
# This function is quite slow, but this effect is desirable because it save us from sending too many requests too fast
# and getting ourselves banned.
# TODO - description

import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_pl_urls(url):
    main_link = "https://depot.ceon.pl"
    urls = []

    read = requests.get(url)
    html_content = read.content
    soup = BeautifulSoup(html_content, "html.parser")

    mydivs = soup.find_all("h4", {"class": "artifact-title"})

    # For loop that iterates over all the <li> tags
    for h in mydivs:
        # looking for anchor tag inside the <li>tag
        a = h.find('a')
        try:
            # looking for href inside anchor tag
            if 'href' in a.attrs:
                # storing the value of href in a separate
                # variable
                url = a.get('href')
                full_link = main_link + url

                read2 = requests.get(full_link + '?show=full')
                html_content2 = read2.content
                soup2 = BeautifulSoup(html_content2, "html.parser")

                if soup2.find('td', class_='label-cell',
                              string=lambda s: s.strip() == 'dc.language.iso').find_next_sibling().string == 'pl':
                    urls.append(full_link)

        # if the list does not has a anchor tag or an anchor
        # tag does not has a href params we pass
        except:
            pass

    next_page = soup.find_all("a", {"class": "next-page-link"})[0]['href']
    print(next_page)

    if next_page:
        urls = urls + get_pl_urls(main_link + next_page)

    return urls


def download_pdf(url):
    read = requests.get(url)
    soup = BeautifulSoup(read.text, "html.parser")

    data = soup.find_all("div", {"class": "item-page-field-wrapper table word-break"})

    a_class = data[0].find_all('a')
    pdf_url = a_class[0].get('href')
    pdf_url_full = "https://depot.ceon.pl" + pdf_url

    r = requests.get(pdf_url_full, stream=True)

    return r.content


def get_article_metadata(url):

    r = requests.get(url)
    df_list = pd.read_html(r.text)  # this parses all the tables in webpages to a list
    df = df_list[0]

    try:
        title = df[df[0].values == 'dc.title'][1].values[0]
    except IndexError:
        title = "unknown_title"

    try:
        authors = df[df[0].values == 'dc.contributor.author'][1].values[0]
    except IndexError:
        authors = "unknown_author"

    try:
        source = df[df[0].values == 'dc.identifier.citation'][1].values[0]
    except IndexError:
        source = "unknown_source"

    try:
        doc_type = df[df[0].values == 'dc.type'][1].values[0]
    except IndexError:
        doc_type = "unknown_doc_type"

    try:
        keywords = df[(df[0].values == 'dc.subject') & (df[2].values == 'pl')][1].values.tolist()
    except IndexError:
        keywords = []

    return title, authors, source, doc_type, keywords


# Get polish articles urls
if __name__ == '__main__':

    url = "https://depot.ceon.pl/handle/123456789/59/recent-submissions"
    ao = get_pl_urls(url)

    with open(r'polish_articles_urls.txt', 'w') as fp:
        for item in ao:
            fp.write("%s\n" % item)
        print('Done')
