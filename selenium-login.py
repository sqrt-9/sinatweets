# -*- coding: utf-8 -*-
"""
Created on Thu Dec 08 11:39:42 2016

@author: Administrator
"""

import time
from selenium import webdriver

import requests

# 直接登陆新浪微博
url = 'http://weibo.com/login.php'

driver = webdriver.PhantomJS()
driver.maximize_window()
driver.get(url)
print('开始登陆')

# 定位到账号密码表单
login_tpye = driver.find_element_by_class_name('info_header').find_element_by_xpath('//a[2]')
login_tpye.click()
time.sleep(3)

name_field = driver.find_element_by_id('loginname')
name_field.clear()
name_field.send_keys('pl60896716@163.com')

password_field = driver.find_element_by_class_name('password').find_element_by_name('password')
password_field.clear()
password_field.send_keys('xx1234')


submit = driver.find_element_by_class_name('W_login_form').find_element_by_link_text('登录')
submit.click()

# 等待页面刷新，完成登陆
time.sleep(5)
print('登陆完成')
driver.get('http://weibo.com/5020817543/profile?is_all=1')
print(driver.current_url)
sina_cookies = driver.get_cookies()

cookie = [item["name"] + "=" + item["value"] for item in sina_cookies]
cookiestr = '; '.join(item for item in cookie)
#print(cookiestr)


#redirect_url = 'http://weibo.com/5020817543/profile?is_all=1'
#headers = {'cookie': cookiestr}
#html = requests.get(redirect_url, headers=headers).text
#print(html)

