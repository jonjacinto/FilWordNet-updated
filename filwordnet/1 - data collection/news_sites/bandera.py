# -*- coding: utf-8 -*-
import scrapy, os
from bs4 import BeautifulSoup
from scrapy import Request
import json
from datetime import datetime

class BanderaSpider(scrapy.Spider):
    name = 'bandera'
    allowed_domains = ['bandera.inquirer.net']
    download_delay = 3
    # custom_settings = {
    #     'AUTOTHROTTLE_ENABLED': True,
    # }

    categories = ['balita', 'chika']

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
            self.start_urls = [f'https://bandera.inquirer.net/{cat}/page/{self.page}' for cat in self.categories]
        else:
            self.start_urls = [f'https://bandera.inquirer.net/{self.category}/page/{self.page}']

        if self.year == -1 or (self.week == -1 and self.month == -1):
            self.log("\n\nPlease specify the year and either the week or month.\n")
            return

        for url in self.start_urls:
            yield Request(url, dont_filter=True, cb_kwargs={'category':url.split('/')[3]})

    def parse(self, response, category):
        articles = response.css("#landing-main-default").css("#gallery-box>a::attr(href)").getall()

        date_dt = datetime.strptime(response.css("#pdate::text").extract()[0], "%B %d, %Y")
        month = date_dt.month
        year = date_dt.year
        week = int(date_dt.strftime("%W"))

        date_dt = datetime.strptime(response.css("#pdate::text").extract()[-1], "%B %d, %Y")
        last_month = date_dt.month
        last_year = date_dt.year
        last_week = int(date_dt.strftime("%W"))

        if self.year == year or self.year == last_year:
            if (month >= self.month and self.month >= last_month) or (week >= self.week and self.week >= last_week):
                yield from response.follow_all(articles, self.parse_article, cb_kwargs={'category':category})

        if year >= self.year:
            if (self.month == -1 and week >= self.week) or (self.week == -1 and month >= self.month):
                load_more_text = response.css("#bndr-prv>a::text").getall()
                load_more_url = response.css("#bndr-prv>a::attr(href)").getall()

                if len(load_more_text) == 2:
                    next_url = load_more_url[1]
                    yield response.follow(next_url, self.parse, cb_kwargs={'category':category})
                
                elif load_more_text[0] == "Next":
                    next_url = load_more_url[0]
                    yield response.follow(next_url, self.parse, cb_kwargs={'category':category})


    def parse_article(self, response, category): 
        main_landing = response.css("div#landing-main-article")
        soup = BeautifulSoup(main_landing.css("#article-content",).get(), "lxml")

        title = main_landing.css("#landing-headline>h1::text").get()
        author = main_landing.css("#m-pd2>span:nth-last-child(2)::text").get().strip() if main_landing.css("#m-pd2>span:nth-last-child(2)::text").get() else ""
        date = main_landing.css("#m-pd2>span:last-child::text").get().strip()
        full_article = "".join([par.get_text() + "\n" for par in soup.find_all("p")]).strip()
        if full_article == "":
            full_article = "".join([par.get_text() + "\n" for par in soup.find("div", id="article-content").findAll(recursive=False)[0:-1]])

        date_dt = datetime.strptime(date, "%B %d, %Y - %I:%M %p")
        month = date_dt.strftime("%m")
        year = date_dt.strftime("%Y")
        week = date_dt.strftime("%W")

        if int(month) == self.month or int(week) == self.week:
            content = {
                "title": title,
                "author": author,
                "date": date_dt.astimezone().replace(microsecond=0).isoformat(),
                "url": response.url,
                "full_article": full_article,
                "category": category,
            }
            
            post_id = response.url.split("/")[3]

            if self.week == -1:
                folder_name = f"news/{self.name}/{category}/{year}/{month}"
            else:
                folder_name = f"news/{self.name}/{category}/{year}/week {week}"

            file_name = f"{folder_name}/{post_id}.json"

            if not os.path.isdir(folder_name):
                os.makedirs(folder_name)

            with open(file_name, "w") as fl:
                json.dump(content, fl)