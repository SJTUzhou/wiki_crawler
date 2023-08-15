import scrapy
import bs4
from bs4 import BeautifulSoup
import re
from ..items import WikiItem


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
                x = extract_text_with_math(content)
                if x:
                    extracted_text += x
    
        return extracted_text





class WikiMathSpider(scrapy.Spider):
    name = "wiki_math"
    allowed_domains = ["en.wikipedia.org"]
    base_url = "https://en.wikipedia.org"
    start_url = "https://en.wikipedia.org/wiki/Mathematics"
    

    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }
    custom_settings = {"ITEM_PIPELINES" : {
                        "wiki.pipelines.WikiMongoDBPipeline": 500 # 保存到本地mongodb
                        }
                    }

    def start_requests(self):
        
        yield scrapy.Request(self.start_url, headers=self.default_headers, callback=self.parse, errback=self.parse_error)


    def parse(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find('div', {'id':'mw-content-text'})
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
                yield scrapy.Request(self.base_url+href, headers=self.default_headers, callback=self.parse, errback=self.parse_error)

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
            
            _key = response.url.split('/wiki/')[-1]
            print(_key)
            yield WikiItem({"key":_key, "url": response.url, "text": out_text})

        except Exception as e:
            self.logger.error(repr(e))
            self.logger.error(f"Failed to parse {response.url}")


    def parse_error(self, failure):
        # log all failures
        self.logger.error(repr(failure))
        


