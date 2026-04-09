import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Get info from your iPhone/GitHub inputs
USER = os.getenv("USER")
PASS = os.getenv("PASS")
WANTED_TIME = os.getenv("TARGET_TIME") # e.g. "08:00 AM"

def book():
    options = Options()
    options.add_argument("--headless") # Runs in the background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        # Login
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername").send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # Calculate Date (Next week)
        target_date = (datetime.now() + timedelta(days=7)).strftime("%m/%d/%Y")
        
        # Wait for 7 AM
        print(f"Waiting for 7 AM to book {target_date} at {WANTED_TIME}...")
        while datetime.now().strftime("%H:%M:%S") < "07:00:00":
            time.sleep(0.1)
            
        # Set Date
        date_input = driver.find_element(By.ID, "txtDate")
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        
        # Click the Time Slot
        time.sleep(1) # Wait for sheet to load
        slot = driver.find_element(By.XPATH, f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Book')]")
        slot.click()
        print("Success! Slot selected.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
