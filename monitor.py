#!/usr/bin/env python
# This program implements multiple realtime data visualizations 
# It utilises the multiprocess module of python to support 
# multiple CPU core
# 
# - Realtime graph 
# - 3D Gyro viewer
# - 3D Motion tracker
#
# Also data processing can be applied to the raw data received from sensors
# - Kalman Filter
# - Complementary filter
# - ... etc

import sys
import os
import time
import multiprocessing  as mp
import py3toolbox       as tb

# import processors
import data_reader      as dr
import data_logger      as dl
import data_processor   as dp
import gyro_viewer      as gv
import graph_monitor    as gm
import motion_tracker   as mt


def run_monitor() :
  processes = ["DataReader", "DataLogger", "DataProcessor", "GraphMonitor" , "GyroViewer", "MotionTracker" ]

  try :
    q_mon          = mp.Queue()
    q_data_out     = [mp.Queue(), mp.Queue()]               # for DataLogger and DataProcessor
    q_proc_out     = [mp.Queue(), mp.Queue(), mp.Queue()]   # for GraphMonitor,GyroViewer,MotionTracker

    # Loading raw data from file,sensors via serial port, TCP, UDP ... etc
    data_reader    = dr.DataReader(q_out=q_data_out, q_mon=q_mon)
    
    
    # Computation and filters on raw data from DataReader
    data_processor = dp.DataProcessor(q_in=q_data_out[0],  q_out=q_proc_out, q_mon=q_mon)

    # Log raw data from DataReader and save to log for replay and analysis
    data_logger    = dl.DataLogger(q_in=q_data_out[1],  q_mon=q_mon)

    # Real time graph for processed data
    graph_monitor  = gm.GraphMonitor(q_in=q_proc_out[0], q_mon=q_mon)

    # 3D object viewer, specifically to show gyro's rotation in real time
    gyro_viewer    = gv.GyroViewer(q_in=q_proc_out[1], q_mon=q_mon)

    # #d motion tracker based on inertial frame of reference
    motion_tracker = mt.MotionTracker(q_in=q_proc_out[2], q_mon=q_mon)

    # make sure all other processes started first except DataReader
    pre_start_procs = [data_processor, data_logger, graph_monitor , gyro_viewer , motion_tracker]
    for p in pre_start_procs: p.start()

    # wait until all started except  DataReader   
    while True:
      data = q_mon.get()
      print (data)
      processes.remove(data)
      
      if len(processes) == 1 and processes[0] == "DataReader":
        break
      else:
        time.sleep(0.1)
    
    # then start up data reader the last
    pre_start_procs.append(data_reader)
    print ("All Processors are started, now starting DataReader ...")
    data_reader.start()
    
  except Exception as err:
    # send messages to stop each process gracefully.
    print (err)
    exit(1) 


if __name__ == '__main__':
  run_monitor()

  