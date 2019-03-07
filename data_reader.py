#!/usr/bin/env python

# =====================================================================
# This is a common class, which can read data from multiple channels,
# and then pass to output queue, which will be consumed by Monitors.
#
# Combined with the monitors, this utility can be used to monitor 
# IOT/Robtics sensors data at real-time, or show 3D object movement
# of Gyro sensor.
#
# Avaliable channels:
# - File         : read data from file, normally for testing only
# - Serial Port  : 
# - TCP Server
# - TCP Client
# - UCP Server
# - UCP Client
# - MQTT
# - ......
# 
# Main configuration file : config.json
# Data format             : CSV
#
# =====================================================================

 
import warnings
warnings.filterwarnings("ignore")

import os,sys,time,json
import collections
import serial
import socket
import queue
import threading
import multiprocessing 
import socketserver
import py3toolbox as tb


q_thr = queue.Queue()



def get_config():
  return tb.load_json('./config.json')

class TCPHandler(socketserver.StreamRequestHandler):
  def handle(self):
    while True:
      data = self.rfile.readline().strip().decode('utf-8')
      if not data: break        
      q_thr.put(data)
      if 'quit' in data :  break


class Thr2ProcBridge(threading.Thread):
  def __init__(self, q_thr, q_proc):
    super(Thr2ProcBridge, self).__init__()
    self.q_thr  = q_thr
    self.q_proc = q_proc
    
  def run(self):
    while True:
      self.q_proc.put(self.q_thr.get())   
      print (self.q_proc.qsize())

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
            tb.write_file(file_name=log_file, text = '\n'.join(self.log_messages[log_file]), mode='a')
            self.log_messages[log_file] = []
          self.timer = time.time()
      except :
        pass
        
class DataReader(multiprocessing.Process):
  def __init__(self, q_out, q_log):
    multiprocessing.Process.__init__(self)

    self.q_out        = q_out
    self.q_log        = q_log
    self.config       = get_config()['DataReader']
    self.rawdata      = ""
    self.mappeddata   = {}
    self.count        = 0
    print (self.config)
    
    
  def mapdata(self,rawdata):
    # =========================================================
    # map raw data to json format
    # this needs to be customized for your own project
    #
    #rawtext = ''
    
    
    
    return rawdata
    # =========================================================
 

  def log(self, message):
    if self.config['logger']['enabled'] == True : 
      self.q_log.put (message)
    
    
  def output_data (self):
    self.q_out.put(self.mappeddata)
 

  def read_from_file(self):  
    file = self.config['channels']['FILE']['name']
    data_lines = tb.read_file(file_name=self.config['channels']['FILE']['name'], return_type='list') 
    for line in data_lines:
      self.rawdata    = line
      self.mappeddata = self.mapdata(self.rawdata)
      self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
      self.output_data()
      


 
  def read_from_serial(self):  
    ser = serial.Serial(  port      = self.config['channels']['SERIAL']['port']       , 
                          baudrate  = self.config['channels']['SERIAL']['baud_rate']  , 
                          timeout   = self.config['channels']['SERIAL']['timeout']
                       )

    self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Connected to: {}".format(ser.port) } )

    while True:
      try :
        one_char = ""
        one_byte = ser.read(1)
        if len(one_byte) < 1 : continue
        try :
          one_char = one_byte.decode('utf-8')
        except Exception as err:  
          one_char = ""
        
        # EOL detected
        if one_byte == b"\r" and ser.read(1) == b"\n": 
          self.count +=1
          self.mappeddata = self.mapdata(self.rawdata)
          self.log({ 'log_file' : self.config['logger']['data_input']  ,  'log_content' : self.rawdata    })
          self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
          self.output_data()
          self.rawdata = "" 
        else:
          self.rawdata += one_char
          
      except Exception as err:
        self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : err })
        pass         



  def read_from_tcpserver(self):
    PASS
  

  def read_from_tcpclient(self) : 
    port = self.config['channels']['TCP_CLT']['port']
    thr2proc = Thr2ProcBridge(q_thr,self.q_out)
    thr2proc.start()
    with socketserver.TCPServer(('127.0.0.1', port), TCPHandler) as server :
      server.serve_forever()
   
  def run(self):
    # Dispatch to channel
    self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Data Channel  : {}".format(self.config['feed_channel']) } )
    if self.config['feed_channel']   == 'FILE':
      self.read_from_file()
    elif self.config['feed_channel'] == 'SERIAL':
      self.read_from_serial()
    elif self.config['feed_channel'] == 'TCP_SVR':
      self.read_from_tcpserver()
    elif self.config['feed_channel'] == 'TCP_CLT':
      self.read_from_tcpclient()
    elif self.config['feed_channel'] == 'UDP_SVR':
      self.read_from_udpserver()
    elif self.config['feed_channel'] == 'UDP_CLT':
      self.read_from_udpclient()
    elif self.config['feed_channel'] == 'MQTT':
      self.read_from_mqtt()     
        
if __name__ == '__main__':   
  q_data = multiprocessing.Queue()  
  q_log  = multiprocessing.Queue()  
  dr     = DataReader(q_data,q_log)
  logger = Logger(q_log)
  logger.start()
  dr.start()
  
    