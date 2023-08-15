#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import re
import json
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import bs4

DEFAULT_OUTPUT = 'wiki_output.jsonl'
DEFAULT_INTERVAL = 5.0  # interval between requests (seconds)
DEFAULT_ARTICLES_LIMIT = 1  # total number articles to be extrated
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'

visited_urls = set()  # all urls already visited, to not visit twice
pending_urls = []  # queue


def load_urls(session_file):
    """Resume previous session if any, load visited URLs"""

    try:
        with open(session_file) as fin:
            for line in fin:
                visited_urls.add(line.strip())
    except FileNotFoundError:
        pass


def extract_text_with_math(element: bs4.element.Tag) -> str:
    extracted_text = ""
    
    if isinstance(element, str):  # Regular text
        extracted_text += element

    elif element.name == 'math':  # MathML element
        alttext = element.get('alttext')
        if alttext:
            extracted_text += f"${alttext}$"
    
    elif element.name == "span" and "texhtml" in element.get("class", []):  # LaTeX element
        extracted_text += f"${element.get_text()}$"

    else:
        if not bool(element.find_all('math')) and not bool(element.find_all('span', class_='texhtml')):  
            # Regular HTML element without math
            extracted_text += element.get_text().strip()
        else: # recursive call to extract text from children elements
            for content in element.contents:
                extracted_text += extract_text_with_math(content)
    
    return extracted_text



def scrap(base_url, article, output_file, session_file):
    """Represents one request per article"""

    full_url = base_url + article
    try:
        r = requests.get(full_url, headers={'User-Agent': USER_AGENT})
    except requests.exceptions.ConnectionError:
        print("Check your Internet connection")
        # input("Press [ENTER] to continue to the next request.")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        try:
            r = requests.get(full_url, headers={'User-Agent': USER_AGENT})
        except requests.exceptions.ConnectionError:
            return
    if r.status_code not in (200, 404):
        print("Failed to request page (code {})".format(r.status_code))
        # input("Press [ENTER] to continue to the next request.")
        return

    soup = BeautifulSoup(r.text, 'html.parser')
    content = soup.find('div', {'id':'mw-content-text'})

    with open(session_file, 'a') as fout:
        fout.write(full_url + '\n')  # log URL to session file

    # add new related articles to queue
    # check if are actual articles URL
    for a in content.find_all('a'):
        href = a.get('href')
        if not href:
            continue
        if href[0:6] != '/wiki/':  # allow only article pages
            continue
        elif ':' in href:  # ignore special articles e.g. 'Special:'
            continue
        elif href[-4:] in ".png .jpg .jpeg .svg":  # ignore image files inside articles
            continue
        elif base_url + href in visited_urls:  # already visited
            continue
        if href in pending_urls:  # already added to queue
            continue
        pending_urls.append(href)

    print("Number of pending URLs: {}".format(len(pending_urls)))

    # skip if already added text from this article, as continuing session
    if full_url in visited_urls:
        return
    visited_urls.add(full_url)

    # remove all citation elements and related content
    for _eid in ["See_also", "References", "External_links", "Works_cited"]:
        # Find the element with id
        _element = soup.find(id=_eid)
        # Remove all the content after the references element
        if _element is not None:
            for x in _element.find_all_next():
                x.extract()
            _element.extract()
    
    # parenthesis_regex = re.compile('\(.+?\)')  # to remove parenthesis content
    citations_regex = re.compile('\[.+?\]')  # to remove citations, e.g. [1]

    # get plain text from each <p>
    elem_list = content.find_all(['p', 'math'])
    
    visited_math_elements = set()
    out_text = ""
    for elem in elem_list:
        if elem.name == 'p':
            for _math_elem in elem.find_all('math'):
                visited_math_elements.add(_math_elem)

            # text = elem.get_text().strip()
            text = extract_text_with_math(elem)
            # text = parenthesis_regex.sub('', text)
            text = citations_regex.sub('', text)
            if text:
                out_text += text + '\n' # extra line between paragraphs
        
        elif elem.name == 'math' and elem not in visited_math_elements: # latex math equation
            latex_code = elem.get('alttext').strip()
            if latex_code:
                out_text += f"${latex_code}$" + '\n'

    json_data = {"url": full_url, "text": out_text}
    append_to_jsonl(output_file, json_data)


# Write data to JSONL file
def append_to_jsonl(file_path, data):
    with open(file_path, 'a', encoding='utf-8') as f:
        json.dump(data, f)
        f.write('\n')  # Add newline to separate JSON objects


def main(initial_url, articles_limit, interval, output_file):
    """ Main loop, single thread """
    minutes_estimate = interval * articles_limit / 60
    print("This session will take {:.1f} minute(s) to download {} article(s):".format(minutes_estimate, articles_limit))
    print("\t(Press CTRL+C to pause)\n")
    session_file = "session_wikipedia_crawler.txt"
    load_urls(session_file)  # load previous session (if any)
    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(initial_url))
    initial_url = initial_url[len(base_url):]
    pending_urls.append(initial_url)

    
    counter = 0
    while len(pending_urls) > 0:
        try:
            counter += 1
            if counter > articles_limit:
                break
            try:
                next_url = pending_urls.pop(0)
            except IndexError:
                break

            time.sleep(interval)
            article_format = next_url.replace('/wiki/', '')[:35]
            print("{:<7} {}".format(counter, article_format))
            scrap(base_url, next_url, output_file, session_file)
        except KeyboardInterrupt:
            input("\n> PAUSED. Press [ENTER] to continue...\n")
            counter -= 1

    print("Finished!")
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial_url", nargs='?', help="Initial Wikipedia article, e.g. https://en.wikipedia.org/wiki/Mathematics", default="https://en.wikipedia.org/wiki/Mathematics")
    parser.add_argument("-a", "--articles", nargs='?', default=DEFAULT_ARTICLES_LIMIT, type=int, help="Total number of articles")
    parser.add_argument("-i", "--interval", nargs='?', default=DEFAULT_INTERVAL, type=float, help="Interval between requests")
    parser.add_argument("-o", "--output", nargs='?', default=DEFAULT_OUTPUT, help="File output")
    args = parser.parse_args()
    main(args.initial_url, args.articles, args.interval, args.output)