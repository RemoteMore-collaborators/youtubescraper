import csv
import time
import memory_profiler

from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains

from utils import custom_logger, paste_csv_to_wks, is_in_english
m1 = memory_profiler.memory_usage()
t1 = datetime.now()

# CURRENT_DIR = '/home/ubuntu/youtubescraper'
CURRENT_DIR = '.'
WINDOW_SIZE = "1920,1440"
URL = "https://www.youtube.com/user/CandyCrushOfficial/community"
SCROLL_PAUSE_TIME = 5

current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
filename = f'{CURRENT_DIR}/logs/scraped_{current_time}.log'

logger = custom_logger(filename)

logger.info(f'Logfile name {filename}')

# Chrome browser options - Version 79.0.3945.88 (Official Build) (64-bit)
chrome_options = Options()

chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)

driver.get(URL)

logger.info("Waiting for the page to load...")
try:
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "text")))
except TimeoutException as err:
    logger.error("Something went wrong, check your internet connection")
    exit()

logger.info("Page loaded...")

# Get scroll height
logger.info("Scrolling through the page...")
last_height = driver.execute_script("return document.documentElement.scrollHeight")

while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0,document.documentElement.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.documentElement.scrollHeight")
    if new_height == last_height:
        logger.info("Reached the bottom of the paginated view")
        break
    last_height = new_height

all_posts = driver.find_elements_by_xpath('//*[@id="more"]/div/paper-button')
total_number_of_posts = len(all_posts)

logger.info(f'Total number of posts {total_number_of_posts}')

logger.info("Clicking through the comments section...")
# Select all view comments and click them
for x in range(total_number_of_posts):
    actions = ActionChains(driver)
    element = all_posts[x]
    logger.info(f"Clicked view comments in post {x + 1}")
    actions.move_to_element(element).click().perform()
    time.sleep(3) 

logger.info("Clicking through the comments section done!")

try:
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
except Exception as err:
    logger.error(err)
    exit()

logger.info("Retrieving comments...")


def parse_posts(soup):
    post_block = len(soup.select('#contents > ytd-backstage-post-thread-renderer'))

    for i in range(post_block):
        post = soup.select(f'#contents > ytd-backstage-post-thread-renderer:nth-child({i + 1})')
        post_text = post[0].select('yt-formatted-string#content-text.style-scope.ytd-backstage-post-renderer')[0].text.strip()
        post_publish_time = post[0].select('yt-formatted-string#published-time-text > a')[0]
        post_publish_time_text = post_publish_time.text
        post_link = f'https://youtube.com{post_publish_time.get_attribute_list("href")[0]}'
        post_body = soup.select('div#main.style-scope.ytd-backstage-post-renderer')
        post_likes = post_body[i].select('span#vote-count-middle.style-scope.ytd-comment-action-buttons-renderer')[0].text.strip()
        comment = post[0].select('#loaded-comments')[0].select('#main')
        video = post[0].select('#content-attachment > ytd-video-renderer')
        video_link = "No video"

        if len(video) > 0:
            video_link_markup = video[0].select("#thumbnail")
            video_link = f'https://youtube.com{video_link_markup[0].get_attribute_list("href")[0]}'

        video_and_comment = [post_text, post_publish_time_text, post_link, post_likes, video_link, comment]
        yield(video_and_comment)

posts = parse_posts(soup)

# Getting all the comments and videos

csv_written_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
filepath = f'{CURRENT_DIR}/csv/scraped_{csv_written_time}.csv'

logger.info(f'Writing comments data to {filepath}...')

with open(filepath, 'w', encoding='utf-8') as csv_file:
    fileWriter = csv.writer(csv_file, dialect='excel')
    
    for post in posts:
        post_text = post[0]
        post_publish_time = post[1]
        post_link = post[2]
        post_likes = post[3]
        video_link = post[-2]
        posted_comments = post[-1]
        n = len(posted_comments)

        row = ['Candy Crush Saga Official', post_text, post_publish_time, post_likes, post_link]
        fileWriter.writerow(row)

        if n > 0:
            for k in range(n):
                comment_text = posted_comments[k].select('#content-text')[0].text.strip()

                if not is_in_english(comment_text):
                    logger.info(f"'{comment_text}' is not english")
                    continue

                author = posted_comments[k].select('#author-text > span')[0].text.strip()
                time_posted = posted_comments[k].select('#header-author > yt-formatted-string > a')[0].text.strip()
                likes = posted_comments[k].select('#vote-count-left')[0].text.strip()
                
                row = [author, comment_text, time_posted, likes, video_link]
                fileWriter.writerow(row)

        fileWriter.writerow(['', '', '', '', ''])

logger.info("Retrieving comments complete!")

logger.info('Writing complete!')

logger.info('Writing to "Youtube Scraping" googlesheets')
 
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(f'{CURRENT_DIR}/client_secret.json', scope)

gc = gspread.authorize(credentials)
wks = gc.open("Youtube scraping")
paste_csv_to_wks(filepath, wks, 'A2', logger)

logger.info('Writing to googlesheets complete!')

t2 = datetime.now()
m2 = memory_profiler.memory_usage()

time_diff = t2 - t1
mem_diff = m2[0] - m1[0]
logger.info(
    f"It took {time_diff} Secs and {mem_diff} Mb to execute this method")