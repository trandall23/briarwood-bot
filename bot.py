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
    wait = WebDriverWait(driver, 20) # Increased to 20 seconds
    
    try:
        # 1. LOGIN
        print("Navigating to Briarwood...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        
        print("Submitting Login...")
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. THE DRILL-DOWN (Finding the sheet)
        time.sleep(8) # Long wait for the heavy CE portal to load
        
        # Sometimes you have to click the word 'Tee Sheet' to actually load the frame
        try:
            print("Ensuring Tee Sheet tab is active...")
            sheet_tab = driver.find_element(By.XPATH, "//span[text()='Tee Sheet'] | //a[text()='Tee Sheet']")
            driver.execute_script("arguments[0].click();", sheet_tab)
            time.sleep(3)
        except:
            print("Already on Tee Sheet tab or tab not clickable.")

        # DEEP FRAME SEARCH
        print("Hunting for the interactive frame...")
        all_frames = driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(all_frames):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            # Look for inner frames (Frame-in-Frame)
            inner_frames = driver.find_elements(By.TAG_NAME, "iframe")
            if inner_frames:
                print(f"Frame {i} has {len(inner_frames)} inner frames. Diving deeper...")
                driver.switch_to.frame(inner_frames[0])
            
            try:
                # This is the "Gold Standard" ID for ClubEssential booking dates
                wait.until(EC.presence_of_element_located((By.ID, "txtDate")))
                print(f"SUCCESS: Interactive sheet found!")
                break
            except:
                continue

        # 3. SET DATE & TIME
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") # TEST MODE

        # TIMER LOOP (Uncomment for Thursday morning!)
        # print("Waiting for 7:00 AM CST...")
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #    time.sleep(0.1)

        print(f"Setting date to {target_date}...")
        date_input = driver.find_element(By.ID, "txtDate")
        date_input.click()
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.ENTER)
        time.sleep(4)

        # 4. GRAB THE SLOT
        print(f"Looking for {WANTED_TIME}...")
        # Broadest possible XPATH to find that Reserve button from your screenshot
        xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]"
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        print("RESERVE CLICKED!")

        # 5. FINAL POPUP
        time.sleep(2)
        try:
            finish = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", finish)
            print("BOOKING CONFIRMED")
        except:
            print("Manual confirmation might be needed, but the time is likely held.")

    except Exception as e:
        print(f"Final Error: {e}")
        # Take a screenshot if it fails (GitHub Actions will save this in 'Artifacts')
        driver.save_screenshot("error_view.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
