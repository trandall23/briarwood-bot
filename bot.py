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
WANTED_TIME = os.getenv("TARGET_TIME") # e.g., "9:30" (AM/PM is handled by fuzzy match)

def book():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO PAGE
        time.sleep(7)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. SELECT DATE
        tz = pytz.timezone('US/Central')
        # TEST MODE: days=1 | REAL RUN: days=7
        target_day_num = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        # --- THE 7:00 AM TIMER (UNCOMMENT FOR THURSDAY) ---
        # print("Waiting for 07:00:00 AM CST...")
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #     time.sleep(0.1)
        # --------------------------------------------------

        print(f"Triggering date: {target_day_num}")
        date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day_num}')] | //*[text()='{target_day_num}']"
        date_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, date_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_trigger)
        driver.execute_script("arguments[0].click();", date_trigger)
        
        # WAIT FOR GRID TO POPULATE
        print("Date clicked. Waiting 8s for the booking engine to load...")
        time.sleep(8) 

        # 4. SCAN FRAMES FOR BUTTONS
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Scanning {len(iframes)} frames...")
        
        time_digits = WANTED_TIME.split(" ")[0] # Gets "9:30" from "9:30 AM"
        found = False
        
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Give the frame internal time to render buttons
                reserve_xpath = "//a[contains(text(), 'Reserve')]"
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, reserve_xpath)))
                
                # Look for specific time
                target_xpath = f"//*[contains(text(), '{time_digits}')]/following::a[contains(text(), 'Reserve')][1]"
                btn = driver.find_element(By.XPATH, target_xpath)
                
                print(f"Target found in frame {i}. Clicking!")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].click();", btn)
                found = True
                break
            except:
                continue
        
        if not found:
            # Last ditch attempt: grab the first available button in the LAST frame we checked
            print("Target time not seen. Trying first available button...")
            try:
                any_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
                driver.execute_script("arguments[0].click();", any_btn)
                print("Clicked first available slot!")
                found = True
            except:
                raise Exception("Zero Reserve buttons found. Grid did not load.")

        # 5. FINAL CONFIRM
        if found:
            time.sleep(2)
            try:
                finish = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
                driver.execute_script("arguments[0].click();", finish)
                print("RESERVATION COMPLETE!")
            except:
                print("No finish button needed.")

    except Exception as e:
        print(f"Failed: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
