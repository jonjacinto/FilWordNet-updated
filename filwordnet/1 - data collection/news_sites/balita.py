# -*- coding: utf-8 -*-
import scrapy, os, lxml
from bs4 import BeautifulSoup
from scrapy import Request
import json
from datetime import datetime

class BanderaSpider(scrapy.Spider):
    name = 'balita'
    download_delay = 0.5
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
    }

    categories = ['balita-archive', 'balita-main', 'features', 'showbiz-2', 'sports']
    
    # DEFAULT PARAMETERS
    category = categories[0]
    month = -1
    year = -1
    week = -1
    page = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start_requests(self):
        self.week = int(self.week)
        self.month = int(self.month)
        self.year = int(self.year)

        if self.category == "all":
            self.start_urls = [f'https://balita.net.ph/category/{cat}/page/{self.page}' for cat in self.categories]
        else: 
            self.start_urls = [f'https://balita.net.ph/category/{self.category}/page/{self.page}']

        if self.year == -1 or (self.week == -1 and self.month == -1):
            self.log("\n\nPlease specify the year and either the week or month.\n")
            return
        
        for url in self.start_urls:
            yield Request(url, dont_filter=True, cb_kwargs={'category': url.split('/')[4]})

    def parse(self, response, category):
        articles = response.css("div.jeg_posts.jeg_load_more_flag").css("h3.jeg_post_title").css("a::attr(href)").getall()
        
        date_dt = datetime.strptime("/".join(articles[0].split("/")[3:6]), "%Y/%m/%d")
        month = date_dt.month
        year = date_dt.year
        week = int(date_dt.strftime("%W"))

        date_dt = datetime.strptime("/".join(articles[-1].split("/")[3:6]), "%Y/%m/%d")
        last_month = date_dt.month
        last_year = date_dt.year
        last_week = int(date_dt.strftime("%W"))

        if self.year == year or self.year == last_year:
            if (month >= self.month and self.month >= last_month) or (week >= self.week and self.week >= last_week):
                yield from response.follow_all(articles, self.parse_article, cb_kwargs={'category':category})

        if year >= self.year:
            next_url = response.css("a.page_nav.next::attr(href)").get()
            if next_url:
                yield response.follow(next_url, self.parse, cb_kwargs={'category':category})

    def parse_article(self, response, category): 
        soup = BeautifulSoup(response.css("div.content-inner",).get(), "lxml")
        
        # remove dividers in soup
        for match in soup.find('div', class_='content-inner').findAll('div'):
            match.decompose()

        title = response.css("h1.jeg_post_title::text").get()
        tags = response.css('div.jeg_post_tags').css('a::text').getall()
        full_article = "".join([par.get_text() + "\n" for par in soup]).strip()

        date_dt = datetime.strptime("-".join(response.url.split('/')[3:6]), '%Y-%m-%d')
        date = date_dt.strftime('%Y-%m-%d')
        month = date_dt.strftime("%m")
        year = date_dt.strftime("%Y")
        week = date_dt.strftime("%W")

        if int(month) == self.month or int(week) == self.week:
            content = {
                "title": title,
                "date": date_dt.astimezone().replace(microsecond=0).isoformat(),
                "tags": tags,
                "url": response.url,
                "full_article": full_article,
                "category": category
            }
            
            post_id = date + '-' + "-".join(response.url.split("/")[-2].split("-")[0:4])

            if self.week == -1:
                folder_name = f"news/{self.name}/{category}/{year}/{month}"
            else:
                folder_name = f"news/{self.name}/{category}/{year}/week {week}"

            file_name = f"{folder_name}/{post_id}.json"

            if not os.path.isdir(folder_name):
                os.makedirs(folder_name)

            with open(file_name, "w") as fl:
                json.dump(content, fl)