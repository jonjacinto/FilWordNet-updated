from bs4 import BeautifulSoup
import scrapy, lxml, json, os
from scrapy import Request
import json
from datetime import datetime

#from drive_uploader.news_uploader import NewsUploader


class AbsSpider(scrapy.Spider):
    name = "abscbn"
    download_delay = 5
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
    }

    categories = ['tagalog-news']
    
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
            self.start_urls = [f"https://news.abs-cbn.com/patrol/tag/{cat}?page={self.page}" for cat in self.categories]
        else:
            self.start_urls = [f'https://news.abs-cbn.com/patrol/tag/{self.category}?page={self.page}']

        for url in self.start_urls:
            yield Request(url, dont_filter=True)

    def parse(self, response):
        soup = make_soup(response)
        articles = get_articles(soup)
        article_links = get_links(articles)

        date_dt = datetime.strptime("/".join(article_links[0].split("/")[-4:-1]), "%m/%d/%y")
        month = date_dt.month
        year = date_dt.year
        week = int(date_dt.strftime("%W"))

        date_dt = datetime.strptime("/".join(article_links[-1].split("/")[-4:-1]), "%m/%d/%y")
        last_month = date_dt.month
        last_year = date_dt.year
        last_week = int(date_dt.strftime("%W"))

        if self.year == year or self.year == last_year:
            if (month >= self.month and self.month >= last_month) or (week >= self.week and self.week >= last_week):
                yield from response.follow_all(article_links, self.parse_article)
        
        if year >= self.year:
            page = int(response.url.split('=')[1])
            if page < 11:
                url = "https://news.abs-cbn.com/patrol/tag/tagalog-news?page=" + str(page + 1)   
                yield response.follow(url, self.parse)

    def parse_article(self, response):
        soup = make_soup(response)
        content = get_content(soup)

        author = get_author(soup)
        date = get_date(soup)
        tags = get_tags(soup)

        headline = get_headline(soup)
        text = get_text_content(content)
        post_id = get_post_id(response.url)
        category = get_category(soup).lower()

        date_dt = datetime.strptime(date, "%b %d %Y %I:%M %p")
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
                "category": category
            }

            final_post_id = str(date_dt).replace(":", "_") + '-' + "-".join(post_id.split('-')[0:3])

            if self.week == -1:
                folder_name = f"news/{self.name}/{category}/{year}/{month}"
            else:
                folder_name = f"news/{self.name}/{category}/{year}/week {week}"

            file_name = f"{folder_name}/{final_post_id}.json"

            if not os.path.isdir(folder_name):
                os.makedirs(folder_name)

            with open(file_name, "w") as fl:
                json.dump(content, fl)


def get_page(soup):
    return soup.find("a", class_="page current")


def make_soup(response):
    return BeautifulSoup(response.body, "lxml")


def get_articles(soup):
    # return soup.find("div", class_="col-9 content").find_all("p", class_="title")
    return soup.find_all("p", class_="title")


def get_links(articles):
    return [x.find("a")["href"] for x in articles]


def get_content(soup):
    if (soup.find("div", attrs={"class": "article-content"})):
        return soup.find("div", attrs={"class": "article-content"})
    else:
        return soup.find("div", attrs={"class": "media-block video"})


def get_author(soup):
    return soup.find("span", attrs={"class": "editor"}).get_text().strip()


def get_date(soup):
    return soup.find("span", attrs={"class": "date-posted"}).get_text().strip()


def get_tags(soup):
    metakey = soup.find("div", attrs={"class": "article-metakey"})
    tags = metakey.find_all("a")
    return [x.get_text().strip() for x in tags]


def get_text_content(content):
    paragraphs = content.find_all("p")
    text = ""
    for x in paragraphs:
        text += x.get_text().strip() + "\n"
    return text


def get_headline(soup):
    return soup.find("h1", attrs={"class": "news-title"}).get_text().strip()


def get_post_id(soup):
    return soup.split('/')[-1]

def get_category(soup):
    return soup.find("div", attrs={"class":"breadcrumb-block"}).find_all("a")[1].get_text()