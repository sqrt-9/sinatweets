import json
import os
import base64
import requests
import logging
from SinaSpider.accountDispose import account

logger = logging.getLogger(__name__)

weibo_account = account()

def getCookie(account,password):
    loginURL = r'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
    username = base64.b64encode(account.encode('utf-8')).decode('utf-8')
    postData = {
            'entry':'sso',
            'gateway':'1',
            'from':'null',
            'savestate':'30',
            'useticket':'0',
            'pagerefer':'',
            'vsnf':'1',
            'su':username,
            'service':'sso',
            'sp':password,
            'sr':'1440*900',
            'encoding':'UTF-8',
            'cdult':'3',
            'domain':'sina.com.cn',
            'prelt':'0',
            'returntype':'TEXT',
            }
    session = requests.Session()
    response = session.post(loginURL,data=postData)
    jsonStr = response.content.decode('gbk')
    info = json.loads(jsonStr)
    if info['retcode'] == '0':
        logger.warning("GET COOKIE SUCCESS!(ACCOUNT:{0})".format(account))
        cookie = session.cookies.get_dict()
        return json.dumps(cookie)
    else:
        logger.warning("FAILED!(REASON:{0})".format(info['reason']))
        return ("")

def initCookie(rconn, spiderName):
    """获取所有帐号的Cookies， 存入Redis。如果Redis已有该帐号的Cookie， 则不再获取。"""
    for weibo in weibo_account:
        if rconn.get("{0}:Cookies:{1}--{2}".format(spiderName, weibo['username'], weibo['password'])) is None:  #'SinaSpider:Cookies:帐号--密码'，为None即为不存在。
            cookie = getCookie(weibo['username'], weibo['password'])
            if len(cookie) > 0:
                key = "{0}:Cookies:{1}--{2}".format(spiderName, weibo['username'], weibo['password'])
                rconn.set(key, cookie)
    cookieNum = "".join(str(i) for i in rconn.keys()).count("SinaSpider:Cookies")
    logger.warning("The num of the cookies is {0}".format(cookieNum))
    if cookieNum == 0:
        logger.warning('Stopping...')
        os.system("echo Press enter to continue; read dummy;")

def updateCookie(accountText, rconn, spiderName):
    """更新一个帐号的Cookie"""
    account = accountText.split("--")[0]
    password = accountText.split("--")[1]
    cookie = getCookie(account, password)
    if len(cookie) > 0:
        logger.warning("The cookie of {0} has been updated successfully!".format(account))
        rconn.set("{0}:Cookies:{1}".format(spiderName,accountText), cookie)
    else:
        logger.warning("The cookie of {0} updated failed! Remove it!".format(accountText))
        removeCookie(accountText, rconn, spiderName)

def removeCookie(accountText, rconn, spiderName):
    """删除某个帐号的Cookie"""
    rconn.delete("{0}:Cookies:{1}".format(spiderName, accountText))
    cookieNum = "".join(rconn.keys()).count("SinaSpider:Cookies")
    logger.warning("The num of the cookies left is {0}".format(cookieNum))
    if cookieNum == 0:
        logger.warning("Stopping...")
        os.system('echo Press enter to continue; read dummy;')


