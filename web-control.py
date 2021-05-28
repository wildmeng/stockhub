from selenium import webdriver
from selenium.webdriver.common.keys import Keys
driver = webdriver.Chrome('C:\\Users\\Administrator\\Downloads\\chromedriver_win32\\chromedriver.exe')
driver.get("https://cn.tradingview.com/")
print(driver)
# driver.close()