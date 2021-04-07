#!/usr/bin/env python

import sys
import math, re, time
import py3toolbox       as tb
import multiprocessing  as mp
import json

MODULE_NAME = "DataLogger"

def get_config():
  config = tb.load_json('./config.json')
  return config


# =================================================
#
# A simple logging class
#
# =================================================

class DataLogger(mp.Process):
  def __init__(self, q_in,  q_mon):
    mp.Process.__init__(self)
    self.config           = get_config()[MODULE_NAME]
    self.q_in             = q_in  
    self.q_mon            = q_mon
    self.data_lines       = ""
    self.last_updated     = time.time() 

  def log(self) :
    if get_config()['DataReader']['feed_channel'] == 'FILE' :
      return
    else:
      tb.rm_file('R:/data.log.data.txt')
      while True:
        self.data_lines = self.data_lines + "\n" + json.dumps(self.q_in.get())
        if time.time() - self.last_updated >= 5:
          tb.write_file(file_name = 'R:/data.log.data.txt', text=self.data_lines + "\n" , mode='a')
          self.data_lines   = ""
          self.last_updated = time.time()

  def run(self):
    self.q_mon.put(MODULE_NAME)
    self.log()
    pass

    