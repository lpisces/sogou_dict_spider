#! /usr/bin/env python
# -*- coding:utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import logging
import sys
import os
import json

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

def _download_dict(cid, path = "./data/dicts/"):
  url = "http://pinyin.sogou.com/dict/download_txt.php?id=%s" % (cid, )
  if not os.path.isfile("%s%s/%s" % (path, cid, "dict.txt")):
    r = requests.get(url, headers = h)
    _save(r.text, "dict.txt", "%s%s/" % (path, cid))
    logging.info("Got dict of %s ." % (cid, ))
  else:
    logging.info("Skip dict of %s ." % (cid, ))

def _get_dict_info(cid, path = "./data/dicts/"):
  url = "http://pinyin.sogou.com/dict/detail/index/%s" % (cid, )
  info = {}
  try:
    if not os.path.isfile("%s%s/%s" % (path, cid, "info1.json")):
      r = requests.get(url, headers = h)
      soup = bs(r.text)
      box = soup.select("#dict_info_content")[0]
      info["cnt"] = box.select(".dict_info_list ul li")[0].text.encode('utf-8')
      info["creator"] = box.select(".dict_info_list ul li")[1].text.encode("utf-8")
      info["size"] = box.select(".dict_info_list ul li")[2].text.encode("utf-8")
      info["updated_at"] = box.select(".dict_info_list ul li")[3].text.encode('utf-8')
      info["version"] = box.select(".dict_info_list ul li")[4].text.encode("utf-8")
      info["intro"] = box.select("#dict_info_intro .dict_info_str")[0].text
      _save(json.dumps(info), "info.json", "%s%s/" % (path, cid))
      logging.info("Got info of %s ." % (cid, ))
    else:
      logging.info("Skip info of %s ." % (cid, ))
    return True
  except Exception as e:
    print e
    return False

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

def go(path = "./data/"):
  lst_file = "%s/%s" % (path, "list.json")
  if os.path.isfile(lst_file):
    with open(lst_file) as f:
      c = f.read()
    if len(c) > 0:
      lst = json.loads(c)
    else:
      lst = dict_list()
      _save(json.dumps(lst), "list.json", path)
  else:
    lst = dict_list()
    _save(json.dumps(lst), "list.json", path)
    
  s = []
  for k, v in lst.items():
    for i in v:
      s.append(i)

  pool = ThreadPool(16)
  pool.map(_download_dict, s)
  pool.close() 
  pool.join()
  logging.info("Dict done")

  pool = ThreadPool(16)
  pool.map(_get_dict_info, s)
  pool.close() 
  pool.join()
  logging.info("Info done")


if __name__ == '__main__':
  go()
  
