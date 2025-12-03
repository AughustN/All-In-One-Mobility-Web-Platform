# pasgo_scraper_FINAL_WORKING.py
# Works perfectly with real pagination (1 2 3 ...) on PasGo.vn — Dec 2025

import os
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------- CONFIG ----------------------
CSV_FILE = "pasgo_restaurants_hcm.csv"
IMAGE_BASE_FOLDER = "images/restaurant"
os.makedirs(IMAGE_BASE_FOLDER, exist_ok=True)

# ---------------------- SETUP CHROME ----------------------
options = Options()
# options.add_argument("--headless")        # ← Remove comment when happy
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

def clean_name(name):
    return "".join(c if c not in '<>:"/\\|?*' else "_" for c in name.strip())[:120]

def download_image(driver, folder):
    img_url = None
    try:
        img_url = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        pass
    if not img_url:
        try:
            img = driver.find_element(By.XPATH, "//img[contains(@src,'pasgo.vn') or contains(@alt,'restaurant')]")
            img_url = img.get_attribute("src") or img.get_attribute("data-src")
        except:
            pass
    if img_url and img_url.startswith("http"):
        try:
            r = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            r.raise_for_status()
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "cover.jpg")
            with open(path, "wb") as f:
                f.write(r.content)
            return path.replace("\\", "/")
        except:
            pass
    return None

def scrape_pasgo():
    driver.get("https://www.pasgo.vn/ho-chi-minh/nha-hang")
    time.sleep(10)

    all_urls = set()
    current_page = 1

    print("Collecting all restaurant links from all pages...\n")

    while True:
        print(f"Loading Page {current_page}...")
        driver.get(f"https://www.pasgo.vn/ho-chi-minh/nha-hang?page={current_page}")
        time.sleep(6)

        links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Đặt chỗ ngay')]")
        new_links = [link.get_attribute("href") for link in links if link.get_attribute("href")]
        all_urls.update(new_links)
        print(f"   Page {current_page}: +{len(new_links)} → Total: {len(all_urls)}")

        # Look for next page number button (e.g. "2", "3", etc.)
        try:
            next_page_num = current_page + 1
            next_btn = driver.find_element(By.XPATH, f"//ul[contains(@class,'pagination')]//a[text()='{next_page_num}' and not(contains(@class,'active'))]")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
            time.sleep(1)
            next_btn.click()
            current_page += 1
            time.sleep(4)
        except NoSuchElementException:
            print("   No more page buttons → reached the end!")
            break
        except ElementClickInterceptedException:
            try:
                driver.execute_script("arguments[0].click();", next_btn)
                current_page += 1
                time.sleep(4)
            except:
                print("   Cannot click next page → finished")
                break

    print(f"\nFound {len(all_urls)} unique restaurants! Starting download...\n")

    # Now scrape details
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "address", "basic_info", "image_local_path", "pasgo_url"])

        count = 0
        for url in all_urls:
            count += 1
            try:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(url)
                time.sleep(6)

                name = driver.find_element(By.TAG_NAME, "h1").text.strip()

                # Address after pipe |
                address = "N/A"
                try:
                    txt = driver.find_element(By.XPATH, "//*[contains(text(),'│') or contains(text(),' | ')]").text
                    if "│" in txt or "|" in txt:
                        address = txt.split("│", 1)[-1].split("|", 1)[-1].strip()
                except:
                    pass

                # Deals
                deals = [e.text.strip() for e in driver.find_elements(By.XPATH, "//strong[contains(text(),'Giảm')] | //p[contains(text(),'Giảm')]")[:4]]
                basic_info = " | ".join(deals) if deals else "No deal"

                folder = os.path.join(IMAGE_BASE_FOLDER, clean_name(name))
                img_path = download_image(driver, folder)

                writer.writerow([name, address, basic_info, img_path or "", url])
                print(f"   Saved #{count}: {name} | Image: {'Yes' if img_path else 'No'}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(2)

            except Exception as e:
                print(f"   Error #{count}: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

    print(f"\nCOMPLETED! {count} restaurants saved to {CSV_FILE}")
    driver.quit()

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    scrape_pasgo()