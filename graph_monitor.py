#!/apps/anaconda3/bin/python3

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import sys
import re
import time
import json
import multiprocessing as mp
import collections
import serial
import socket



from random import randint
from multiprocessing import Process, Pipe
import py3toolbox as tb
import data_reader as dr

import pyqtgraph as pg
from PyQt5 import QtGui, QtCore


from collections import deque , defaultdict

module_name = 'GraphMonitor'

def get_config():
  return tb.load_json('./config.json')[module_name]


class GraphMonitor(mp.Process):
  def __init__(self,q_in=None):
    mp.Process.__init__(self)
    self.config     = get_config()
    self.q_in       = q_in
    self.trace_data = {}

    self.fps = 0   

    # for FPS calculation
    self.last  = time.time()

  def init_plots(self):
    #self.app = QtGui.QApplication([])
    self.app = pg.mkQApp("RealtimeGraph")
    self.win = pg.GraphicsWindow(title="Basic plotting")
    self.win.addLayout(row=self.config['layouts']['win_layout'][0], col=self.config['layouts']['win_layout'][1]) 
    self.win.resize(self.config['layouts']['win_size'][0],self.config['layouts']['win_size'][1])

    self.win.setWindowTitle(self.config['win_title'])
    pg.setConfigOptions(useOpenGL=True)
    #pg.setConfigOptions(antialias=True)    
    self.boards = {}
    for b in self.config['layouts']['boards'].keys():
      cfg = self.config['layouts']['boards'][b]['layout']
      t_row     = cfg[0]
      t_col     = cfg[1]
      t_rowspan = cfg[2]
      t_colspan = cfg[3]      
      title     = None
      for d in self.config['data_config'].keys():
        if self.config['data_config'][d]['board_id'] == b :
          if title is None : title=d 
          else: title += ',' + d
      self.boards[b] =  self.win.addPlot(row=t_row, col=t_col, rowspan=t_rowspan, colspan=t_colspan, title=title) 
      
  def init_trace_data (self, key):
    max_entries =  self.config['layouts']['boards'][self.config['data_config'][key]['board_id']]['max_entries']

    self.trace_data[key] = {}
    self.trace_data[key]['color']   = self.config['data_config'][key]['color']
    self.trace_data[key]['x_data']  = np.arange(0,max_entries,1)
    self.trace_data[key]['y_data']  = deque ([0] * max_entries, maxlen = max_entries)
    self.trace_data[key]['plot']    = self.boards[self.config['data_config'][key]['board_id']].plot(pen=pg.mkPen(self.trace_data[key]['color'], width=1), name=key)
    
  
  # update FPS  
  def update_fps(self):
    self.fps = int(1.0/(time.time() - self.last + 0.00001 ))
    self.last = time.time()
    self.win.setWindowTitle(self.config['win_title'] + ' : ' + str(self.fps ) + ' FPS, Q = ' + str(self.q_in.qsize())  )

  # update data for charts  
  def update(self):
    try :
      data = self.q_in.get()
      for k in data.keys():
        if k not in self.config['data_config']: continue
        if k not in self.trace_data :  self.init_trace_data(k) 
        self.trace_data[k]['y_data'].append(float(data[k]))
        self.trace_data[k]['plot'].setData(self.trace_data[k]['x_data'] ,self.trace_data[k]['y_data'])

    except KeyboardInterrupt:
      exit(1)       
    """
    # wait for data feed
    if self.config['data_feed_wait'] == True:
      #rawdata = self.q_in.get()
      #print (rawdata)
      data = self.q_in.get()
      #data = json.loads(self.q_in.recv())
      #if self.config['DROP_FRAME'] == True and self.config['FILE_TEST'] == False and self.q_in.qsize() > int(self.fps / 8) :
      #  return
      for k in data.keys():
        if k not in self.config['data_config']: continue
        if k not in self.trace_data :
          self.init_trace_data(k) 
        self.trace_data[k]['y_data'].append(float(data[k]))
    else :
      # NOT wait for data feed
      try :
        data = self.q_in.get(block=False, timeout=1)
        for k in data.keys():
          if k not in self.config['data_config']: continue
          if k not in self.trace_data:
            self.init_trace_data(k)
          #self.trace_data[k]['y_data'].append(float(data[k]))        
          self.trace_data[k]['y_data'].append(data[k])

      except Exception:
        for k in self.trace_data.keys():
          self.trace_data[k]['y_data'].append( self.trace_data[k]['y_data'][-1] )  
      
    for k in self.trace_data.keys():
      self.trace_data[k]['plot'].setData(self.trace_data[k]['x_data'] ,self.trace_data[k]['y_data'])
    """
    self.update_fps()

  def run(self):
    self.init_plots()
    # kick off the animation
 
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    timer.start(0)
    
    """
    if self.config['data_feed_wait'] == True:
      timer.start(0)
    else:
      timer.start(self.config['refresh_rate'])
    """

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
      pg.mkQApp().exec_()
    



if __name__ == '__main__':
  data_queues     = [mp.Queue(), mp.Queue()]
  data_reader     = dr.DataReader(data_queues)
  graph_monitor   = GraphMonitor(data_queues[1])

  graph_monitor.start()
  data_reader.start()  
  