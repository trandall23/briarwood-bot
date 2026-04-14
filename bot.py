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
WANTED_TIME = os.getenv("TARGET_TIME") # e.g., "9:30 AM"

def book():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Adding a 'User Agent' makes the bot look like a real Mac browser
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. THE BYPASS LOGIN
        # We go to the login page first to get the session cookie
        print("Authenticating...")
        driver.get("https://www.briarwoodgolfclub.org/login.aspx")
        
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        time.sleep(5)

        # 2. JUMP DIRECTLY TO THE SHEET
        # We use the specific SSID and PageID for the booking engine
        print("Jumping to direct booking URL...")
        direct_url = "https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&ssid=100184&vnf=1"
        driver.get(direct_url)
        time.sleep(5)

        # 3. DATE SETUP
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") # TEST MODE

        # Real-time wait (Uncomment for Thursday morning!)
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #    time.sleep(0.1)

        # 4. SEARCH FOR DATE INPUT NO MATTER WHERE IT IS
        print(f"Setting date to {target_date}...")
        # We search 'everywhere' (//) for the date box
        try:
            date_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='txtDate' or @name='txtDate']")))
            date_box.click()
            date_box.clear()
            date_box.send_keys(target_date)
            date_box.send_keys(Keys.ENTER)
            time.sleep(3)
        except:
            print("Date box still hidden. Trying a page refresh...")
            driver.refresh()
            time.sleep(3)

        # 5. THE AGGRESSIVE GRAB
        time.sleep(5) # Give the sheet plenty of time to load
        print(f"Scanning page for {WANTED_TIME}...")
        
        try:
            # This looks for the time text and then find the very next 'Reserve' link
            # It uses 'contains' to handle any weird spacing or hidden characters
            xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]"
            
            # Wait up to 15 seconds for the button to be clickable
            booking_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            
            # Use JavaScript to click it (bypasses any 'invisible' overlays)
            driver.execute_script("arguments[0].click();", booking_button)
            print(f"SUCCESS: Clicked Reserve for {WANTED_TIME}")
            
            # 6. THE FINAL CONFIRMATION
            time.sleep(2)
            try:
                # Look for a 'Finish' or 'Reserve' button in the popup
                final_btn = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish') or contains(@id, 'Finish')]")
                driver.execute_script("arguments[0].click();", final_btn)
                print("FINAL CONFIRMATION CLICKED!")
            except:
                print("No final confirmation button found—the slot might already be held.")
                
        except Exception as e:
            print(f"Could not find the {WANTED_TIME} slot.")
            # Fallback: Just click the FIRST Reserve button on the whole page
            try:
                first_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
                driver.execute_script("arguments[0].click();", first_btn)
                print("Clicked the first available 'Reserve' button instead.")
            except:
                print("Total Failure: No 'Reserve' buttons found on the page.")
