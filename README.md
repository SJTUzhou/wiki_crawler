# wiki_crawler

Crawl wikipedia from a start url and turn math formula into latex format.

The code is modified from Repo: https://github.com/AndreiRegiani/wikipedia-crawler

1.  "`wikipedia-crawler.py`": Single thread crawling from a start url. 

    - Usage: `python wikipedia-crawler.py --initial_url https://en.wikipedia.org/wiki/Mathematics --articles 100 --interval 3 --output ./wiki_output.jsonl` (Crawl from the initial url with the maximum number of articles to crawl = 100 and the time interval to send a request = 3s)

    - A text file "`session_wikipedia_crawler.txt`" is used to keep track of the visited urls.

    - The output cleaned text is stored in a jsonl file "`wiki_output.jsonl`".

2. "`ray-wiki-crawler.py`": Multi-processing crawling supported by ray from a start url.

    - The output is saved in Directory "`ray_wiki_output`: A text file "`session_visited_urls.txt`" to save the visited urls and `NUM_WORKERS` jsonl files "`wiki_data_{:03d}.jsonl`" where `{:03d}` is the process id.

3. "`wiki`": a scraper project using Scrapy framework to crawl wikipedia.

    - Usage: `cd ./wiki` and run `scrapy crawl wiki_math`

    - Use library pymongo to store output in the local mongodb (i.e. "mongodb://localhost:27017/").


