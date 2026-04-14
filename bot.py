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
    wait = WebDriverWait(driver, 30) # High patience for slow club sites
    
    try:
        # 1. LOGIN
        print("Logging in...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE
        time.sleep(7)
        print("Opening Tee Sheet...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        # 3. DATE SELECT
        tz = pytz.timezone('US/Central')
        target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        # --- TIMER (UNCOMMENT FOR THURSDAY) ---
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #    time.sleep(0.1)

        print(f"Selecting date: {target_day}...")
        date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']"
        date_btn = wait.until(EC.element_to_be_clickable((By.XPATH, date_xpath)))
        driver.execute_script("arguments[0].click();", date_btn)
        
        # 4. WAIT FOR REFRESH & GRID
        print("Waiting for grid to re-initialize...")
        time.sleep(12) # Give the refresh plenty of time
        
        # 5. SCAN FRAMES (DETERMINISTIC)
        found = False
        search_time = WANTED_TIME.split(" ")[0]
        
        # We look for IFRAMES specifically that contain booking content
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} frames after refresh. Scanning...")
        
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Search for digits + following Reserve button
                # We use a broader search to find ANY Reserve button if specific time is missed
                specific_xpath = f"//*[contains(text(), '{search_time}')]/following::a[contains(text(), 'Reserve')][1]"
                any_reserve = "//a[contains(text(), 'Reserve')]"
                
                try:
                    btn = driver.find_element(By.XPATH, specific_xpath)
                except:
                    btn = driver.find_element(By.XPATH, any_reserve)
                
                print(f"Button found in Frame {i}. Clicking...")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].click();", btn)
                found = True
                break
            except:
                continue
                
        if not found:
            raise Exception("Tee sheet grid failed to load. All frames scanned were empty.")

        # 6. FINAL CONFIRM
        time.sleep(3)
        try:
            finish = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", finish)
            print("RESERVATION FINALIZED!")
        except:
            print("Selection made, check account for confirmation.")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
