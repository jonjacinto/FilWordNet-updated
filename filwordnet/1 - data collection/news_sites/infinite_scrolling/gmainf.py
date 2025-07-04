from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import json

# Global dictionary to store URLs
URLS = {}

# Change chromedriver path accordingly
# TODO: Ask adrian how to change this for cloud hosting
chrome_path = "//Users/MacBookAir/Desktop/CPROG/robot/chromedriver"
driver = webdriver.Chrome(chrome_path)

# Make sure components are visible
driver.maximize_window()
# Base URL
driver.get("https://www.gmanetwork.com/news/archives/just_in/")
# Scroll down
driver.execute_script("window.scrollTo(0, 746)")

# Start from 2008
# TODO: XPATH String builder for year
year = driver.find_element_by_xpath("""//*[@id="year-2008"]""")
year.click()
yr = year.get_attribute("id")[-4:]
time.sleep(2)

# Iterate all the months
months = driver.find_elements_by_css_selector(
    "#ui-accordion-accordion-panel-13 > ul > li")

wait = WebDriverWait(driver, 10)

for month in months:
    # print(month.get_attribute('data-value').capitalize() + " " + year.get_attribute('id').split('-')[-1])
    driver.execute_script("arguments[0].click();", month)
    name = month.get_attribute('data-value').capitalize(
    ) + " " + year.get_attribute('id').split('-')[-1]
    wait.until(
        EC.text_to_be_present_in_element(
            (By.XPATH, '//*[@id="grid_thumbnail_stories"]/h3'), name))

    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".story_link")))

    articles = driver.find_elements_by_css_selector(".story_link")
    links = [article.get_attribute('href') for article in articles]

    name = month.get_attribute('data-value').capitalize() + " " + yr
    print(links)
    URLS[name] = links
    time.sleep(5)

print(URLS)

for key, month_links in URLS.items():
    print(key)
    for i in month_links:  # Enumerate gives the index and value.
        driver.get(i)
        try:
            header = driver.find_element_by_css_selector("header h1").text
            timestamp = driver.find_element_by_css_selector(
                "time").get_attribute("datetime")
            tags = driver.find_elements_by_css_selector(".automatic_tags > a")
            tags = [tag.text for tag in tags]

            content = driver.find_element_by_css_selector(".story_main").text

            obj = {
                "headline": header,
                "date": timestamp,
                "tags": tags,
                "url": i,
                "full_article": content,
            }

            parsed_headline = header.replace(" ", "-")
            file_name = f"news/gma/[{timestamp}] {parsed_headline}.json"
            print(file_name)

            # if not os.path.isdir("news/gma/"):
            #     os.makedirs("news/gma/")

            # with open(file_name, "w") as fl:
            #     json.dump(content, fl)

            time.sleep(3)
        except NoSuchElementException:
            continue