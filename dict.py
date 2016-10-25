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

def _cate_name(cid):
  url = "http://pinyin.sogou.com/dict/cate/index/%s" % (cid, )
  try:
    r = requests.get(url, headers = h)
    soup = bs(r.text)
    name = soup.select("title")[0].text.split("_")[0]
    print "id %s's name is %s" % (cid, name)
    logging.info("id %s's name is %s" % (cid, name))
    return name
  except Exception as e:
    print e
    return ""

def dict_tree():
  index = "http://pinyin.sogou.com/dict/cate/index/"
  ret  = {}
  try:
    logging.info("Start to get dict tree ...")
    r = requests.get(index, headers = h)
    soup = bs(r.text)
    cate = soup.select(".nav_list a")
    index_ids = [c["href"].split("/")[-1] for c in cate]
    pool = ThreadPool(4)
    r = pool.map(_sub_cate, index_ids)
    pool.close() 
    pool.join()
    for i in range(len(index_ids)):
      ret[index_ids[i]] = r[i] 
    tree = {}
    q = []
    for k,v in ret.items():
      for kk,vv in v.items():
        if not k in tree:
          tree[k] = {}
        if not kk in tree[k]:
          tree[k][kk] = {}
        if len(vv) == 0:
          q.append(kk)
        for i in vv:
          if not i in tree[k][kk]:
            q.append(i)
    
    pool = ThreadPool(16)
    r = pool.map(_cate_list, q)
    pool.close() 
    pool.join()

    n = 0
    for k,v in ret.items():
      for kk,vv in v.items():
        if not k in tree:
          tree[k] = {}
        if not kk in tree[k]:
          tree[k][kk] = {}
        if len(vv) == 0:
          tree[k][kk] = r[n]
          n += 1
        for i in vv:
          if not i in tree[k][kk]:
            tree[k][kk][i] = r[n]
            n += 1
  except Exception as e:
    logging.info("Failed to get dict tree .")
    print e
  logging.info("End to get dict tree ...")
  return tree

def _sub_cate(cid):
  url = "http://pinyin.sogou.com/dict/cate/index/%s" % (cid, )
  try:
    r = requests.get(url, headers = h)
    soup = bs(r.text)
    cates = {}
    no_child = [a["href"].split("/")[-1] for a in soup.select(".cate_words_list .cate_no_child a")]
    for i in no_child:
      cates[i] = []
    has_child = [a["href"].split("/")[-1] for a in soup.select(".cate_words_list .cate_has_child a")]
    child = soup.select(".cate_child_words_list")
    g = []
    for c in child:
      g.append([i["href"].split("/")[-1] for i in c.select("a")])
    for j in range(len(has_child)):
      cates[has_child[j]] = g[j]
  except Exception as e:
    print e
  return cates
    

def _cate_list(cid):
  url = "http://pinyin.sogou.com/dict/cate/index/%s/default/%s"
  num = _get_cate_pagenum(cid)  
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
  url = "http://pinyin.sogou.com/dict/cate/index/%s" % (cid, )
  try:
    logging.info("Get page number of %s " % (cid, ))
    r = requests.get(url, headers = h)
    soup = bs(r.text)
    num = soup.select("#dict_page_list li a")[-2].text
    return int(num)
  except Exception as e:
    logging.info("Failed to get page number of %s " % (cid, ))
    print e
    return 1
  return 1

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
      info["name"] = soup.select("title")[0].text.split("_")[0]
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

  tree_file = "%s/%s" % (path, "tree.json")
  if os.path.isfile(tree_file):
    with open(tree_file) as f:
      c = f.read()
    if len(c) > 0:
      tree = json.loads(c)
    else:
      tree = dict_tree()
      _save(json.dumps(lst), "tree.json", path)
  else:
    tree = dict_tree()
    _save(json.dumps(lst), "tree.json", path)

  
  name_file = "%s/%s" % (path, "name.json")
  if not os.path.isfile(name_file):
    names = []
    for k,v in tree.items():
      names.append(k)
      for kk,vv in v.items():
        if isinstance(vv, list):
          names.append(kk)
        else:
          for kkk, vvv in vv.items():
            names.append(kkk)
  
    pool = ThreadPool(16)
    n = pool.map(_cate_name, names)
    pool.close() 
    pool.join()
    name = {}
    for i in range(len(names)):
      name[names[i]] = n[i]
    _save(json.dumps(name), "name.json", path)
    logging.info("Name done")
    
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
