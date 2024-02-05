#!/apps/anaconda3/bin/python3

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import sys
import re
import time
import json
import math
import py3toolbox as tb
import multiprocessing as mp
from random import randint
import data_reader as dr

import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QOpenGLWidget, QMainWindow
from collections import deque , defaultdict

MODULE_NAME = 'GraphMonitor'


def get_config():
  return tb.load_json('./config.json')


class GraphMonitor(mp.Process):
  def __init__(self, q_in, q_mon):
    mp.Process.__init__(self)
    self.config     = get_config()[MODULE_NAME]
    self.q_in       = q_in
    self.q_mon      = q_mon

    self.trace_data = {}
    self.fps = 0   

    # for FPS calculation
    self.last  = time.time()

  def init_plot(self):
    #self.win = pg.GraphicsWindow(size=(self.config['layouts']['win_size'][0],self.config['layouts']['win_size'][1]), title="Basic plotting")
    self.win = pg.GraphicsLayoutWidget(size=(self.config['layouts']['win_size'][0],self.config['layouts']['win_size'][1]), title="Basic plotting", show=True)
    self.win.move(0, 0)
    self.win.addLayout(row=self.config['layouts']['win_layout'][0], col=self.config['layouts']['win_layout'][1]) 
    #self.win.resize(self.config['layouts']['win_size'][0],self.config['layouts']['win_size'][1])

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
      data = self.q_in.get(False)
      if data is not None:
        for k in data.keys():
          if k not in self.config['data_config']: continue
          if k not in self.trace_data :  self.init_trace_data(k) 
          self.trace_data[k]['y_data'].append(float(data[k]))
          self.trace_data[k]['plot'].setData(self.trace_data[k]['x_data'] ,self.trace_data[k]['y_data'])
        self.update_fps()  
    except Exception:
      pass      

    

  def run(self):
    self.app   =   QApplication.instance()
    if self.app is None:
      self.app = QApplication([])  
    self.init_plot()
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    timer.start(0)
    self.q_mon.put(MODULE_NAME)
    QApplication.exec_()
    return

    
def GraphMonitor_demo() :
  q_in          = mp.Queue()
  q_mon         = mp.Queue()
  config        = get_config()[MODULE_NAME]
  p = GraphMonitor(q_in =q_in, q_mon=q_mon)  

  p.start()
  data = {}
  for x in np.arange(0,10000, math.pi/90):
    data[list(config['data_config'].keys())[0]] = math.sin(x)
    data[list(config['data_config'].keys())[1]] = math.cos(x)
    data[list(config['data_config'].keys())[2]] = math.cos(x) + math.sin(x)
    q_in.put(data)
    time.sleep(0.02)






  pass


if __name__ == '__main__':
  GraphMonitor_demo()
  