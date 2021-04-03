#!/usr/bin/env python

# =====================================================================
# This is a common class, which can read data from multiple channels,
# and then pass to output queue to be consumed by Monitor tools.
#
# Combined with the monitors, this utility can be used to collect 
# IOT/Robtics sensors data at real-time, or show 3D object movement
# of Gyro sensor.
#
# Avaliable channels:
# - File         : read data from file, normally for testing only
# - Serial Port  : 
# - Mouse        : Use mouse movements to generate random signals
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
#warnings.filterwarnings("ignore")

import os,sys,time,json
import collections
import serial
import socket
import queue
import threading
import multiprocessing 
import socketserver
import random
import numpy as np
import py3toolbox as tb
import pyautogui



q_thr = queue.Queue()



def get_mouse_pos():
  pos = pyautogui.position()
  return (pos.x, pos.y)


def get_config():
  config = tb.load_json('./config.json')
  return config



# =================================================
#
# TCP request handler
#
# =================================================
class TCPHandler(socketserver.StreamRequestHandler):
  def handle(self):
    while True:
      data = self.rfile.readline().strip().decode('utf-8')
      if not data: break        
      q_thr.put(data)
      if 'quit' in data :  break

# =================================================
#
# UDP request handler
#
# =================================================
class UDPHandler(socketserver.DatagramRequestHandler):
  def handle(self):
    while True:
      data = self.rfile.readline().strip().decode('utf-8')
      if not data: break        
      q_thr.put(data)
      if 'quit' in data :  break



# =================================================
#
# TCP server, running in seperate thread
#
# =================================================
class TCPServer(threading.Thread):
  def __init__(self, host, port): 
    super(TCPServer, self).__init__()
    self.host = host
    self.port = port
  
  def run(self):
    with socketserver.TCPServer((self.host, self.port), TCPHandler) as server :
      server.serve_forever()    

# =================================================
#
# UDP server, running in seperate thread
#
# =================================================
class UDPServer(threading.Thread):
  def __init__(self, host, port): 
    super(UDPServer, self).__init__()
    self.host = host
    self.port = port
  
  def run(self):
    with socketserver.UDPServer((self.host, self.port), UDPHandler) as server :
      server.serve_forever()   





