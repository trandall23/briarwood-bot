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
WANTED_TIME = os.getenv("TARGET_TIME") # e.g., "10:00 AM"

def book():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. DATE CALCULATION
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") # TEST MODE: 1 day
        
        # 3. THE TIMER (Uncomment this for the real run tomorrow!)
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #    time.sleep(0.1)

        # 4. HANDLE IFRAME (The Secret Sauce)
        time.sleep(5) # Give the page a long time to load
        
        # This looks for any 'iframe' and switches to it
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if len(iframes) > 0:
            print(f"Found {len(iframes)} frames. Switching to the tee sheet frame...")
            driver.switch_to.frame(iframes[0]) 
        
        # 5. SET DATE
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDate")))
        date_input.click()
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        time.sleep(3) # Wait for sheet to refresh
        
        # 6. CLICK RESERVE
        print(f"Searching for {WANTED_TIME}...")
        try:
            # Look for the time, then the very next Reserve link
            xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]"
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            print("SUCCESS: Clicked Reserve!")
            
            # FINAL CONFIRMATION
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);") # Popups are usually at the top
            conf = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            conf.click()
            print("BOOKING CONFIRMED")
            
        except Exception as e:
            print(f"Failed to find button: {e}")
            # Fallback to FIRST available
            btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
            btn.click()
            print("Clicked first available slot as fallback.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
