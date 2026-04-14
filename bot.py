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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE TO THE PAGE
        time.sleep(8)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. SELECT DATE
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        # 4. TRIGGER THE GRID (THE KICKSTART)
        print(f"Targeting Day: {target_day}")
        try:
            # Click the date number/icon
            date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']"
            date_el = wait.until(EC.element_to_be_clickable((By.XPATH, date_xpath)))
            driver.execute_script("arguments[0].click();", date_el)
            print("Date clicked. Performing force-render...")
            
            # FORCE RENDER: Scroll down and back up to trigger the AJAX load
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            
            # Heavy wait for the grid to fill the white space
            time.sleep(10) 
        except Exception as e:
            print(f"Warning: Date click or force-render failed: {e}")

        # 5. SCAN EVERY FRAME (DEEP SCAN)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found = False
        search_val = WANTED_TIME.split(" ")[0]

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            print(f"Scanning Frame {i} for 'Reserve'...")
            
            try:
                # Look for the time-specific button or ANY button
                xpath_specific = f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]"
                xpath_any = "//a[contains(text(), 'Reserve')]"
                
                # Check for buttons inside this frame
                btns = driver.find_elements(By.XPATH, xpath_any)
                if len(btns) > 0:
                    print(f"Found {len(btns)} buttons in frame {i}!")
                    try:
                        btn = driver.find_element(By.XPATH, xpath_specific)
                    except:
                        btn = btns[0] # Grab the first one if specific time isn't there
                    
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    driver.execute_script("arguments[0].click();", btn)
                    found = True
                    break
            except:
                continue

        if not found:
            # One last check: Is it on the main page WITHOUT a frame?
            driver.switch_to.default_content()
            try:
                btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
                driver.execute_script("arguments[0].click();", btn)
                found = True
                print("Found button on main page level!")
            except:
                raise Exception("The tee sheet grid is simply not loading. White space still present.")

        # 6. FINAL CONFIRMATION
        if found:
            time.sleep(2)
            try:
                confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
                driver.execute_script("arguments[0].click();", confirm)
                print("RESERVATION FINALIZED!")
            except:
                print("Confirm button not found, check dashboard.")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
