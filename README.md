# wiki_crawler

Crawl wikipedia from a start url and turn math formula into latex format.

The code is modified from Repo: https://github.com/SJTUzhou/wiki_crawler.git

1.  "wikipedia-crawler.py": Single thread crawling from a start url. 

(1.1) A text file "session_wikipedia_crawler.txt" is used to keep track of the visited urls.

(1.2) The output cleaned text is stored in a jsonl file "wiki_output.jsonl".

2. "ray-wiki-crawler.py": Multi-processing crawling supported by ray from a start url.

(2.1) The output is saved in Directory "ray_wiki_output": A text file "session_visited_urls.txt" to save the visited urls and $NUM_WORKERS$ jsonl files "wiki_data_{:03d}.jsonl" where {:03d} is the process id.

3. "wiki": a scraper project using Scrapy framework to crawl wikipedia.

(3.1) Usage: 
    ```
    cd ./wiki
    scrapy crawl wiki_math
    ```
(3.2) Use library pymongo to store output in the local mongodb (i.e. "mongodb://localhost:27017/").


