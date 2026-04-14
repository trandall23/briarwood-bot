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
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtUsername"))).send_keys(USER)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(PASS)
        driver.find_element(By.ID, "masterPageUC_MPCA152_ctl00_ctl02_txtPassword").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO TEE SHEET PAGE
        time.sleep(7)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. CLICK THE DATE ICON (To trigger the grid)
        tz = pytz.timezone('US/Central')
        # We want to click the date for 'Wed 15' in your test
        target_day_num = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        print(f"Triggering grid for day: {target_day_num}")
        
        try:
            # Looks for the weather icon/date text and clicks it
            date_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'date') and contains(., '{target_day_num}')] | //*[text()='{target_day_num}']")))
            driver.execute_script("arguments[0].click();", date_trigger)
            print("Date clicked, waiting for grid...")
            time.sleep(5)
        except:
            print("Could not find date trigger, grid might already be loading.")

        # 4. EXHAUSTIVE SEARCH FOR RESERVE BUTTON
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Checking {len(iframes)} frames for the Reserve button...")
        
        found = False
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Look for the specific time and its Reserve button
                xpath = f"//*[contains(text(), '{WANTED_TIME}')]/following::a[contains(text(), 'Reserve')][1]"
                btn = driver.find_element(By.XPATH, xpath)
                print(f"SUCCESS: Found button in frame {i}!")
                driver.execute_script("arguments[0].click();", btn)
                found = True
                break
            except:
                continue
        
        if not found:
            raise Exception(f"Grid loaded but could not find {WANTED_TIME} Reserve button.")

    except Exception as e:
        print(f"Error: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
