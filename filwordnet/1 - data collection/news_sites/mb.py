from bs4 import BeautifulSoup
import scrapy, lxml, json, os
from scrapy import Request
import json
from datetime import datetime
import requests

class MBSpider(scrapy.Spider):
    name = "mb"
    download_delay = 3
    # custom_settings = {
    #     'AUTOTHROTTLE_ENABLED': True,
    # }

    categories = ['national']

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
            self.start_urls = [f"https://mb.com.ph/category/news/{cat}/page/{self.page}" for cat in self.categories]
        else:
            self.start_urls = [f'https://mb.com.ph/category/news/{self.category}/page/{self.page}']

        if self.year == -1 or (self.week == -1 and self.month == -1):
            self.log("\n\nPlease specify the year and either the week or month.\n")
            return

        for url in self.start_urls:
            category = url.split("/")[5]
            yield Request(url, dont_filter=True, cb_kwargs={'category':category})

    def parse(self, response, category):
        soup = make_soup(response)
        articles = get_articles(soup)
        article_links = get_links(articles)
        

        dates = soup.find("div", attrs={"class": "articles"}).findAll("time", attrs={"class": "time-ago"})
        date_dt = datetime.strptime(dates[0].get("data-time").split(" ")[0], "%Y-%m-%d")
        month = date_dt.month
        year = date_dt.year
        week = int(date_dt.strftime("%W"))

        date_dt = datetime.strptime(dates[-1].get("data-time").split(" ")[0], "%Y-%m-%d")
        last_month = date_dt.month
        last_year = date_dt.year
        last_week = int(date_dt.strftime("%W"))

        if self.year == year or self.year == last_year:
            if (month >= self.month and self.month >= last_month) or (week >= self.week and self.week >= last_week):
                yield from response.follow_all(article_links, self.parse_article, cb_kwargs={'category':category})

        if year >= self.year:
            if (self.month == -1 and week >= self.week) or (self.week == -1 and month >= self.month):
                page = int(response.meta['redirect_urls'][0].split('/')[7]) + 1
                url = f"https://mb.com.ph/category/news/{category}/page/{page}"   
                yield response.follow(url, self.parse, cb_kwargs={'category':category})

    def parse_article(self, response, category):
        soup = make_soup(response)
        content = get_content(soup)

        author = " ".join(get_author(soup).split(" ")[1:])
        date = get_date(soup)
        tags = get_tags(soup)

        headline = get_headline(soup)
        text = get_text_content(soup)
        post_id = get_post_id(response.url)

        date_dt = datetime.strptime(date, "Published %B %d, %Y, %I:%M %p")
        month = date_dt.strftime("%m")
        year = date_dt.strftime("%Y")
        week = date_dt.strftime("%W")

        if int(month) == self.month or int(week) == self.week:
            content = {
                "title": headline,
                "author": author,
                "date": date_dt.astimezone().replace(microsecond=0).isoformat(),
                "tags": tags,
                "url": response.url,
                "full_article": text,
                "category": category,
            }

            post_id = "-".join(post_id.split('-')[0:3])

            if self.week == -1:
                folder_name = f"news/{self.name}/{category}/{year}/{month}"
            else:
                folder_name = f"news/{self.name}/{category}/{year}/week {week}"

            file_name = f"{folder_name}/{date_dt}-{post_id}.json"
            file_name = file_name.replace(":", "_")

            if not os.path.isdir(folder_name):
                os.makedirs(folder_name)

            with open(file_name, "w") as fl:
                json.dump(content, fl)


def make_soup(response):
    return BeautifulSoup(response.body, "lxml")


def get_articles(soup):
    # return soup.find("div", class_="col-9 content").find_all("p", class_="title")
    return soup.find("div", attrs={"class": "articles"}).find_all("h4", attrs={"class": "title"})


def get_links(articles):
    return [x.find("a")["href"] for x in articles]


def get_content(soup):
    return soup.find("section", attrs={"class": "article-content"})

def get_author(soup):
    return soup.find("p", attrs={"class": "author"}).find("a").get_text().strip()


def get_date(soup):
    return soup.find("p", attrs={"class": "published"}).get_text().strip()

def get_tags(soup):
    if (soup.find("ul", attrs={"class": "list col-12 col-md d-flex flex-wrap"})):
        tags = soup.find("ul", attrs={"class": "list col-12 col-md d-flex flex-wrap"}).find_all("a")
        return [x.get_text().strip() for x in tags]
    else:
        return ""


def get_text_content(content):
    paragraphs = content.find("section", attrs={"class": "article-content"}).find_all("p")
    text = ""
    for x in paragraphs:
            text += x.get_text().strip() + "\n"
    return text[:-2]

def get_headline(soup):
    return soup.find("h2", attrs={"class": "title"}).get_text().strip()


def get_post_id(soup):
    return soup.split('/')[6]