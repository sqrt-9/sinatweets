import re

def tweetDispose(n):
    if isinstance(n,str):
        n = n.replace('【','').replace('】','').replace('『','').replace('』','').replace('☆','').replace('◈','').replace('✿','').replace('☼','').replace('※','').replace('☂','').replace('秒拍视频','').replace('分享视频','').replace('APP下载地址','').replace('全文','').replace('\xa0','')
        regex = r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))'  #匹配任意网址
        n = re.sub(regex,'',n)
        n = re.sub(r'\[.*?\]','',n)
        n = re.sub(r'[+vx:]\w+','',n)
        n = re.sub(r'（.*?[直播|录制|来自].*?）','',n)
        return n
    elif isinstance(n,list):
        m = []
        for i in n:
            m.append(tweetDispose(i))
        return m

if __name__ == '__main__':
    pass