# =================================================
#
#  Data Reader - main process, creates threading 
#  for TCP server/UDP server
#
# =================================================
class DataReader(multiprocessing.Process):
  def __init__(self, q_log, q_out):
    multiprocessing.Process.__init__(self)

    self.q_log            = q_log  
    self.q_out            = q_out

    self.config           = get_config()['DataReader']
    self.rawdata          = ""
    self.mapped_data      = {}
    self.count            = 0
    
    self.input_rate       = 0
    self.output_rate      = 0
    
    self.input_time       = time.time()
    self.input_time_prev  = 0
    self.input_rate       = 0
    self.output_time      = time.time()
    self.output_time_prev = 0
    self.noises           = np.random.normal(self.config['noise']['mean'], self.config['noise']['sigma'], size=10000)
    self.noise_level      = self.config['noise']['level']
    print (self.config)
  
  
    
  def mapdata(self,rawdata):
    # =========================================================
    # map raw data to json format
    # this needs to be customized for your own project
    #
    
    #print (rawdata);
    mapped_data = {}

    # read the data type
    for t in tb.re_findall (r'^(\w+):', rawdata) :
      mapped_data['Type'] = t

    # read the data
    for (k,v) in tb.re_findall (r'(\w+)\=\s*(\-*\d+\.*\d*|\d*)', rawdata) :
      mapped_data[k] = float(v)

    return mapped_data
    # =========================================================
 

  def log(self, message):
    #if self.config['logger']['enabled'] == True : 
    #  self.q_log.put (message)
    pass
      
    
  def get_input_rate(self):
    self.input_time   = time.time()
    if (self.input_time - self.input_time_prev) > 0:
      self.input_rate   = 1/(self.input_time - self.input_time_prev)
    else:
      self.input_rate = 9999
    self.input_time_prev  = self.input_time

  def output_data (self):
    if bool(self.mapped_data) :
      if self.config['throttle']['enabled'] == True:
        self.get_input_rate()
        self.q_out.put(self.mapped_data)
      else:
        self.q_out.put(self.mapped_data)
      
    


  ###############################################################
  #
  # Read data from File
  #
  ###############################################################
  def read_from_file(self):  
    data_lines = tb.read_file(file_name=self.config['channels']['FILE']['name'], return_type='list') 
    for line in data_lines:
      self.rawdata    = line
      self.mapped_data = self.mapdata(self.rawdata)
      self.output_data()
      

  ###############################################################
  #
  # Read data from Serial Port
  #
  ###############################################################
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
          self.mapped_data = self.mapdata(self.rawdata)
          self.output_data()
          self.rawdata = "" 
        else:
          self.rawdata += one_char
      
      except KeyboardInterrupt:
        exit(1)         
        
      except Exception as err:
        self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : err })
        pass         




  ###############################################################
  #
  # Read data from mouse movement
  #
  ###############################################################
  def read_from_mouse(self): 
    sample_rate = self.config['channels']['MOUSE']['sample_rate']
    while True:
      try:
        mX, mY = get_mouse_pos()
        if self.noise_level >0 :
          mX_noise = mX * (1 + self.noise_level * random.choice(self.noises))
          mY_noise = mY * (1 + self.noise_level * random.choice(self.noises))
          
        self.rawdata     = 'mouseX=' + str(mX_noise) + ',' + 'mouseY=' + str(mY_noise)
        self.mapped_data = self.mapdata(self.rawdata)
        self.output_data()
        time.sleep(1/sample_rate)
        
      except KeyboardInterrupt:
        exit(1)
        break    

  ###############################################################
  #
  # Read data from TCP Server
  #
  ###############################################################
  def read_from_tcpserver(self):
    while True:
      try :
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)
        client.connect((self.config['channels']['TCP_SVR']['host'] , self.config['channels']['TCP_SVR']['port'] ))
        print (self.config['channels']['TCP_SVR']['host'] + ":" + str(self.config['channels']['TCP_SVR']['port']) );
        print ("Connected.");
        while True:
          self.rawdata  = client.recv(4096).decode("utf-8")
          if len(self.rawdata.rstrip())==0 : continue
          self.mapped_data = self.mapdata(self.rawdata)
          self.output_data()   
          
      except KeyboardInterrupt:
        exit(1)              
      except Exception as e:
        print(str(e))
        pass

  def read_from_udpserver(self):
    pass
  
  def read_from_mqtt(self):
    pass
  
  ###############################################################
  #
  # Read data from TCP Client
  #
  ###############################################################
  def read_from_tcpclient(self) : 
    tcpsvr = TCPServer(host = '127.0.0.1', port = self.config['channels']['TCP_CLT']['port'])
    tcpsvr.start()
    while True:
      try:
        self.rawdata = q_thr.get()
        self.mapped_data = self.mapdata(self.rawdata)
        self.output_data() 
      except KeyboardInterrupt:
        exit(1)              

  ###############################################################
  #
  # Read data from UDP Client
  #
  ###############################################################
  def read_from_udpclient(self) : 
    udpsvr = UDPServer(host =  self.config['channels']['UDP_CLT']['host'], port = self.config['channels']['UDP_CLT']['port'])
    udpsvr.start()
    while True:
      try :
        self.rawdata = q_thr.get()
        self.mapped_data = self.mapdata(self.rawdata)
        self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mapped_data })
        self.output_data() 
      except KeyboardInterrupt:
        exit(1)              



  def run(self):
    # Dispatch to channel
    #self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Data Channel  : {}".format(self.config['feed_channel']) } )
    
    if self.config['feed_channel']   == 'FILE':
      self.read_from_file()
    elif self.config['feed_channel'] == 'SERIAL':
      self.read_from_serial()
    elif self.config['feed_channel'] == 'MOUSE':
      self.read_from_mouse()      
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
  dr = DataReader([q_data])
  dr.start()
  
    