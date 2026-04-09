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
        
       # 5. FIND AND CLICK THE 'RESERVE' BUTTON
        time.sleep(3) # Give the green bars plenty of time to render
        try:
            print(f"Searching for the 'Reserve' button next to {WANTED_TIME}...")
            
            # This XPath translates to: 
            # "Find the element that has the text '10:00 AM' exactly, 
            # then find the 'Reserve' link right next to it."
            xpath_selector = f"//*[text()='{WANTED_TIME}']/following::a[contains(text(), 'Reserve')][1]"
            
            booking_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
            
            # Scroll to it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", booking_button)
            time.sleep(0.5)
            
            # Use a 'JavaScript Click' - this is more powerful for these green buttons
            driver.execute_script("arguments[0].click();", booking_button)
            
            print(f"SUCCESS: Clicked 'Reserve' for {WANTED_TIME}")
            
            # --- FINAL STEP: CONFIRMATION ---
            time.sleep(2)
            try:
                # Based on the screenshot, look for a 'Reserve' or 'Finish' button in the popup
                finish_btn = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish') or @id='btnReserve']")
                finish_btn.click()
                print("Final confirmation clicked!")
            except:
                print("Could not find final 'Finish' button, but the slot was initiated.")
                
        except Exception as e:
            print(f"Direct search failed. Trying 'First Available' fallback...")
            try:
                # This finds the very first green 'Reserve' button on the whole page
                first_reserve = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
                first_reserve.click()
                print("Clicked the first available 'Reserve' button on the page.")
            except:
                print("Failed to find any 'Reserve' buttons. Check if the tee sheet loaded.")
            
        except Exception as e:
            print(f"Time slot {WANTED_TIME} not found or already taken: {e}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing session.")
        driver.quit()

if __name__ == "__main__":
    book()
