#! /usr/bin/env python
# -*- coding:utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import logging
import sys
import os

reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(filename='dict.log', filemode='a', level=logging.DEBUG, format='[%(asctime)s]\t%(message)s', datefmt="%Y/%m/%d %H:%M:%S")
logging.getLogger("requests").setLevel(logging.WARNING)

h = {"Accept-Encoding": "gzip, deflate, sdch", "user_agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36"}

def dict_list():
  index = "http://pinyin.sogou.com/dict/cate/index/"
  ret  = {}
  try:
    logging.info("Start to get dict index ...")
    r = requests.get(index, headers = h)
    soup = bs(r.text)
    cate = soup.select(".nav_list a")
    index_ids = [c["href"].split("/")[-1] for c in cate]
    pool = ThreadPool(4)
    r = pool.map(_cate_list, index_ids)
    pool.close() 
    pool.join()
    for i in range(len(index_ids)):
      ret[index_ids[i]] = r[i] 
  except Exception as e:
    logging.info("Failed to get dict index .")
    print e
  logging.info("End to get dict index ...")
  return ret

def _cate_list(cid):
  url = "http://pinyin.sogou.com/dict/cate/index/%s/default/%s"
  num = _get_cate_pagenum(cid)  
  if num == 0:
    return [] 
  ids = []
  for i in range(1, num + 1):
    u = url % (cid, i)
    logging.info("Get items of %s in page %s" % (cid, i))
    try:
      r = requests.get(u, headers = h)
      soup = bs(r.text)
      ids += [j["href"].split("/")[-1] for j in soup.select(".detail_title a")]
    except Exception as e:
      logging.info("Failed to get items of %s in page %s" % (cid, i))
      print e
  return ids

def _get_cate_pagenum(cid):
  url = "http://pinyin.sogou.com/dict/cate/index/%s/default/1" % (cid, )
  try:
    logging.info("Get page number of %s " % (cid, ))
    r = requests.get(url, headers = h)
    soup = bs(r.text)
    num = soup.select("#dict_page_list li a")[-2].text
    return int(num)
  except Exception as e:
    logging.info("Failed to get page number of %s " % (cid, ))
    print e
  return 0

def _download(tup):
  url = tup[0]
  path = tup[1]

def _save(content, filename, path):
  try:
    if not os.path.isdir(path):
      _mkdir(path)
    with open(path + filename, "w") as f:
      f.write(content)
    return True
  except Exception as e:
    print e
    return False

def _mkdir(path):
  try:
    p = path.split("/")
    p = ["/".join(p[:i+1]) for i in range(len(p))][1:]
    for i in p:
      if not os.path.isdir(i):
        os.mkdir(i)
    return True
  except Exception as e:
    print e
    return False

if __name__ == '__main__':
  lst = dict_list() 
  
