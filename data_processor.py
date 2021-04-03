#!/usr/bin/env python

# =====================================================================
#
# =====================================================================

 
import sys
import math, re, time
import multiprocessing
import py3toolbox as tb

def get_config():
  config = tb.load_json('./config.json')
  return config



# =================================================
#
#  Data Processor 
#  - Process signals and apply filters 
#
# =================================================
class DataProcessor(multiprocessing.Process):
  def __init__(self, q_in, qs_out):
    multiprocessing.Process.__init__(self)
    self.q_in             = q_in
    self.qs_out           = qs_out
    self.config           = get_config()['DataProcessor']
    self.processed_data   = ""


  def apply_no_filter_for_raw(self):
    Yaw = 0
    t = time.time()
    while True:
      try : 
        data = self.q_in.get()
        if bool(data) == True:
          data['Roll']  = - math.atan2(-data['aX'], data['aZ']) / math.pi  * 180
          data['Pitch'] = - math.atan2(data['aY'], data['aZ'])  / math.pi  * 180
          Yaw +=data['gZ'] * (time.time() - t)
          data['Yaw'] = Yaw
          t = time.time()
          data['Type'] = 'YPR'
          print (self.q_in.qsize(),self.qs_out[0].qsize() )
        self.processed_data = data
        self.output()
      except Exception:
        pass

  def apply_no_filter_for_quat(self):
    Yaw = 0
    t = time.time()
    while True:
      try : 
        data = self.q_in.get()
        data['Type'] = 'QUATERNION'
        #data['Type'] = 'YPR'
        self.processed_data = data
        self.output()
      except Exception:
        pass

  def apply_complementary(self):
    Yaw = 0
    t = time.time()
    while True:
      try : 
        data = self.q_in.get()
        if bool(data) == True:
          data['Roll']  = - math.atan2(-data['aX'], data['aZ']) / math.pi  * 180
          data['Pitch'] = - math.atan2(data['aY'], data['aZ'])  / math.pi  * 180
          Yaw +=data['gZ'] * (time.time() - t)
          data['Yaw'] = Yaw
          t = time.time()
          data['Type'] = 'YPR'
          print (self.q_in.qsize(),self.qs_out[0].qsize() )
        self.processed_data = data
        self.output()
      except Exception:
        pass

  def output(self) :
    for q in self.qs_out:   q.put(self.processed_data)
    
  def run(self):
    if self.config['filter']   == 'COMPLEMENTARY':
      self.apply_complementary()
    elif self.config['filter'] == 'KALMAN':
      self.apply_kalman()
    elif self.config['filter'] == 'FOURIER':
      self.apply_fourier()      
    elif self.config['filter'] == 'LAPLACE':
      self.apply_laplace()
    elif self.config['filter'] == 'NOFLTR_FOR_RAW':
      self.apply_no_filter_for_raw()
    elif self.config['filter'] == 'NOFLTR_FOR_QUAT':
      self.apply_no_filter_for_quat()


        
        
        
if __name__ == '__main__':   
  pass
  
    