import time
from selenium import webdriver

from webdriver_manager.chrome import ChromeDriverManager

def open_browser(url):
    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")
    options.add_argument("user-data-dir=C:/Users/xiaof/AppData/Local/Google/Chrome/User Data/Default");
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.get(url)
    return driver

url = "https://cn.tradingview.com/chart/jZLdvwX6/#signin"
driver = open_browser(url)