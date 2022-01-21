#!/usr/bin/env python

# =====================================================================
#
# =====================================================================

import os, sys, time
import math, re, time
import multiprocessing as mp
import py3toolbox as tb


import math_helper as mh

import low_pass_filters as lpf

from scipy.spatial.transform import Rotation 


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

  def apply_test_filter(self):
    ravg_fltr = lpf.RunningAvarageFilter(10)
    exp_fltr  = lpf.ExponentialFilter(0.2)


    """
    mX_min = None
    mX_max = None
    mY_min = None
    mY_max = None
    mZ_min = None
    mZ_max = None
    """
    pX = 0
    pY = 0
    pZ = 0
    t = time.time()
    

    while True:
      try : 
        data = self.q_in.get()
        data['Type'] = 'QUATERNION'
        data['avg.aX'], data['avg.aY'], data['avg.aZ'] = ravg_fltr.compute([data['aX'], data['aY'], data['aZ']])
        data['exp.aX'], data['exp.aY'], data['exp.aZ'] = exp_fltr.compute([data['aX'], data['aY'], data['aZ']])
        quat = [] 
        
        rot_aX , rot_aY, rot_aZ = mh.rotate_vector ( [  data['qX'],  data['qY'], data["qZ"], data['qW']   ], [data['exp.aX'], data['exp.aY'], data['exp.aZ']] )


        pX += rot_aX * (time.time() - t) * (time.time() - t)
        pY += rot_aY * (time.time() - t) * (time.time() - t)
        pZ += rot_aZ * (time.time() - t) * (time.time() - t)


        t = time.time()
        data["pX"] = pX
        data["pY"] = pY
        data["pZ"] = pZ

        





        """
        if mX_min is None : mX_min = data["mX"]
        if mX_max is None : mX_max = data["mX"]

        if mY_min is None : mY_min = data["mY"]
        if mY_max is None : mY_max = data["mY"]

        if mZ_min is None : mZ_min = data["mZ"]
        if mZ_max is None : mZ_max = data["mZ"]

        if data["mX"] < mX_min : mX_min = data["mX"]
        if data["mX"] > mX_max : mX_max = data["mX"]

        if data["mY"] < mY_min : mY_min = data["mY"]
        if data["mY"] > mY_max : mY_max = data["mY"]

        if data["mZ"] < mZ_min : mZ_min = data["mZ"]
        if data["mZ"] > mZ_max : mZ_max = data["mZ"]
        """

        data['Roll'], data['Pitch'],  data['Yaw'] = mh.get_euler( [  data['qX'],  data['qY'], data["qZ"], data['qW']   ] , degrees = True  )

        self.processed_data = data
        self.output_data()
      except  Exception as e:
        print (str(e))
        pass

 

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
          data['Type'] = 'EULR'
          print (self.q_in.qsize(),self.q_out[0].qsize() )
        self.processed_data = data
        self.output_data()
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
        self.output_data()
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
        self.output_data()
      except Exception:
        pass



  def output_data (self):
    if bool(self.processed_data) :
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
      elif self.config['filter'] == 'TEST':
        #self.apply_test_filter()
        self.apply_no_filter_for_quat()
    
    except Exception as err:
      exit (1)

        
        
        
if __name__ == '__main__':   
  pass
  
    