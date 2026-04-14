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
    # Using a very standard User Agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN (Starting from Home to set cookies)
        print("Opening Home Page...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        time.sleep(3)
        
        print("Attempting login...")
        # Use a more flexible selector for the username
        user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']")))
        user_input.send_keys(USER)
        
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']")
        pass_input.send_keys(PASS)
        pass_input.send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO SHEET
        time.sleep(7)
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y")
        
        print(f"Jumping to Tee Sheet for {target_date}...")
        # Direct URL with date injection
        sheet_url = f"https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&ssid=100184&vnf=1&date={target_date}"
        driver.get(sheet_url)
        
        # --- THE 7:00 AM TIMER (UNCOMMENT FOR THE REAL RUN) ---
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #     time.sleep(0.1)

        # 3. SCAN FOR BUTTONS
        print("Waiting for booking engine...")
        time.sleep(10) 
        
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Scanning {len(iframes)} frames...")
        
        time_digits = WANTED_TIME.split(" ")[0]
        found = False
        
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Search for digits + following Reserve button
                xpath = f"//*[contains(text(), '{time_digits}')]/following::a[contains(text(), 'Reserve')][1]"
                btn = WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                
                print(f"SUCCESS: Found {time_digits} in frame {i}. Clicking...")
                driver.execute_script("arguments[0].click();", btn)
                found = True
                break
            except:
                continue
        
        if not found:
            raise Exception("Grid visible but target time/Reserve button not found.")

        # 4. FINAL CONFIRMATION
        time.sleep(2)
        try:
            confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", confirm)
            print("RESERVATION FINALIZED!")
        except:
            print("Confirmation button not found - check club account.")

    except Exception as e:
        print(f"Failed: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
