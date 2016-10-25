#! /usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import os
import hashlib
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import json
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')

def load_data(path):
  with open(path, 'r') as fd:
    content = fd.read()
  lst = content.split("\n")
  return lst

def get_json(word):
  url = "http://baike.baidu.com/api/openapi/BaikeLemmaCardApi?scope=103&format=json&appid=379020&bk_key=%s&bk_length=600&qq-pf-to=pcqq.discussion" % (word, )
  print url
  data = ''
  try:
    r = requests.get(url, timeout = 5)
  except Exception as e:
    print e
  else:
    data = r.text
  return data

def download(url, path):
  local_filename = url.split('/')[-1]  
  print "Download File=", local_filename  
  r = requests.get(url, stream=True)
  with open(path + local_filename, 'wb') as f:  
    for chunk in r.iter_content(chunk_size=1024):  
      if chunk:
        f.write(chunk)  
        f.flush()
    f.close()  
  return local_filename 

def save(item, out = "./data/dicts"):
  if not os.path.isdir(out):
    os.mkdir(out)

  item_dir = "%s/%s" % (out, item[0])
  if not os.path.isdir(item_dir):
    os.mkdir(item_dir)

  words = item[1].split(",")
  for w in words:
    filename = hashlib.md5(w).hexdigest()
    if os.path.isfile("%s/%s" % (item_dir, filename)):
      print "skip "+ w
      continue

    j = get_json(w)
    with open("%s/%s" % (item_dir, filename), "w") as fd:
      fd.write(j)

def save_image(item, out = "./data/dicts"):
  if not os.path.isdir(out):
    os.mkdir(out)

  item_dir = "%s/%s" % (out, item[0])
  if not os.path.isdir(item_dir):
    os.mkdir(item_dir)

  words = item[1].split(",")
  for w in words:
    filename = hashlib.md5(w).hexdigest()
    if not os.path.isfile("%s/%s" % (item_dir, filename)):
      print "file of "+ w + " not exists"
      continue
    else:
      with open("%s/%s" % (item_dir, filename), "r") as fd:
        o = fd.read()
        try:
          o = json.loads(o)
          img = item_dir + "/" + o['image'].split("/")[-1]
          if os.path.isfile(img):
            print "skip "+ img
            continue
          download(o["image"], item_dir + "/")
        except Exception as e:
          print e

def save_desc(item, out = "./data"):
  if not os.path.isdir(out):
    os.mkdir(out)

  item_dir = "%s/%s" % (out, item[0])
  if not os.path.isdir(item_dir):
    os.mkdir(item_dir)

  words = item[1].split(",")
  for w in words:
    filename = hashlib.md5(w).hexdigest()
    if not os.path.isfile("%s/%s" % (item_dir, filename)):
      print "file of "+ w + " not exists"
      continue
    else:
      with open("%s/%s" % (item_dir, filename), "r") as fd:
        o = fd.read()
        try:
          o = json.loads(o)
          if os.path.isfile(item_dir + '/' + filename + '_desc'):
            print "skip "+ filename + '_desc'
            continue
          with open(item_dir + '/' + filename + '_desc', "w") as f:
            f.write(o["abstract"])
            print o["abstract"]
        except Exception as e:
          print e

if __name__ == '__main__':
  lst_file = "./data/list.json"
  with open(lst_file, "r") as f:
    lst = f.read()
  dicts = []
  for k,v in json.loads(lst).items():
    for vv in v:
      dicts.append(vv)
  items = []
  for d in dicts:
    dict_file  = "./data/dicts/%s/dict.txt" % (d, )
    words = load_data(dict_file)
    items.append((d, ",".join(words)))

  pool = ThreadPool(16)
  pool.map(save, items)
  pool.close() 
  pool.join()

  pool = ThreadPool(16)
  pool.map(save_image, items)
  pool.close() 
  pool.join()

  pool = ThreadPool(16)
  pool.map(save_desc, items)
  pool.close() 
  pool.join()
