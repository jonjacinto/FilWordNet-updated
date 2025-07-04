from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import json
import os

# Global dictionary to store URLs
category = "drlove"
# Change to Source Path
path = "/Users/MacBookAir/Documents/DLSU/Thesis"
# Change chromedriver path accordingly
chrome_path = "//Users/MacBookAir/Desktop/CPROG/robot/chromedriver"
driver = webdriver.Chrome(chrome_path)

# Make sure components are visible
driver.maximize_window()
# Base URL
driver.get("https://www.philstar.com/pilipino-star-ngayon/dr-love")
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(4)
print("Scroll Down")
for i in range(1, 2):
    print("Scroll Up")
    driver.execute_script("window.scrollTo(0, -50);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(4)

html_source = driver.page_source
soup = BeautifulSoup(html_source, "html.parser")

for article in soup.find_all("div", {"class": "microsite_article"}):
    section = article.find("div", {"class": "microsite_article_section"})

    if section is None:
        continue

    if "Dr. Love" in section.getText():
        article_head = article.find("div",
                                    {"class": "microsite_article_title"})
        # print(article_head)
        title = article_head.getText().replace('\n', '')
        link = article_head.find("a")['href']
        summary = article.find("div", {
            "class": "microsite_article_summary"
        }).getText().replace('\n', '').strip()
        date = article.find("div", {
            "class": "microsite_article_date"
        }).getText().replace('\n', '').strip()

        print("TITLE: " + title)
        print("LINK: " + link)
        print("SUMMARY: " + summary)
        print("DATE: " + date)

        obj = {
            "headline": title,
            "url": link,
            "description": summary,
            "date": date,
        }

        filename = title.replace(" ", "-") + ".json"
        print(filename)

        if not os.path.isdir(path + "/news/news/spiders/news/philstar/" + category):
            os.makedirs(path + "news/love/" + category)

        save_path = path + "/news/news/spiders/news/philstar/" + category+"/"+ filename
        with open(save_path, "w") as fl:
            json.dump(obj, fl)

