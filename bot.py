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
        print("Logging in...")
        driver.get("https://www.briarwoodgolfclub.org/login.aspx")
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        time.sleep(5)

        # 2. DATE CALCULATION
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y")
        
        # 3. DIRECT URL INJECTION
        print(f"Jumping directly to grid for {target_date}...")
        # We append the date directly to the query string
        direct_url = f"https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&ssid=100184&vnf=1&date={target_date}"
        driver.get(direct_url)
        
        # --- TIMER (UNCOMMENT FOR 7:00 AM RUN) ---
        # print("Waiting for 07:00:00 AM CST...")
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #    time.sleep(0.1)
        
        # 4. PATIENT SCANNING
        print("Waiting for grid frames to settle...")
        time.sleep(10) # Heavy wait for the injector to work

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Scanning {len(iframes)} frames...")
        
        # Get digits (e.g., "9:30")
        time_digits = WANTED_TIME.split(" ")[0]
        found = False
        
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Look for the time and the Reserve button
                xpath = f"//*[contains(text(), '{time_digits}')]/following::a[contains(text(), 'Reserve')][1]"
                # Wait up to 10s inside the frame for the content to appear
                btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                
                print(f"Target found in frame {i}! Clicking...")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].click();", btn)
                found = True
                break
            except:
                continue
        
        if not found:
            # Final attempt: grab the first 'Reserve' button found anywhere
            print("Specific time not found. Searching for ANY available slot...")
            try:
                any_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
                driver.execute_script("arguments[0].click();", any_btn)
                print("Grabbed first available slot!")
                found = True
            except:
                raise Exception("The grid is still empty. Possible session timeout or date mismatch.")

        # 5. FINAL CONFIRMATION
        if found:
            time.sleep(2)
            try:
                finish = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
                driver.execute_script("arguments[0].click();", finish)
                print("RESERVATION SUCCESSFUL!")
            except:
                print("Slot selected, but no 'Finish' button found. Check account.")

    except Exception as e:
        print(f"Failed: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
