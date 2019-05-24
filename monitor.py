#!/usr/bin/env python

import sys
import os
import multiprocessing  as mp
import data_reader      as dr
import gyro_monitor     as gyro
import graph_monitor    as graph


if __name__ == '__main__':
  data_queues = [mp.Queue(), mp.Queue()]
  data_reader    = dr.DataReader(data_queues)
  gyro_monitor   = gyro.GyroMonitor(data_queues[0])
  graph_monitor  = graph.GraphMonitor(data_queues[1])

  gyro_monitor.start()
  graph_monitor.start()
  data_reader.start()  
  