import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
URL_TO_OPEN = "https://wurstliga.onrender.com/"
WAIT_SECONDS_AFTER_OPEN = 5  # How long to keep the browser open (optional)
RUN_HEADLESS = True # Set to True to run Chrome without a visible window

# --- Setup WebDriver ---
options = Options()
if RUN_HEADLESS:
    options.add_argument('--headless')
    options.add_argument('--disable-gpu') # Often needed for headless mode
    options.add_argument('--window-size=1920x1080') # Specify window size

# Use webdriver-manager to automatically handle the ChromeDriver
# It will download/update the driver if needed and cache it.
service = Service(ChromeDriverManager().install())

driver = None # Initialize driver variable

# --- Main Logic ---
try:
    print(f"[{datetime.datetime.now()}] Starting WebDriver...")
    driver = webdriver.Chrome(service=service, options=options)
    print(f"[{datetime.datetime.now()}] WebDriver started. Opening URL: {URL_TO_OPEN}")
    driver.get(URL_TO_OPEN)
    print(f"[{datetime.datetime.now()}] Successfully opened URL. Waiting for {WAIT_SECONDS_AFTER_OPEN} seconds...")
    time.sleep(WAIT_SECONDS_AFTER_OPEN)
    print(f"[{datetime.datetime.now()}] Wait finished.")

except Exception as e:
    print(f"[{datetime.datetime.now()}] An error occurred: {e}")

finally:
    # Ensure the browser is closed even if an error occurred
    if driver:
        print(f"[{datetime.datetime.now()}] Closing WebDriver.")
        driver.quit()
    print(f"[{datetime.datetime.now()}] Script finished.")