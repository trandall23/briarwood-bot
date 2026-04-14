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
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. LOGIN
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE
        time.sleep(10) # Heavy wait for session to settle
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(8) # Wait for the visual landing page

        # 3. SELECT DATE
        tz = pytz.timezone('US/Central')
        # TEST: days=1 | REAL: days=7
        target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        # 4. EXHAUSTIVE CLICKER
        print(f"Searching for date icon '{target_day}'...")
        
        # Try to click the date icon on the main page first
        try:
            date_icon = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']")))
            driver.execute_script("arguments[0].click();", date_icon)
            print("Date icon clicked on main page.")
            time.sleep(5)
        except:
            print("Date icon not found on main page, checking frames...")

        # 5. SCAN EVERY FRAME FOR THE RESERVE BUTTON
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        found = False
        
        # We strip the search time down to the numbers (e.g., "9:30")
        search_time = WANTED_TIME.split(" ")[0]

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            print(f"Scanning Frame {i}...")
            
            try:
                # Look for the time followed by a Reserve button
                target_xpath = f"//*[contains(text(), '{search_time}')]/following::a[contains(text(), 'Reserve')][1]"
                # Backup: Just any Reserve button
                any_reserve = "//a[contains(text(), 'Reserve')]"
                
                try:
                    btn = driver.find_element(By.XPATH, target_xpath)
                except:
                    btn = driver.find_element(By.XPATH, any_reserve)

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].click();", btn)
                found = True
                print(f"SUCCESS: Clicked button in frame {i}")
                break
            except:
                # Dive one level deeper into nested frames
                nested = driver.find_elements(By.TAG_NAME, "iframe")
                for j, n_frame in enumerate(nested):
                    driver.switch_to.frame(n_frame)
                    try:
                        btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Reserve')]")
                        driver.execute_script("arguments[0].click();", btn)
                        found = True
                        print(f"SUCCESS: Clicked button in nested frame {i}-{j}")
                        break
                    except:
                        driver.switch_to.parent_frame()
                if found: break

        if not found:
            raise Exception("No Reserve buttons found anywhere on the page or in frames.")

        # 6. FINAL CONFIRMATION
        time.sleep(2)
        confirm = driver.find_element(By.XPATH, "//input[contains(@value, 'Reserve') or contains(@value, 'Finish')]")
        driver.execute_script("arguments[0].click();", confirm)
        print("RESERVATION FINALIZED!")

    except Exception as e:
        print(f"Failed at: {e}")
        driver.save_screenshot("error_screenshot.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    book()
