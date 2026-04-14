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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN
        print("Logging in...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO THE GOLF PAGE (Ensures session is active)
        time.sleep(8)
        print("Opening Tee Sheet landing page...")
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. SELECT DATE (Triggering the JavaScript)
        tz = pytz.timezone('US/Central')
        target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        print(f"Selecting date: {target_day}...")
        # We search for the date number and click it to trigger the AJAX load
        date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']"
        date_btn = wait.until(EC.element_to_be_clickable((By.XPATH, date_xpath)))
        driver.execute_script("arguments[0].click();", date_btn)
        
        # 4. WAIT FOR THE "ENGINE" TO INITIALIZE
        print("Date clicked. Waiting for booking engine frames to initialize...")
        time.sleep(12) 

        # 5. SCAN EVERY FRAME FOR THE RESERVE BUTTON
        # We do this in a loop because the frame might appear after a few seconds
        success = False
        search_time = WANTED_TIME.split(" ")[0]
        
        for attempt in range(2):
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Attempt {attempt+1}: Scanning {len(iframes)} frames...")
            
            for i, frame in enumerate(iframes):
                driver.switch_to.default_content()
                driver.switch_to.frame(frame)
                try:
                    # Look for the specific time or ANY reserve button
                    target_xpath = f"//*[contains(text(), '{search_time}')]/following::a[contains(text(), 'Reserve')][1]"
                    any_btn = "//a[contains(text(), 'Reserve')]"
                    
                    try:
                        btn = driver.find_element(By.XPATH, target_xpath)
                    except:
                        btn = driver.find_element(By.XPATH, any_btn)
                        
                    print(f"SUCCESS: Found button in frame {i}!")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    driver.execute_script("arguments[0].click();", btn)
                    success = True
                    break
                except:
                    continue
            if success: break
            time.sleep(5) # Wait before second attempt

        if not success:
            raise Exception("Tee sheet grid did not load even after clicking the date.")

        # 6. FINAL CONFIRM
        time.sleep(3)
        try:
            confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
            driver.execute_script("arguments[0].click();", confirm)
            print("RESERVATION COMPLETE!")
        except:
            print("Time selected, but no final confirmation button found. Manual check advised.")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
