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
        time.sleep(8)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. DATE SETUP
        tz = pytz.timezone('US/Central')
        target_date = (datetime.now(tz) + timedelta(days=1)).strftime("%m/%d/%Y") 
        
        # 4. DEEP FRAME SEARCH FOR DATE BOX
        print("Searching all nested frames for the booking engine...")
        found_date_box = False
        
        # Get top-level frames
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            
            # Check for txtDate in this frame OR nested frames
            try:
                date_box = driver.find_element(By.ID, "txtDate")
                found_date_box = True
            except:
                # Look for frames inside this frame (The "Deep Dive")
                inner_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for j, inner_frame in enumerate(inner_iframes):
                    driver.switch_to.frame(inner_frame)
                    try:
                        date_box = driver.find_element(By.ID, "txtDate")
                        found_date_box = True
                        print(f"Found booking engine in nested frame {i}-{j}")
                        break
                    except:
                        driver.switch_to.parent_frame()
            
            if found_date_box:
                date_box.click()
                date_box.clear()
                date_box.send_keys(target_date)
                date_box.send_keys(Keys.ENTER)
                break

        if not found_date_box:
            raise Exception("Could not find the booking engine in any frame or nested frame.")

        # 5. WAIT AND CLICK RESERVE
        print("Date set. Waiting for grid...")
        time.sleep(8)
        
        # Re-scan for buttons (using the frame we are currently in)
        search_val = WANTED_TIME.split(" ")[0]
        xpath_specific = f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]"
        xpath_any = "//a[contains(text(), 'Reserve')]"
        
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_specific)))
        except:
            print("Specific time not found, attempting any open slot...")
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_any)))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        print("SUCCESS: Reserve button clicked!")

        # 6. FINAL CONFIRM
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
