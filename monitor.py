#!/usr/bin/env python

import sys
import os
import multiprocessing  as mp
import data_reader      as dr
import gyro_monitor     as gyro
import graph_monitor    as graph


if __name__ == '__main__':
  q_data = mp.Queue()
  data_reader    = dr.DataReader(q_data)
  gyro_monitor   = gyro.GyroMonitor(q_data)
  graph_monitor  = graph.GraphMonitor(q_data)

  gyro_monitor.start()
  graph_monitor.start()
  data_reader.start()  
  