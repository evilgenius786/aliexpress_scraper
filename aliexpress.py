import datetime
import itertools
import os.path
import re
import sqlite3
import time
import csv
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

timeout = 5
debug = os.path.isfile('debug')
headless = False
images = False
max = True
incognito = False

data = []

headers = ["Item ID", "URL", "Variation", "Qty", "Price", "Shipping Price - Method(s)"]

conn = sqlite3.connect("database.db")
cursor = conn.cursor()


def viewDB():
    for data in cursor.execute("SELECT * FROM aliexpress").fetchall():
        print(data)


def createTable():
    # cursor.execute("DROP TABLE aliexpress")
    # conn.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS aliexpress
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itemid TEXT,
                    url TEXT,
                    variation TEXT,
                    qty TEXT,
                    price TEXT,
                    s_price_method TEXT,
                    checked TEXT)""")
    conn.commit()


def main():
    createTable()
    logo()
    os.system('color 0a')
    driver = getChromeDriver()
    # driver.delete_all_cookies()
    urls = open('urls.txt', 'r').read().splitlines()
    # driver.get(urls[0])
    # if not debug:
    #     changecountry(driver)
    while True:
        try:
            while True:
                cursor.execute("UPDATE aliexpress SET checked='false'")
                conn.commit()
                with open('aliexpress.csv', mode='w', newline='') as outfile:
                    csv.writer(outfile, delimiter=',').writerow(headers)
                    csv.writer(outfile, delimiter=',').writerows(cursor.execute("SELECT * FROM aliexpress").fetchall())
                for url in urls:
                    # while True:
                    #     try:
                    #         driver.get(url)
                    #         time.sleep(2)
                    #         break
                    #     except:
                    #         time.sleep(5)
                    #         pass
                    for element in driver.find_elements_by_xpath('//li[@class="sku-property-item selected"]'):
                        element.click()
                    while ">China</span>" in driver.page_source:
                        try:
                            getElement(driver, '//span[text()="China"]').click()
                            if "selected" in getElement(driver, '//li/div/*[text()="China"]/../..').get_attribute(
                                    'class'):
                                break
                        except:
                            pass
                    shipping = []
                    # while True:
                        # try:
                        #     click(driver, '//span[@class="product-shipping-info black-link"]', True)
                        #     time.sleep(2)
                        #     getElement(driver, '//div[@class="table-tr active"]')
                        #     for tr in getElements(driver, '//div[contains(@class,"table-tr")]')[1:]:
                        #         while len(tr.find_elements_by_xpath('./*')[2].text) < 4:
                        #             time.sleep(2)
                        #         td = tr.find_elements_by_xpath('./*')
                        #         shipping.append(f"{td[2].text}-{td[4].text}")
                        #     getElement(driver, '//button[text()="Apply"]').click()
                        #     break
                        # except Exception:
                        #     shipping = []
                        #     if debug:
                        #         traceback.print_exc()
                    try:
                        properties = []
                        for ul in getElements(driver, '//ul[@class="sku-property-list"]'):
                            varience = []
                            for div in ul.find_elements_by_xpath('./li[@class="sku-property-item"]/div'):
                                img = div.find_elements_by_xpath('./img')
                                span = div.find_elements_by_xpath('./span')
                                if len(img) > 0:
                                    varience.append(img[0])
                                elif len(span) > 0:
                                    if "Ships From" not in span[0].find_element_by_xpath('./../../../../div').text:
                                        varience.append(span[0])
                                else:
                                    print("Error")
                            if len(varience) > 0:
                                properties.append(varience)
                        combs = list(itertools.product(*properties))
                        for var in properties:
                            for x in var:
                                try:
                                    print(x.get_attribute('alt').strip())
                                except:
                                    print(x.text)
                        print("Properties",properties)
                        print("combs",combs)
                        for combination in combs:
                            variation = ""
                            for element in combination:
                                alt = element.get_attribute('alt')
                                text = element.text
                                if alt is not None:
                                    variation += alt + "/"
                                elif len(text) > 0:
                                    variation += text + "/"
                                else:
                                    print("Error")
                                if "selected" not in element.find_element_by_xpath('./../..').get_attribute('class'):
                                    element.click()
                                time.sleep(1)
                            time.sleep(1)
                            write(driver, variation, shipping, url)
                    except:
                        if debug:
                            traceback.print_exc()
                        write(driver, "No variation", shipping, url)
        except:
            pass


def changecountry(driver):
    while True:
        try:
            click(driver, '//*[@id="switcher-info"]')
            click(driver, '//a[@data-role="country"]')
            click(driver, '//li[@data-name="United States"]')
            click(driver, '//button[@class="ui-button ui-button-primary go-contiune-btn"]')
            break
        except:
            pass


def write(driver, variation, shipping, url):
    try:
        price = getElement(driver, '//span[@itemprop="price"]').text
    except:
        price = getElement(driver, '//span[@class="uniform-banner-box-price"]').text
    qty = getElement(driver, '//div[@class="product-quantity-tip"]/span').text
    qty = re.findall("\d+", qty)[0]
    itemid = re.search(r'item/(.*?)\.html', driver.current_url).group(1)
    info = [itemid, url, variation, qty, price]
    info.extend(shipping)
    print(info)
    data = cursor.execute(f"SELECT * FROM aliexpress WHERE itemid='{itemid}' AND variation='{variation}'").fetchone()
    if data is not None and len(data) > 0:
        change = False
        for i in range(len(info)):
            if data[i] != info[i]:
                change = True
                break
        if change:
            filename = str(datetime.datetime.now()).replace(":", "")
            if not os.path.isfile(filename):
                with open(f'{filename}.csv', mode='a', newline='') as outfile:
                    csv.writer(outfile, delimiter=',').writerow(headers)
            print(f"{filename} Changed from", data, "to", info)
            with open(f'{filename}.csv', mode='a', newline='') as outfile:
                csv.writer(outfile, delimiter=',').writerow(data)
                csv.writer(outfile, delimiter=',').writerow(info)
            cursor.execute(f"UPDATE aliexpress SET qty='{qty}',price='{price}',s_price_method='{shipping}' WHERE "
                           f"itemid='{itemid}' AND variation='{variation}'")
            conn.commit()
        else:
            print("Nothing changed", data)
            cursor.execute(f"UPDATE aliexpress SET checked='true' WHERE itemid='{itemid}' AND variation='{variation}'")
            conn.commit()
    else:
        print("Data added to database", data)
        cursor.execute(
            f"INSERT INTO aliexpress SET itemid='{itemid}',url='{url}',variation='{variation},qty='{qty}',price='{price}',s_price_method='{shipping}''")


def click(driver, xpath, js=False):
    if js:
        driver.execute_script("arguments[0].click();", getElement(driver, xpath))
    else:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def getElement(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))


def getElements(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))


def sendkeys(driver, xpath, keys, js=False):
    if js:
        driver.execute_script(f"arguments[0].value='{keys}';", getElement(driver, xpath))
    else:
        getElement(driver, xpath).send_keys(keys)


def getChromeDriver(proxy=None):
    options = webdriver.ChromeOptions()
    if debug:
        # print("Connecting existing Chrome for debugging...")
        options.debugger_address = "127.0.0.1:9222"
    else:
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if not images:
        # print("Turning off images to save bandwidth")
        options.add_argument("--blink-settings=imagesEnabled=false")
    if headless:
        # print("Going headless")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    if max:
        # print("Maximizing Chrome ")
        options.add_argument("--start-maximized")
    if proxy:
        # print(f"Adding proxy: {proxy}")
        options.add_argument(f"--proxy-server={proxy}")
    if incognito:
        # print("Going incognito")
        options.add_argument("--incognito")
    return webdriver.Chrome(options=options)


def getFirefoxDriver():
    options = webdriver.FirefoxOptions()
    if not images:
        # print("Turning off images to save bandwidth")
        options.set_preference("permissions.default.image", 2)
    if incognito:
        # print("Enabling incognito mode")
        options.set_preference("browser.privatebrowsing.autostart", True)
    if headless:
        # print("Hiding Firefox")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    return webdriver.Firefox(options)


def logo():
    print(""" 
       _____  .__  .__  ___________                                           
      /  _  \ |  | |__| \_   _____/__  ________________   ____   ______ ______
     /  /_\  \|  | |  |  |    __)_\  \/  /\____ \_  __ \_/ __ \ /  ___//  ___/
    /    |    \  |_|  |  |        \>    < |  |_> >  | \/\  ___/ \___ \ \___ \ 
    \____|__  /____/__| /_______  /__/\_ \|   __/|__|    \___  >____  >____  >
            \/                  \/      \/|__|               \/     \/     \/ 
                                                                                              
======================================================================================
    Data scraping and monitoring tool by: https://www.fiverr.com/muhammadhassan7/
======================================================================================
""")


if __name__ == "__main__":
    main()
    # conn.close()
