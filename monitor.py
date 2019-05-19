#!/usr/bin/env python

import sys
import os
import multiprocessing as mp
import data_reader as dr
import gyro_monitor as gyro
import graph_monitor as graph


if __name__ == '__main__':
  q_data = mp.Queue()
  gm = gyro.GyroMonitor(q_data)
  dr = dr.DataReader(q_data)
  gm.start()
  dr.start()  
  