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
from selenium.webdriver.common.action_chains import ActionChains

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

        # 3. SELECT DATE
        tz = pytz.timezone('US/Central')
        target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        print(f"Searching for date icon '{target_day}'...")
        # Find the date element, scroll it into the middle of the screen, and click it
        date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']"
        date_el = wait.until(EC.presence_of_element_located((By.XPATH, date_xpath)))
        
        # Use ActionChains to move to the element and click (more human-like)
        actions = ActionChains(driver)
        actions.move_to_element(date_el).perform()
        time.sleep(1)
        driver.execute_script("arguments[0].click();", date_el)
        print("Date clicked. Waiting for AJAX grid...")
        
        # 4. THE "GRID FORCE" - Wait specifically for any Reserve link to appear in any frame
        time.sleep(12) 
        
        found = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Scanning {len(iframes)} frames for buttons...")

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            
            # Check for the Reserve buttons (try multiple ways)
            try:
                # Look for the specific time if possible
                time_val = WANTED_TIME.split(" ")[0]
                specific_xpath = f"//*[contains(text(), '{time_val}')]/following::a[contains(text(), 'Reserve')][1]"
                
                # Check for any button
                reserve_btns = driver.find_elements(By.XPATH, "//a[contains(text(), 'Reserve')]")
                
                if reserve_btns:
                    print(f"Buttons found in Frame {i}!")
                    try:
                        target = driver.find_element(By.XPATH, specific_xpath)
                        print(f"Found specific time: {time_val}")
                    except:
                        target = reserve_btns[0]
                        print("Specific time not found, taking first available.")
                    
                    driver.execute_script("arguments[0].click();", target)
                    found = True
                    break
            except:
                continue

        if not found:
            raise Exception("Tee sheet grid did not populate with 'Reserve' buttons.")

        # 5. FINAL CONFIRM
        time.sleep(3)
        confirm_btn = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
        driver.execute_script("arguments[0].click();", confirm_btn)
        print("RESERVATION SUCCESS!")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
