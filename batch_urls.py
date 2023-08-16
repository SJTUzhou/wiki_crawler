import os
import re
from urllib.parse import quote, unquote, urljoin
from tqdm import tqdm





def get_urls_from_file(inp_url_file):
    _urls = []
    with open(inp_url_file) as fin:
        for line in fin.readlines():
            _url = line.strip()
            _urls.append(_url)
    return _urls


def split_list(input_list, chunk_size):
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]


if __name__ == "__main__":
    chunk_size = int(1e6)
    _urls = get_urls_from_file("wiki_en_unique_urls.txt")
    batch_urls = split_list(_urls, chunk_size)
    for i, _batch_urls in enumerate(batch_urls):
        with open("target_urls_{}.txt".format(i), "w") as fout:
            for _url in _batch_urls:
                fout.write(_url + "\n")


