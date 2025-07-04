from bs4 import BeautifulSoup
import scrapy, json, os
from scrapy import Request
import json
from datetime import datetime


class AbanteSpider(scrapy.Spider):
    name = "abante"
    download_delay = 3
    # custom_settings = {
    #     'AUTOTHROTTLE_ENABLED': True,
    # }

    categories = ["news", "ent", "sports3", "op", "metro", "lifestyle", "vismin2"]

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
            self.start_urls = [f'https://www.abante.com.ph/category/{cat}/page/{self.page}' for cat in self.categories]
        else:
            self.start_urls = [f'https://www.abante.com.ph/category/{self.category}/page/{self.page}']
    

        #if self.year == -1 or (self.week == -1 and self.month == -1):
        if self.year == -1 and self.week == -1 and self.month == -1:
            self.log("\n\nPlease specify the year and either the week or month.\n")
            return
        
        for url in self.start_urls:
            yield Request(url, dont_filter=True, cb_kwargs={'category': url.split('/')[4]})

    def parse(self, response, category):
        soup = make_soup(response)
        articles = get_articles(soup)
        article_links = get_links(articles)
        article_dates = get_dates(soup)

        date_dt = datetime.strptime(article_dates[0].split("T")[0], "%Y-%m-%d")
        month = date_dt.month
        year = date_dt.year
        week = int(date_dt.strftime("%W"))

        date_dt = datetime.strptime(article_dates[-1].split("T")[0], "%Y-%m-%d")
        last_month = date_dt.month
        last_year = date_dt.year
        last_week = int(date_dt.strftime("%W"))

        if self.year == year or self.year == last_year:
            if (self.month == -1 and self.week == -1) or (month >= self.month and self.month >= last_month) or (week >= self.week and self.week >= last_week):
                yield from response.follow_all(article_links, self.parse_article, cb_kwargs={'date_dict': dict(zip(article_links, article_dates)), 'category': category})
        
        if year >= self.year:
            if (self.month == -1 and self.week == -1) or (self.month == -1 and week >= self.week) or (self.week == -1 and month >= self.month):
                next_url = soup.find("div", class_="older").find("a")

                if next_url:
                    yield response.follow(next_url['href'], self.parse, cb_kwargs={'category': category})
    
    def parse_article(self, response, date_dict, category):
        soup = make_soup(response)
        content = get_content(soup)

        headline = get_headline(soup)
        text = get_text_content(content)
        date = date_dict[response.url]
        tags = get_tags(soup)
        author = get_author(soup)

        date_dt = datetime.strptime(date.split("T")[0], "%Y-%m-%d")
        month = date.split("-")[1]
        year = date.split("-")[0]
        week = date_dt.strftime("%W")

        if (self.month == -1 and self.week == -1 and self.year == int(year)) or int(month) == self.month or int(week) == self.week:
            content = {
                "category": category,
                "title": headline,
                "author": author,
                "date": date,
                "tags": tags,
                "url": response.url,
                "full_article": text,
            }

            post_id = date.replace(':', '_') + '-' + get_post_id(response.url)
            
            if self.week == -1:
                folder_name = f"news/{self.name}/{category}/{year}/{month}"
            else:
                folder_name = f"news/{self.name}/{category}/{year}/week {week}"

            file_name = f"{folder_name}/{post_id}.json"

            if not os.path.isdir(folder_name):
                os.makedirs(folder_name)

            with open(file_name, "w") as fl:
                json.dump(content, fl)


def make_soup(response):
    return BeautifulSoup(response.body, "lxml")


def get_articles(soup):
    return soup.find("main", id="content").find(
        "div", class_="row main-section").find_all("h2", class_="title")


def get_links(articles):
    return [x.find("a")["href"] for x in articles]


def get_content(soup):
    return soup.find("div",
                     attrs={
                         "class": "entry-content clearfix single-post-content"
                     }).find("div",
                             attrs={"class": "continue-reading-content close"})


# def remove_related_posts(content):
#     related = content.find_all(class_=["breadcrumb-block", "author-block","news-share-block"])
#     for x in related: x.decompose()
#     return content

def get_author(soup):
    return soup.find("span", attrs={
        "class": "post-author-name"
    }).find("b").get_text().strip()


def get_dates(soup):
    times = soup.find("div", class_="row main-section").find(
        "div",
        class_="col-sm-8 content-column").find_all("span",
                                                   attrs={"class": "time"})
    return [
        time.find("time", attrs={
            "class": "post-published updated"
        }).get('datetime').strip() for time in times
    ]


def get_tags(soup):
    tags = soup.find_all("a", attrs={"rel": "tag"})
    return [x.get_text().strip() for x in tags]


def get_text_content(content):
    paragraphs = content.find_all("p", attrs={"class": None})
    text = ""
    for x in paragraphs:
        text += x.get_text() + " "
    return text[:-1]


def get_headline(soup):
    return soup.find("span", attrs={"class": "post-title"}).get_text().strip()


def get_post_id(soup):
    return "-".join(soup.split('/')[3].split('-')[0:3])