import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from tkinter import messagebox

COOKIE_FILE = 'cookies.json'


# 保存cookies
def save_cookies(cookies):
    with open(COOKIE_FILE, 'w') as f:
        json.dump(cookies, f)


# 加载cookies
def load_cookies():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            return json.load(f)
    return None


# 获取谷歌浏览器驱动路径
def get_chrome_driver_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'chromedriver.exe')  # 打包
    else:
        return os.path.join(os.path.dirname(__file__), 'chromedriver.exe')  # 开发环境


# 获取cookies
def get_cookies_from_browser(url):
    # 提示
    messagebox.showinfo("注意", "需手动登录后台，要求账号包含后台子包基础库权限，后台登录成功后请勿关闭浏览器，单击“确定”继续")
    chrome_driver_path = get_chrome_driver_path()
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    # 提示
    messagebox.showinfo("手动登录完成确认", "请手动登录后单击“确定”继续(点击继续前请勿关闭浏览器)")
    # 获取Cookie
    cookies = driver.get_cookies()
    driver.quit()
    return cookies
