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
# Format: "9:30" or just "9" to grab anything in the 9 o'clock hour
WANTED_TIME = os.getenv("TARGET_TIME") 

def book():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']")))
        user_input.send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. DATE SETTINGS
        time.sleep(7)
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y")
        
        # 3. DIRECT JUMP
        print(f"Jumping to Tee Sheet for {target_date}...")
        sheet_url = f"https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&ssid=100184&vnf=1&date={target_date}"
        driver.get(sheet_url)

        # --- TIMER (UNCOMMENT THE 2 LINES BELOW FOR THE 7:00 AM RUN) ---
        # while datetime.now(tz).strftime("%H:%M:%S") < "07:00:00":
        #     time.sleep(0.1)
        
        # 4. PATIENT SCAN
        print("Scanning frames for any Reserve buttons...")
        time.sleep(12) # Maximum patience for the grid
        
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found = False
        
        # We strip AM/PM to be safe
        search_val = WANTED_TIME.split(" ")[0]

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # OPTION A: Look for your specific time
                xpath_specific = f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]"
                # OPTION B: Look for ANY reserve button as a backup
                xpath_any = "//a[contains(text(), 'Reserve')]"
                
                print(f"Checking frame {i}...")
                try:
                    btn = driver.find_element(By.XPATH, xpath_specific)
                    print(f"Target {search_val} found!")
                except:
                    btn = driver.find_element(By.XPATH, xpath_any)
                    print("Target time not found, but grabbing FIRST available slot instead!")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].click();", btn)
                found = True
                break
            except:
                continue
        
        if not found:
            raise Exception("No Reserve buttons visible in any frame. Grid might be empty or restricted.")

        # 5. FINAL CONFIRM
        time.sleep(2)
        try:
            confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", confirm)
            print("RESERVATION FINALIZED!")
        except:
            print("Button clicked, but no final confirmation screen appeared. Check site.")

    except Exception as e:
        print(f"Failed: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
