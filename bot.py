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
        print("Opening Briarwood...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        print("Logging in...")
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. CALCULATE DATE (7 Days out in CST)
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y")
        
        # 3. PRECISION WAIT UNTIL 7:00:00 AM CST
        print(f"Targeting Date: {target_date} | Time: {WANTED_TIME}")
        print("Standing by for 7:00 AM CST release...")
        
       # while True:
       #     now_cst = datetime.now(tz)
            # When it hits 7:00:00 AM, we break the loop and act
       #     if now_cst.hour == 7 and now_cst.minute == 0:
       #         print(f"GO! Local Time: {now_cst.strftime('%H:%M:%S')}")
       #         break
       #     time.sleep(0.1) # Check every 100ms
            
        # 4. SET DATE
        # We refresh or interact with the date picker the moment it turns 7 AM
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDate")))
        date_input.click()
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        
       # 5. FIND AND CLICK THE 'BOOK' BUTTON
        time.sleep(2) # Give it an extra second to fully load the sheet
        try:
            # This version is much "smarter":
            # 1. It looks for any cell containing your number (e.g., "10:00")
            # 2. It finds the very next 'Book' link in the table
            xpath_selector = f"//td[contains(., '{WANTED_TIME.split()[0]}')]//following::a[contains(text(), 'Book')][1]"
            
            print(f"Searching for slot near {WANTED_TIME}...")
            booking_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
            
            # Scroll it into view just in case
            driver.execute_script("arguments[0].scrollIntoView();", booking_button)
            time.sleep(0.5)
            
            booking_button.click()
            print(f"SUCCESS: Clicked 'Book' for {WANTED_TIME}")
            
        except Exception as e:
            print(f"Bot reached the sheet but couldn't 'grab' the {WANTED_TIME} slot.")
            print("This usually means the time format on the site is slightly different.")
            # This line is key: it prints the page text so we can see what the bot sees
            # print(driver.find_element(By.TAG_NAME, "body").text[:500])
            
        except Exception as e:
            print(f"Time slot {WANTED_TIME} not found or already taken: {e}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing session.")
        driver.quit()

if __name__ == "__main__":
    book()
