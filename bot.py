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
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. DATE CALCULATION
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") # TEST MODE
        
        # 3. THE IFRAME HUNT
        time.sleep(6) # Give it plenty of time
        
        found_sheet = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Detected {len(iframes)} frames. Searching for the tee sheet...")

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content() # Go back to main page
            driver.switch_to.frame(frame) # Dive into frame i
            try:
                # Check if the date input exists in this specific frame
                driver.find_element(By.ID, "txtDate")
                print(f"SUCCESS: Tee sheet found in Frame #{i}")
                found_sheet = True
                break
            except:
                continue
        
        if not found_sheet:
            print("COULD NOT FIND TEE SHEET IN ANY FRAME.")
            driver.switch_to.default_content() # Stay on main page as fallback

        # 4. SET DATE
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDate")))
        date_input.click()
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        time.sleep(4) # Wait for "Reserve" buttons to appear
        
        # 5. CLICK RESERVE
        print(f"Scanning for {WANTED_TIME}...")
        # We use a very broad search now: find any link near our time
        xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve') or contains(text(), 'Book')][1]"
        
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        print("SUCCESS: Slot selected!")
        
        # 6. FINAL CONFIRMATION
        time.sleep(2)
        try:
            # Look for a final 'Reserve' or 'Finish' button
            finish = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            finish.click()
            print("BOOKING CONFIRMED")
        except:
            print("Final button not found, but slot was clicked. Check your email!")

    except Exception as e:
        print(f"Error encountered: {e}")
        # Final debug: What does the bot actually see right now?
        print("Bot's current view (First 500 chars):")
        print(driver.find_element(By.TAG_NAME, "body").text[:500])
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
