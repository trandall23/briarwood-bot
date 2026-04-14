import os
import time
import pytz
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
USER = os.getenv("USER")
PASS = os.getenv("PASS")
WANTED_TIME = os.getenv("TARGET_TIME") 

def book():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. LOGIN
        print("Logging into Briarwood...")
        driver.get("https://www.briarwoodgolfclub.org/login.aspx")
        
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        time.sleep(5)

        # 2. JUMP TO SHEET
        print("Navigating to Tee Sheet...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. DATE SETUP
        tz = pytz.timezone('US/Central')
        # CHANGE TO days=7 FOR THE REAL RUN
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") 

        # TIMER (Uncomment the 3 lines below for the 7:00 AM run)
        # print("Waiting for 7:00:00 AM CST...")
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #     time.sleep(0.1)

        # 4. IFRAME HANDLING
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"Switching to interactive frame...")
            driver.switch_to.frame(iframes[0])

        # 5. SET DATE
        print(f"Setting date to {target_date}...")
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDate")))
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        time.sleep(3)

        # 6. CLICK RESERVE
        print(f"Searching for {WANTED_TIME}...")
        xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]"
        
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", btn)
        print("SUCCESS: Reserve button clicked!")

        # 7. FINAL CONFIRMATION
        time.sleep(2)
        try:
            finish = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", finish)
            print("BOOKING CONFIRMED")
        except:
            print("Manual confirmation may be needed.")

    except Exception as e:
        print(f"Bot failed at: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
