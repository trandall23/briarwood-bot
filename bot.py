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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN
        print("Logging in...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE
        time.sleep(8)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. DATE CALCULATION
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y")
        
        # 4. THE INSIDE-OUT TRIGGER
        print(f"Hunting for the hidden date box to trigger {target_date}...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found_trigger = False

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Find the actual text box inside the frame
                date_box = driver.find_element(By.ID, "txtDate")
                print(f"Found date box in frame {i}. Activating...")
                
                # Human-like interaction
                date_box.click()
                date_box.send_keys(Keys.COMMAND + "a") # Select all
                date_box.send_keys(Keys.BACKSPACE)    # Delete
                
                # Type the date slowly
                for char in target_date:
                    date_box.send_keys(char)
                    time.sleep(0.1)
                
                date_box.send_keys(Keys.ENTER)
                found_trigger = True
                break
            except:
                continue

        if not found_trigger:
            print("Direct date box not found. Clicking weather icon as backup...")
            driver.switch_to.default_content()
            day_num = (datetime.now(tz) + timedelta(days=1)).strftime("%-d")
            driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, f"//*[text()='{day_num}']"))

        # 5. SCAN FOR RESERVE BUTTONS
        print("Waiting 12s for the grid to fill...")
        time.sleep(12)
        
        # Final sweep of all frames for ANY reserve button
        success = False
        search_val = WANTED_TIME.split(" ")[0]
        
        # Re-fetch frames in case the page refreshed
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Look for specific time OR any button
                xpath_specific = f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]"
                btns = driver.find_elements(By.XPATH, "//a[contains(text(), 'Reserve')]")
                
                if btns:
                    try:
                        btn = driver.find_element(By.XPATH, xpath_specific)
                        print(f"Target {search_val} found!")
                    except:
                        btn = btns[0]
                        print("Target time not found, but grabbing FIRST available slot!")
                    
                    driver.execute_script("arguments[0].click();", btn)
                    success = True
                    break
            except:
                continue

        if not success:
            raise Exception("Grid still empty. The 'txtDate' update did not trigger the slots.")

        # 6. CONFIRM
        time.sleep(3)
        confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
        driver.execute_script("arguments[0].click();", confirm)
        print("RESERVATION FINALIZED!")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
