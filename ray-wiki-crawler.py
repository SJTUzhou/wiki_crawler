#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import ray
import sys
import time
import argparse
import re
import json
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import bs4

DEFAULT_OUTPUT = 'ray_wiki_output'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
TIME_INTERVAL = 3  # interval before retry
NUM_WORKERS = 8


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
    
def record_visited_urls(session_file:str, visited_not_recorded_urls:list) -> None:
    with open(session_file, 'a') as fout:
        for url in visited_not_recorded_urls:
            fout.write(url + '\n')


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


@ray.remote
def scrap(base_url, article, output_dir, process_id, visited_urls:set):
    """Represents one request per article"""
    article_format = article.replace('/wiki/', '')[:35]
    print(article_format)

    full_url = base_url + article
    try:
        # time.sleep(TIME_INTERVAL)
        r = requests.get(full_url, headers={'User-Agent': USER_AGENT})
    except requests.exceptions.ConnectionError:
        print("Check your Internet connection")
        print(f"Retrying in {TIME_INTERVAL} seconds...")
        time.sleep(TIME_INTERVAL)
        try:
            r = requests.get(full_url, headers={'User-Agent': USER_AGENT})
        except requests.exceptions.ConnectionError:
            return [], False
    if r.status_code not in (200, 404):
        print("Failed to request page (code {})".format(r.status_code))
        return [], False

    try:
        soup = BeautifulSoup(r.text, 'html.parser')
        content = soup.find('div', {'id':'mw-content-text'})
        # add new related articles to queue
        # check if are actual articles URL

        _pend_urls = []

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
            
            _pend_urls.append(href)


        # skip if already added text from this article, as continuing session
        if full_url in visited_urls:  # already visited
            return _pend_urls, True


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
        output_file = os.path.join(output_dir, "wiki_data_{:03d}.jsonl".format(process_id))
        append_to_jsonl(output_file, json_data)

        return _pend_urls, True
    
    except Exception as e:
        print(e)
        return [], False


# Write data to JSONL file
def append_to_jsonl(file_path, data):
    with open(file_path, 'a', encoding='utf-8') as f:
        json.dump(data, f)
        f.write('\n')  # Add newline to separate JSON objects





def main(initial_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print("\t(Press CTRL+C to pause)\n")

    session_file = os.path.join(output_dir, "session_visited_urls.txt")
    load_urls(session_file)

    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(initial_url))
    initial_url = initial_url[len(base_url):]
    pending_urls = [initial_url, ]
    
    while len(pending_urls) > 0:
        try:
            print("Number of pending URLs: {}".format(len(pending_urls)))
            new_pending_urls = set()

            batch_size = 10 * NUM_WORKERS
            for b in range(0, len(pending_urls), batch_size):
                next_urls = pending_urls[b:b+batch_size]
                new_pending_url_lists_with_flags = ray.get([scrap.remote(base_url, next_url, output_dir, i%NUM_WORKERS, visited_urls) for i, next_url in enumerate(next_urls)])

                prev_visited_urls = []
                failed_urls = []
                for (_list, _success), _url in zip(new_pending_url_lists_with_flags, next_urls):
                    new_pending_urls.update(_list)
                    if _success == True:
                        prev_visited_urls.append(_url)
                    else:
                        print("Failed to request page: {}".format(_url))
                        failed_urls.append(_url)

                visited_urls.update(prev_visited_urls)
                new_pending_urls.update(failed_urls)
                record_visited_urls(session_file, prev_visited_urls)
                print("Number of visited URLs in total: {}".format(len(visited_urls)))
                    
            pending_urls = list(new_pending_urls)
            
        except KeyboardInterrupt:
            input("\n> PAUSED. Press [ENTER] to continue...\n")

    print("Finished!")
    sys.exit(0)


if __name__ == '__main__':
    ray.init(num_cpus=NUM_WORKERS)
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial_url", nargs='?', help="Initial Wikipedia article, e.g. https://en.wikipedia.org/wiki/Mathematics", default="https://en.wikipedia.org/wiki/Mathematics")
    parser.add_argument("-o", "--output", nargs='?', default=DEFAULT_OUTPUT, help="File output")
    args = parser.parse_args()
    main(args.initial_url,  args.output)
    ray.shutdown()