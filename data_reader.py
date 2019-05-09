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


class UDPHandler(socketserver.DatagramRequestHandler):
  def handle(self):
    while True:
      data = self.rfile.readline().strip().decode('utf-8')
      print (data)
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
            tb.write_file(file_name=log_file, text = '\n'.join(self.log_messages[log_file]), mode='a')
            self.log_messages[log_file] = []
          self.timer = time.time()
      except :
        pass


# =================================================
#
#  Data Reader - main process, creates threading 
#  for TCP server/UDP server
#
# =================================================
class DataReader(multiprocessing.Process):
  def __init__(self, q_out):
    multiprocessing.Process.__init__(self)

    self.q_out        = q_out
    self.q_log        = multiprocessing.Queue()  
    self.config       = get_config()['DataReader']
    self.rawdata      = ""
    self.mappeddata   = {}
    self.count        = 0
    
    self.input_rate   = 0
    self.output_rate  = 0
    
    self.input_time       = time.time()
    self.input_time_prev  = 0
    self.input_rate       = 0
    self.output_time      = time.time()
    self.output_time_prev = 0
    
    self.logger           = Logger(self.q_log)
    self.logger.start()
    print (self.config)

  
    
  def mapdata(self,rawdata):
    # =========================================================
    # map raw data to json format
    # this needs to be customized for your own project
    # 
    #rawtext = ''

    yaw_matched = tb.re_findall   ('Yaw=(\-*\d+\.\d*)/i',   rawdata)
    
    
    print (yaw_matched)
    exit(1)
    
    pitch_matched = tb.re_findall ('Pitch=(\-*\d+\.\d*)/i', rawdata)
    roll_matched = tb.re_findall  ('Roll=(\-*\d+\.\d*)/i',  rawdata)
    mappeddata = {
      "Yaw"     : float(yaw_matched[0][0]),
      "Pitch"   : float(pitch_matched[0][0]),
      "Roll"    : float(roll_matched[0][0])
    }
    print (mappeddata)
    return mappeddata
    # =========================================================
 

  def log(self, message):
    if self.config['logger']['enabled'] == True : 
      self.q_log.put (message)
    
  def get_input_rate(self):
    self.input_time   = time.time()
    if (self.input_time - self.input_time_prev) > 0:
      self.input_rate   = 1/(self.input_time - self.input_time_prev)
    else:
      self.input_rate = 9999
    self.input_time_prev  = self.input_time

  def output_data (self):
    self.get_input_rate()
    if self.config['throttle']['enabled'] == True:
      self.output_time   = time.time()
      if (self.output_time - self.output_time_prev) >0:
        self.output_rate   = 1/(self.output_time - self.output_time_prev)
      else:
        self.output_rate = 9999
      if self.output_rate <= self.config['throttle']['output_rate'] :
        self.q_out.put(self.mappeddata)
        print (self.mappeddata)
        self.output_time_prev  = self.output_time
    else:
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
    pass
  

  def read_from_tcpclient(self) : 
    tcpsvr = TCPServer(host = '127.0.0.1', port = self.config['channels']['TCP_CLT']['port'])
    tcpsvr.start()
    while True:
      self.rawdata = q_thr.get()
      self.mappeddata = self.mapdata(self.rawdata)
      self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
      self.output_data() 

  def read_from_udpclient(self) : 
    udpsvr = UDPServer(host =  self.config['channels']['UDP_CLT']['host'], port = self.config['channels']['UDP_CLT']['port'])
    udpsvr.start()
    while True:
      self.rawdata = q_thr.get()
      self.mappeddata = self.mapdata(self.rawdata)
      self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
      self.output_data() 



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
  dr     = DataReader(q_data)
  dr.start()
  
    