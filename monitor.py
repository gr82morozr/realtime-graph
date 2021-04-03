#!/usr/bin/env python

import sys
import os
import multiprocessing  as mp
import data_reader      as dr
import data_processor   as dp
import gyro_monitor     as gyro
import graph_monitor    as graph


if __name__ == '__main__':
  try :
    q_log     = mp.Queue()
    q_dr_out  = mp.Queue()
    qs_dp_out = [mp.Queue(), mp.Queue(), mp.Queue()]
    
    data_reader    = dr.DataReader(q_log=q_log,       q_out=q_dr_out)
    data_processor = dp.DataProcessor(q_in=q_dr_out,  qs_out=qs_dp_out)
    
    
    graph_monitor  = graph.GraphMonitor(qs_dp_out[0])
    gyro_monitor   = gyro.GyroMonitor(qs_dp_out[1])
    

    graph_monitor.start()
    gyro_monitor.start()
    
    data_processor.start()
    
    data_reader.start()
  except KeyboardInterrupt:
    exit(1)         