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
WANTED_TIME = os.getenv("TARGET_TIME") # e.g., "9:30"

def book():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']")))
        user_input.send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO TEE SHEET
        time.sleep(7)
        print("Navigating to Tee Sheet page...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        # 3. SELECT DATE VIA INPUT BOX
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y")
        
        # --- TIMER (UNCOMMENT FOR 7:00 AM THURSDAY) ---
        # print("Waiting for 07:00:00 AM CST...")
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #     time.sleep(0.1)

        print(f"Typing date: {target_date}")
        
        # We find the frame containing the txtDate box first
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found_date_box = False
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                date_box = driver.find_element(By.ID, "txtDate")
                date_box.click()
                date_box.clear()
                date_box.send_keys(target_date)
                date_box.send_keys(Keys.ENTER)
                print(f"Date entered in frame {i}")
                found_date_box = True
                break
            except:
                continue
        
        if not found_date_box:
            raise Exception("Could not find the date input box (txtDate) in any frame.")

        # 4. SCAN FOR RESERVE BUTTONS
        print("Waiting 10s for the grid to update...")
        time.sleep(10)
        
        # Search frames again for the buttons
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found_btn = False
        search_val = WANTED_TIME.split(" ")[0]

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Target specific time OR any available slot
                xpath_specific = f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]"
                xpath_any = "//a[contains(text(), 'Reserve')]"
                
                try:
                    btn = driver.find_element(By.XPATH, xpath_specific)
                except:
                    btn = driver.find_element(By.XPATH, xpath_any)
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].click();", btn)
                found_btn = True
                break
            except:
                continue
        
        if not found_btn:
            raise Exception("No Reserve buttons found after typing date.")

        # 5. FINAL CONFIRM
        time.sleep(2)
        try:
            confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", confirm)
            print("RESERVATION FINALIZED!")
        except:
            print("Confirmation button not found - check site.")

    except Exception as e:
        print(f"Failed: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
