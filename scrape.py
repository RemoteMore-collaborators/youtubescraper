from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import lxml.html
from lxml import etree

# WINDOW_SIZE = "1920,1080"
# URL = "https://www.youtube.com/user/CandyCrushOfficial/community"
# chrome_options = Options()
# chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
# # chrome_options.add_argument("--headless")
#
# driver = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)
#
# driver.get(URL)
# element = ""
#
# print("Waiting for the page to load...")
# try:
#     element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "text")))
# finally:
#     print(element)
#
# print("Page loaded...")
# SCROLL_PAUSE_TIME = 5
#
# # Get scroll height
# """last_height = driver.execute_script("return document.body.scrollHeight")
#
# this doesn't work due to floating web elements on youtube
# """
#
# print("Scrolling through the page...")
# last_height = driver.execute_script("return document.documentElement.scrollHeight")
#
# while True:
#     # Scroll down to bottom
#     driver.execute_script("window.scrollTo(0,document.documentElement.scrollHeight);")
#
#     # Wait to load page
#     time.sleep(SCROLL_PAUSE_TIME)
#
#     # Calculate new scroll height and compare with last scroll height
#     new_height = driver.execute_script("return document.documentElement.scrollHeight")
#     if new_height == last_height:
#         print("Reached the bottom of the paginated view")
#
#         break
#     last_height = new_height
#
# view_all_comments = driver.find_elements_by_xpath('//*[@id="more"]/div/paper-button')
#
# print("Clicking through the comments section...")
# for x in range(0, len(view_all_comments)):
#     actions = ActionChains(driver)
#     element = view_all_comments[x]
#     print(f'Clicked element {x}')
#     actions.move_to_element(element).click().perform()
#     time.sleep(5)
# # Select all view comments and click them
# print("done")
# soup = BeautifulSoup(driver.page_source, "html.parser")
# driver.quit()
# with open('final.html', "w") as file:
#     file.write(str(soup))

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1PWGfQqgsbrC-WUAPCGsQgdHltQEt_MCrRqzfI37Jz_A/edit#gid=0").sheet1
data = []
with open("./final.html", 'r') as file:
    contents = file.read()

    soup = BeautifulSoup(contents, 'html.parser')
    el = soup.select(f'#contents > ytd-backstage-post-thread-renderer')
    number_of_post_section = len(el)
    print("Retrieving comments...")
    for i in range(number_of_post_section):
        post = soup.select(f'#contents > ytd-backstage-post-thread-renderer:nth-child({i + 1})')
        comments_section = post[0].select('#loaded-comments')
        comments = comments_section[0].select(f'#loaded-comments > ytd-comment-thread-renderer')
        if len(comments) > 0:
            for x in range(len(comments)):
                posted_comment = comments[x]
                author = posted_comment.select('#author-text > span')[0].text.strip()
                time_posted = posted_comment.select('#header-author > yt-formatted-string > a')[0].text.strip()
                post_content = posted_comment.select('#content-text')[0].text.strip()
                likes = posted_comment.select('#vote-count-left')[0].text.strip()
                row = [author, post_content, time_posted, likes]
                data.append(row)


for i in range(len(data)):
    print(f'Writing {data[i]} to sheet1')
    sheet.insert_row(data[i],index=2)
    if i == 100:
        time.sleep(20)
