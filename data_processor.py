#!/usr/bin/env python

# =====================================================================
#
# =====================================================================

 
import sys
import math, re, time
import multiprocessing as mp
import py3toolbox as tb


MODULE_NAME = 'DataProcessor'


def get_config():
  config = tb.load_json('./config.json')
  return config



# =================================================
#
#  Data Processor 
#  - Process signals and apply filters 
#
# =================================================
class DataProcessor(mp.Process):
  def __init__(self, q_in,  q_out, q_mon):
    mp.Process.__init__(self)
    self.config           = get_config()[MODULE_NAME]

    self.q_in             = q_in  
    self.q_out            = q_out
    self.q_mon            = q_mon

    
    self.processed_data   = {}


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
          print (self.q_in.qsize(),self.q_out[0].qsize() )
        self.processed_data = data
        self.output()
      except Exception:
        pass

  def apply_no_filter_for_quat(self):
    t = time.time()
    pX = 0
    pY = 0
    pZ = 0
    while True:
      try : 
        data = self.q_in.get()
        #pX += data["aX"] * (time.time() - t)
        #pY += data["aY"] * (time.time() - t)
        #pZ += data["aZ"] * (time.time() - t)
        #t = time.time()
        #data["pX"] = pX
        #data["pY"] = pY
        #data["pZ"] = pZ
        
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
          print (self.q_in.qsize(),self.q_out[0].qsize() )
        self.processed_data = data
        self.output()
      except Exception:
        pass


  def output(self) :
    if type(self.q_out) is list:
      for q in self.q_out:
        q.put(self.processed_data)
    else:
      self.q_out.put(self.processed_data)


    
  def run(self):
    self.q_mon.put(MODULE_NAME)
    try : 
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
    
    except Exception as err:
      exit (1)

        
        
        
if __name__ == '__main__':   
  pass
  
    