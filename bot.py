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
    # Stealth arguments to bypass bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Hide the 'navigator.webdriver' flag
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    wait = WebDriverWait(driver, 25)
    
    try:
        # 1. LOGIN
        print("Logging in...")
        driver.get("https://www.briarwoodgolfclub.org/default.aspx?p=home&E=1")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='txtUsername']"))).send_keys(USER)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(PASS)
        driver.find_element(By.CSS_SELECTOR, "input[id*='txtPassword']").send_keys(Keys.ENTER)
        
        # 2. NAVIGATE & FORCE RELOAD
        time.sleep(8)
        driver.get("https://www.briarwoodgolfclub.org/Default.aspx?p=DynamicModule&pageid=131&tt=booking&ssid=100184&vnf=1")
        time.sleep(5)

        # 3. SELECT DATE
        tz = pytz.timezone('US/Central')
        target_day = (datetime.now(tz) + timedelta(days=1)).strftime("%-d") 
        
        print(f"Targeting Day: {target_day}")
        date_xpath = f"//div[contains(@class, 'date') and contains(., '{target_day}')] | //*[text()='{target_day}']"
        date_el = wait.until(EC.presence_of_element_located((By.XPATH, date_xpath)))
        
        # Scroll to it and click via JS
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_el)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", date_el)
        
        # 4. THE "KICKSTART" LOOP
        print("Date clicked. Performing scroll-dance to trigger load...")
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
            driver.execute_script("window.scrollBy(0, -300);")
            time.sleep(1)
            
        # 5. SCAN EVERY FRAME
        print("Checking frames for populate...")
        found = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        search_val = WANTED_TIME.split(" ")[0]

        for i, frame in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            try:
                # Give each frame a tiny moment to check
                btns = driver.find_elements(By.XPATH, "//a[contains(text(), 'Reserve')]")
                if btns:
                    print(f"Buttons found in Frame {i}!")
                    try:
                        # Try finding specific time
                        btn = driver.find_element(By.XPATH, f"//*[contains(text(), '{search_val}')]/following::a[contains(text(), 'Reserve')][1]")
                    except:
                        btn = btns[0]
                    
                    driver.execute_script("arguments[0].click();", btn)
                    found = True
                    break
            except:
                continue

        if not found:
            # Last ditch: Take another screenshot to see if the grid finally appeared
            driver.save_screenshot("error_screenshot.png")
            raise Exception("Grid failed to load. The site might require a real mouse hover.")

        # 6. FINAL CONFIRM
        time.sleep(3)
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
