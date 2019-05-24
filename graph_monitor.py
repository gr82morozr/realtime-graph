#!/apps/anaconda3/bin/python3

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import sys
import re
import time
import json
import multiprocessing
import collections
import serial
import socket

import py3toolbox as tb
import pyqtgraph as pg
from random import randint
from multiprocessing import Process, Pipe
from PyQt5 import QtGui, QtCore
from collections import deque , defaultdict

module_name = 'GraphMonitor'

def get_config():
  return tb.load_json('./config.json')[module_name]


class GraphMonitor(multiprocessing.Process):
  def __init__(self,in_q=None):
    multiprocessing.Process.__init__(self)
    self.config     = get_config()
    self.in_q       = in_q
    self.trace_data = {}

    self.fps = 0   

    # for FPS calculation
    self.last  = time.time()

  def init_plots(self):
    self.app = QtGui.QApplication([])
    self.win = pg.GraphicsWindow(title="Basic plotting")
    self.win.addLayout(row=self.config['layouts']['win_layout'][0], col=self.config['layouts']['win_layout'][1]) 
    self.win.resize(self.config['layouts']['win_size'][0],self.config['layouts']['win_size'][1])

    self.win.setWindowTitle(self.config['win_title'])
    pg.setConfigOptions(antialias=True)    
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
    self.trace_data[key]['plot']    = self.boards[self.config['data_config'][key]['board_id']].plot(pen=pg.mkPen(self.trace_data[key]['color'], width=2), name=key)
    
  
  # update FPS  
  def update_fps(self):
    self.fps = int(1.0/(time.time() - self.last + 0.00001 ))
    self.last = time.time()
    self.win.setWindowTitle(self.config['win_title'] + ' : ' + str(self.fps ) + ' FPS, Q = ' + str(self.in_q.qsize())  )

  # update data for charts  
  def update(self):
    
    # wait for data feed
    if self.config['data_feed_wait'] == True:
      #rawdata = self.in_q.get()
      #print (rawdata)
      data = self.in_q.get()
      #data = json.loads(self.in_q.recv())
      #if self.config['DROP_FRAME'] == True and self.config['FILE_TEST'] == False and self.in_q.qsize() > int(self.fps / 8) :
      #  return
      for k in data.keys():
        if k not in self.config['data_config']: continue
        if k not in self.trace_data :
          self.init_trace_data(k)
        self.trace_data[k]['y_data'].append(float(data[k]))
    else :
      # NOT wait for data feed
      try :
        data = self.in_q.get(block=False, timeout=1)
        for k in data.keys():
          if k not in self.config['data_config']: continue
          if k not in self.trace_data:
            self.init_trace_data(k)
          self.trace_data[k]['y_data'].append(float(data[k]))        
      except Exception:
        for k in self.trace_data.keys():
          self.trace_data[k]['y_data'].append( self.trace_data[k]['y_data'][-1] )  
      
    for k in self.trace_data.keys():
      self.trace_data[k]['plot'].setData(self.trace_data[k]['x_data'] ,self.trace_data[k]['y_data'])
     
    self.update_fps()

  def run(self):
    self.init_plots()
    # kick off the animation
 
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)

    if self.config['data_feed_wait'] == True:
      timer.start(0)
    else:
      timer.start(self.config['refresh_rate'])

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
      QtGui.QApplication.instance().exec_() 
 



if __name__ == '__main__':
  g    = GraphMonitor()
  g.start()

  pass