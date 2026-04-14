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
    # Updated User Agent to be even more "Human"
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. LOGIN
        print("Logging in...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO THE TEE SHEET PAGE
        time.sleep(8)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. DATE SETUP
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") 
        
        # 4. INTERNAL FRAME HANDSHAKE
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found_grid = False
        
        print(f"Probing {len(iframes)} frames for the internal date box...")
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Try to find the hidden date input box
                date_input = driver.find_element(By.ID, "txtDate")
                print(f"Bingo! Found date box in Frame {i}. Injecting date {target_date}...")
                
                # Use JS to set value and fire the 'change' event to trigger the grid
                driver.execute_script(f"arguments[0].value = '{target_date}';", date_input)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", date_input)
                date_input.send_keys(Keys.ENTER)
                
                found_grid = True
                break
            except:
                continue

        if not found_grid:
            print("Could not find internal date box. Trying a 'fallback' click on the weather icons...")
            driver.switch_to.default_content()
            target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d")
            date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']"
            driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, date_xpath))

        # 5. FINAL SCAN FOR RESERVE BUTTONS
        print("Waiting 10s for grid population...")
        time.sleep(10)
        
        # We stay in the frame we found or scan all again
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        success = False
        search_val = WANTED_TIME.split(" ")[0]

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                btn_xpath = f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]"
                # Backup: First available
                any_btn_xpath = "//a[contains(text(), 'Reserve')]"
                
                try:
                    btn = driver.find_element(By.XPATH, btn_xpath)
                except:
                    btn = driver.find_element(By.XPATH, any_btn_xpath)
                
                print(f"Button found in Frame {i}! Clicking...")
                driver.execute_script("arguments[0].click();", btn)
                success = True
                break
            except:
                continue

        if success:
            time.sleep(2)
            try:
                confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
                driver.execute_script("arguments[0].click();", confirm)
                print("RESERVATION SUCCESSFUL!")
            except:
                print("Reserve clicked, but no confirmation button. Manual check recommended.")
        else:
            raise Exception("Grid failed to load buttons in all frames.")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
