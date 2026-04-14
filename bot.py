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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. LOGIN
        print("Opening Briarwood...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        
        user_field = wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername")))
        user_field.send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE
        time.sleep(8)
        print("Navigating to Tee Sheet...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        # 3. SMART FRAME SWITCH
        time.sleep(5)
        print("Searching for the correct frame...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                driver.find_element(By.ID, "txtDate")
                print(f"Interactive frame found at index {i}!")
                break
            except:
                continue

        # 4. SET DATE (TEST MODE: Tomorrow)
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") 

        print(f"Setting date to {target_date}...")
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDate")))
        date_input.click()
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        
        # 5. WAIT FOR SHEET TO REFRESH
        print("Waiting for slots to load...")
        time.sleep(6) # Increase sleep to ensure AJAX finishes
        
        # 6. AGGRESSIVE SEARCH FOR RESERVE
        print(f"Scanning for {WANTED_TIME} Reserve button...")
        
        # Try 3 different XPaths in order of reliability
        selectors = [
            f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]",
            f"//tr[contains(., '{WANTED_TIME.split(':')[0]}')]//a[contains(text(), 'Reserve')]",
            f"//a[contains(@href, 'booking') and contains(., 'Reserve')][1]" # Last ditch: First available
        ]
        
        btn = None
        for selector in selectors:
            try:
                btn = driver.find_element(By.XPATH, selector)
                if btn.is_displayed():
                    print(f"Found button using: {selector}")
                    break
            except:
                continue
        
        if btn:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn)
            print("SUCCESS: Reserve button clicked!")
        else:
            raise Exception("No Reserve button found after trying all selectors.")

    except Exception as e:
        print(f"Bot failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
