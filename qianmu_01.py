from queue import Queue
import threading
import requests
import time
from lxml import etree

start_url = 'http://qianmu.iguye.com/2018USNEWS世界大学排名'

link_queue = Queue()
threads = []
DOWNLOADER_NUM = 10
download_page = 0
def fetch(url,raise_err = False):
    global download_page
    try:
        r = requests.get(url)
    except Exception as e:
        print(e)
    else:
        # print(r.text)
        download_page += 1
        #如果返回的状态码不是200,就报错
        if raise_err:
            r.raise_for_status()
    return r.text.replace('\t', '')

def parse(html):
    global link_queue
    selector = etree.HTML(html)
    links = selector.xpath('//*[@id="content"]/table/tbody/tr/td[2]/a/@href')
    for link in links:
        if not link.startswith('http://'):
            link = 'http://qianmu.iguye.com/%s' % link
        link_queue.put(link)
def parse_university(html):
    selector = etree.HTML(html)
    table = selector.xpath('//*[@id="wikiContent"]/div[1]/table/tbody')
    if not table:
        return
    table = table[0]
    keys = table.xpath('./tr/td[1]//text()')
    cols = table.xpath('./tr/td[2]')
    # values = table.xpath('.tr/td[2]//text()')
    values = [' '.join(col.xpath('.//text()')) for col in cols]
    #以下这四行等于上面那行
    # values = []
    # for col in cols:
    #     text = ' '.join(col.xpath('.//text()'))
    #     values.append(text)
    info = dict(zip(keys,values))
    print(info)

def downloader():
    while True:
        link = link_queue.get()
        if link is None:
            break
        parse_university(fetch(link))
        link_queue.task_done()
        print('remaining queue: %s' % link_queue.qsize())
if __name__ == '__main__':
    start_time = time.time()
    parse(fetch(start_url,raise_err = True))
    for i in range(DOWNLOADER_NUM):
        t = threading.Thread(target = downloader)
        t.start()
        threads.append(t)
    link_queue.join()
    #当link_queue.join()结束时,说明没有link了.
    #这时候我们在link_queue中发送Nnoe,告诉线程退出
    for i in range(DOWNLOADER_NUM):
        link_queue.put(None)
    for t in threads:
        t.join()
    cost_seconds = time.time() - start_time
    print('download %s pages,cost %s seonds' %(download_page,cost_seconds))