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
    # Makes the bot look like a real person
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25) # Give it 25 seconds to find things
    
    try:
        # 1. LOGIN STARTING FROM HOME
        print("Opening Briarwood Home...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        
        print("Searching for login boxes...")
        user_field = wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername")))
        user_field.send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO SHEET
        time.sleep(7)
        print("Navigating to Tee Sheet...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. DATE SETUP
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") 

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
        time.sleep(4)

        # 6. CLICK RESERVE
        print(f"Searching for {WANTED_TIME}...")
        xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]"
        
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", btn)
        print("SUCCESS: Reserve button clicked!")

    except Exception as e:
        print(f"Bot failed at: {e}")
        # THIS IS KEY: Saves a picture of the error
        driver.save_screenshot("error_screenshot.png")
        print("Screenshot saved as error_screenshot.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
