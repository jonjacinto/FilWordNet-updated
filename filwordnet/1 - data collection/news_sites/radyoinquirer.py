from bs4 import BeautifulSoup
import scrapy, lxml, json, os
from scrapy import Request
from datetime import datetime
import json

class RadyoInquirerSpider(scrapy.Spider):
    name = "radyoinquirer"
    download_delay = 3
    # custom_settings = {
    #     'AUTOTHROTTLE_ENABLED': True,
    # }

    categories = ["latest-news", "national", "metro", "provincial", "entertainment", "sports", "column", "lifestyle", "business"]

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
            self.start_urls = [f"https://radyo.inquirer.net/category/{cat}/page/{self.page}" for cat in self.categories]
        else:
            self.start_urls = [f'https://radyo.inquirer.net/category/{self.category}/page/{self.page}']
        
        if self.year == -1 or (self.week == -1 and self.month == -1):
            self.log("\n\nPlease specify the year and either the week or month.\n")
            return

        for url in self.start_urls:
            category = url.split('/')[4]
            yield Request(url, dont_filter=True, cb_kwargs={'category':category})

    def parse(self, response, category):
        soup = make_soup(response)
        articles = get_articles(soup)
        article_links = get_links(articles)

        dates = soup.findAll("div", attrs={"id": "postdate-byline"})
        date_dt = datetime.strptime(dates[0].findAll("span")[-1].get_text().strip(), "%m/%d/%Y")
        month = date_dt.month
        year = date_dt.year
        week = int(date_dt.strftime("%W"))

        date_dt = datetime.strptime(dates[-1].findAll("span")[-1].get_text().strip(), "%m/%d/%Y")
        last_month = date_dt.month
        last_year = date_dt.year
        last_week = int(date_dt.strftime("%W"))

        if self.year == year or self.year == last_year:
            if (month >= self.month and self.month >= last_month) or (week >= self.week and self.week >= last_week):
                yield from response.follow_all(article_links, self.parse_article, cb_kwargs={'category':category})

        if year >= self.year:
            if (self.month == -1 and week >= self.week) or (self.week == -1 and month >= self.month):
                next_url = soup.find("div", id="cdn-section-pages").find("div", id="cdn-pages-left").find("div", id="pages-nav").find_all("a")
                next_url = next_url[len(next_url) - 1]

                if next_url.get_text() == "Next":
                    yield response.follow(next_url['href'], self.parse, cb_kwargs={'category': category})

    def parse_article(self, response, category):
        soup = make_soup(response)
        content = get_content(soup)

        headline = get_headline(content)
        text = get_text_content(content)
        date = get_date(content)
        #tags = get_tags(soup)
        author = get_author(soup)

        date_dt = datetime.strptime(date.strip(), "%Y-%m-%d %H:%M:%S")
        month = date_dt.strftime("%m")
        year = date_dt.strftime("%Y")
        week = date_dt.strftime("%W")

        if int(month) == self.month or int(week) == self.week:
            content = {
                "category": category,
                "title": headline,
                "author": author,
                "date": date_dt.astimezone().replace(microsecond=0).isoformat(),
                # "tags": tags,
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
    return soup.find("div", id="cdn-section-pages").find_all("div", id="pages-box")


def get_links(articles):
    return [x.find("a")["href"] for x in articles]


def get_content(soup):
    return soup.find("div",
                     attrs={
                         "id": "article-content-wrap"
                     }).find("div",
                             attrs={"id": "landing-main-article"})


def get_author(soup):
    string = soup.find("div", attrs={"id": "landing-headline"}).find("div", attrs={"id": "m-pd2"}).find_all("span")
    if len(string) > 1:
        return soup.find("div", attrs={"id": "landing-headline"}).find("div", attrs={"id": "m-pd2"}).find_all("span")[0].get_text().strip().split("By ", 1)[1]
    return ""

def get_date(soup):
    time = soup.find("div", attrs={"id": "landing-headline"}).find("div", attrs={"id": "m-pd2"}).find_all("span")[-1].get_text().strip()
    return datetime.strptime(time, "%B %d, %Y - %I:%M %p").strftime("%Y-%m-%d %H:%M:%S")



def get_tags(soup):
    tags = soup.find_all("a", attrs={"rel": "tag"})
    return [x.get_text().strip() for x in tags]


def get_text_content(content):
    paragraphs = content.find("div", attrs={"id": "article-content"}).find_all("p")
    text = ""
    for x in paragraphs:
        text += x.get_text() + " "
    return text[:-2]


def get_headline(content):
    return content.find("div", attrs={"id": "landing-headline"}).find("h1").get_text().strip()


def get_post_id(soup):
    return "-".join(soup.split('/')[4].split('-')[0:3])