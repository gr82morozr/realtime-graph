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
import multiprocessing 
import py3toolbox as tb



def get_config():
  return tb.load_json('./config.json')


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
 

  def read_file(self):  
    file = self.config['channels']['FILE']['name']
    data_lines = tb.read_file(file_name=self.config['channels']['FILE']['name'], return_type='list') 
    for line in data_lines:
      self.rawdata    = line
      self.mappeddata = self.mapdata(self.rawdata)
      self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
      self.output_data()
      


 
  def read_serial(self):  
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



  def read_tcpserver(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.bind(('', self.config['TCP_SERVER']['port']))
    self.sock.listen(5)
    self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Listening on {}".format(self.config['TCP_SERVER']['port']) } )
    try:
      while True:
        client_socket, client_address = sock.accept()
        self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Connected from {}".format(client_address) } )
        # loop serving the new client
        while True:
          self.rawdata = client_socket.recv(4096).decode("utf-8")
          if not self.rawdata: break
          self.mappeddata = self.mapdata(self.rawdata)
          self.log({ 'log_file' : self.config['logger']['data_input']  ,  'log_content' : self.rawdata    })
          self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
          self.output_data()          
          
        client_socket.close(  )
        self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Disconnected from {}".format(client_address) } )
    finally:
      self.sock.close()
  

  def read_tcpclient(self) : 
    remote_host = self.config['TCP_CLIENT']['host']
    remote_port = self.config['TCP_CLIENT']['port']
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((remote_host, remote_port))
    
    while True:
      try :
        self.rawdata = client.recv(4096).decode("utf-8")
        self.mappeddata = self.mapdata(self.rawdata)
        self.log({ 'log_file' : self.config['logger']['data_input']  ,  'log_content' : self.rawdata    })
        self.log({ 'log_file' : self.config['logger']['data_output'] ,  'log_content' : self.mappeddata })
        self.output_data()
      except Exception as err:
        self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : err })
        pass  
   
  def run(self):
    # Dispatch to channel
    self.log({ 'log_file' : self.config['logger']['script_log'] , 'log_content' : "Data Channel  : {}".format(self.config['feed_channel']) } )
    if self.config['feed_channel']   == 'FILE':
      self.read_file()
    elif self.config['feed_channel'] == 'SERIAL':
      self.read_serial()
    elif self.config['feed_channel'] == 'TCP_SERVER':
      self.read_tcpserver()
    elif self.config['feed_channel'] == 'TCP_CLIENT':
      self.read_tcpclient()
    elif self.config['feed_channel'] == 'UDP_SERVER':
      self.read_udpserver()
    elif self.config['feed_channel'] == 'UDP_CLIENT':
      self.read_udpclient()
    elif self.config['feed_channel'] == 'MQTT':
      self.read_mqtt()     
        
if __name__ == '__main__':   
  q_data = multiprocessing.Queue()  
  q_log  = multiprocessing.Queue()  
  dr     = DataReader(q_data,q_log)
  logger = Logger(q_log)
  logger.start()
  dr.start()
  
    