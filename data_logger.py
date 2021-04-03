#!/usr/bin/env python

import sys
import math, re, time

# =================================================
#
# A simple logging class
#
# =================================================

class Logger(multiprocessing.Process):
  def __init__(self, q_log):  
    multiprocessing.Process.__init__(self)
    self.q_log        = q_log
    self.log_messages = {}
    self.timer        = time.time()
    
  def run(self):
    self.timer        = time.time()
    while True:
      try : 
        log_message = self.q_log.get(timeout=2)
        if log_message is not None:
          log_file = log_message['log_file']
          if log_file not in self.log_messages.keys():  
            self.log_messages[log_file] = []
          self.log_messages[log_file].append (log_message['log_content'])
        
        if (time.time() - self.timer) > 10:  # write log every 10 seconds
          for log_file in self.log_messages.keys():
            tb.write_file(file_name=log_file, text = '\n'.join(self.log_messages[log_file]) , mode='a')
            self.log_messages[log_file] = []
          self.timer = time.time()
      except :
        pass
  
    