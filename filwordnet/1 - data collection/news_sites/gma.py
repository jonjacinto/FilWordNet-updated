# -*- coding: utf-8 -*-
import scrapy, json, os
from bs4 import BeautifulSoup
from scrapy import Request
#from drive_uploader.news_uploader import NewsUploader
from langdetect import detect
from scrapy import signals
import json


class GmaSpider(scrapy.Spider):

    name = 'gma'
    start_urls = [
        'https://data2.gmanetwork.com/gno/widgets/grid_reverse_listing/story_news_ulatfilipino/50'
    ]

    def __init__(self):
        super()
        # shar - commented this out para di ma-upload kina blaise
        # self.news_uploader = NewsUploader()
        # self.news_uploader.assign_folder("1dEdIDarT1pYeL0oRe6nm5fK520l_fuk9")
        self.nontl = 0

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        spider.logger.info('Spider Closed: %s', spider.name)
        spider.logger.info('Total non-tagalog articles: %s', spider.nontl)

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, dont_filter=True, meta={"page_number": 1})

    def parse(self, response):
        def produce_article_url(post_id):
            return "https://data2.gmanews.tv/%s/gno/story/%s" % (
                post_id[:-4:-1], post_id)

        json_article = json.loads(response.text)

        articles = [
            produce_article_url(article["id"])
            for article in json_article["data"]
        ]

        yield from response.follow_all(articles, self.parse_article)

        page_number = response.meta["page_number"]

        next_url = json_article["next_url"]
        yield response.follow(next_url,
                              self.parse,
                              meta={"page_number": page_number + 1})

    # def get_date(soup):
    #     return soup.find("span", attrs={
    #         "class": "article-time"
    #     }).get_text().strip()

    def parse_article(self, response):
        json_content = json.loads(response.text)
        #self.log(json_content)
        headline = json_content["title"].split('|')[0].strip()

        post_id = json_content["story"]["id"]

        date = json_content["story"]["postDate"]

        timestamp = json_content["story"]["timestamp"]

        tags = json_content["all_tags"]

        html_content = json_content["story"]["main"]
        soup = BeautifulSoup(html_content, 'lxml')
        for br in soup.find_all("br"):
            br.replace_with("\n")
        full_article = soup.get_text()

        self.log(post_id)
        self.log(headline)
        #self.log(full_article)
        self.log(date)
        self.log(tags)
        self.log(timestamp)

        content = {
            "title": headline,
            "date": date,
            "timestamp": timestamp,
            "full_article": full_article,
            "url": response.url
        }

        file_name = 'news/gma/%s.json' % post_id

        if not os.path.isdir("news/gma"):
            os.makedirs("news/gma")

        if detect(full_article) == 'tl':
            with open(file_name, "w") as fl:
                json.dump(content, fl)

            #self.news_uploader.upload(file_name, post_id)

            os.remove(file_name)

        else:
            self.log("THIS IS NOT TAGALOG")
            self.nontl += 1
