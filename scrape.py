import csv
import time

from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains

from utils import custom_logger, paste_csv_to_wks, is_in_english
t1 = datetime.now()

CURRENT_DIR = '/home/ubuntu/youtubescraper'
#CURRENT_DIR = '.'
DRIVER_PATH = '/usr/bin'
#DRIVER_PATH = '.'
WINDOW_SIZE = "1920,1440"
URL = "https://www.youtube.com/user/CandyCrushOfficial/community"
SCROLL_PAUSE_TIME = 3
POST_TO_SCRAPE = 30

current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
filename = f'{CURRENT_DIR}/logs/scraped_{current_time}.log'

logger = custom_logger(filename)

logger.info(f'Logfile name {filename}')

# Chrome browser options - Version 79.0.3945.88 (Official Build) (64-bit)
chrome_options = Options()

chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
#chrome_options.add_argument("--disable-gpu")
#chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(executable_path=f'{DRIVER_PATH}/chromedriver', options=chrome_options)

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
all_posts = all_posts[:POST_TO_SCRAPE]
total_post_to_scrape = len(all_posts)

logger.info(f'Total number of posts {total_number_of_posts}')
logger.info(f'Total number of posts to be scraped {total_post_to_scrape}')

logger.info("Clicking through the comments section...")
# Select all view comments and click them
for x in range(POST_TO_SCRAPE):
    actions = ActionChains(driver)
    element = all_posts[x]
    logger.info(f"Clicked view comments in post {x + 1}")
    actions.move_to_element(element).click().perform()
    time.sleep(3)

logger.info("Clicking through the comments section done!")

logger.info("Retrieving comments...")

csv_written_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
filepath = f'{CURRENT_DIR}/csv/scraped_{csv_written_time}.csv'

logger.info(f'Writing comments data to {filepath}...')

with open(filepath, 'w+', encoding='utf-8') as csv_file:
    fileWriter = csv.writer(csv_file, dialect='excel')

    for i in range(POST_TO_SCRAPE):
        try:
            post_block_ = driver.find_element_by_xpath(f'(//*[@id="contents"]/ytd-backstage-post-thread-renderer)[{i + 1}]')
            post_block_ = post_block_.get_attribute('innerHTML')
        except:
            logger.error(f'Skipped post {i + 1}')
            continue

        soup = BeautifulSoup(post_block_, 'html.parser')

        post_text = soup.select('yt-formatted-string#content-text.style-scope.ytd-backstage-post-renderer')[0].text
        post_text = " ".join(post_text.split())
        post_publish_time = soup.select('yt-formatted-string#published-time-text > a')[0]
        post_publish_time_text = post_publish_time.text
        post_link = f'https://youtube.com{post_publish_time.get_attribute_list("href")[0]}'
        post_likes = soup.select('span#vote-count-middle.style-scope.ytd-comment-action-buttons-renderer')[0].text.strip()
        posted_comments = soup.select('#loaded-comments')[0].select('#main')
        video = soup.select('#content-attachment > ytd-video-renderer')

        video_link = "No video"

        if len(video) > 0:
            video_link_markup = video[0].select("#thumbnail")
            video_link = f'https://youtube.com{video_link_markup[0].get_attribute_list("href")[0]}'
        
        n = len(posted_comments)

        row = ['Candy Crush Saga Official', post_text, post_publish_time_text, post_likes, post_link]

        fileWriter.writerow(row)

        if n > 0:
            for k in range(n):
                comment_text = posted_comments[k].select('#content-text')[0].text.strip()

                if not is_in_english(comment_text):
                    continue

                author = posted_comments[k].select('#author-text > span')[0].text.strip()
                time_posted = posted_comments[k].select('#header-author > yt-formatted-string > a')[0].text.strip()
                likes = posted_comments[k].select('#vote-count-left')[0].text.strip()
                
                row = [author, comment_text, time_posted, likes, video_link]
                fileWriter.writerow(row)

        fileWriter.writerow(['', '', '', '', ''])
        logger.info(f"Parsed post {i + 1}")
        
        time.sleep(1)


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

time_diff = t2 - t1
logger.info(f"It took {time_diff} Secs to execute this method")
driver.quit()
