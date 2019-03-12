#!/apps/anaconda3/bin/python3

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import sys
import re
import time
import json
import multiprocessing as mp
import data_reader as dr


import py3toolbox as tb
import pyqtgraph as pg
from random import randint
from pyqtgraph.Qt import QtGui, QtCore
from collections import deque , defaultdict

def get_config():
  return tb.load_json('./config.json')

class GraphMonitor(mp.Process):
  def __init__(self,q_data=None):
    mp.Process.__init__(self)
    self.config = get_config()['GraphMonitor']
    self.q_data   = q_data
    self.trace_data = {}

    # data stuff
    self.fps = 0   
        
    # PyQtGRaph stuff
    self.app = QtGui.QApplication([])
    self.win = pg.GraphicsWindow(title="Graph Monitor")
    self.win.addLayout(row=self.config['layouts']['win_layout'][0], col=self.config['layouts']['win_layout'][1]) 
    self.win.resize(self.config['WIN_SIZE_X'],self.config['WIN_SIZE_Y'])
    self.win.setWindowTitle(self.config['WIN_TITLE'])
    pg.setConfigOptions(antialias=self.config['ANTIALIAS'])
    self.init_plots()

    # for FPS calculation
    self.last  = time.time()

  def init_plots(self):
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
    self.trace_data[key]['plot']    = self.boards[self.config['data_config'][key]['board_id']].plot(pen=pg.mkPen(self.trace_data[key]['color'], width=self.config['PEN_WIDTH']), name=key)
    
  
  # update FPS  
  def update_fps(self):
    self.fps = int(1.0/(time.time() - self.last + 0.00001 ))
    self.last = time.time()
    self.win.setWindowTitle(self.config['WIN_TITLE'] + ' : ' + str(self.fps ) + ' FPS, Q = ' + str(self.q_data.qsize())  )
    #print (self.fps)

  # update data for charts  
  def update(self):
    # wait for data feed
    if self.config['DATA_FEED_WAIT'] == True:
      data = json.loads(self.q_data.get())
      #data = json.loads(self.q_data.recv())
      if self.config['DROP_FRAME'] == True and self.config['FILE_TEST'] == False and self.q_data.qsize() > int(self.fps / 8) :
        return
      for k in data.keys():
        if k not in self.config['data_config']: continue
        if k not in self.trace_data :
          self.init_trace_data(k)
        self.trace_data[k]['y_data'].append(float(data[k]))     
    else :
      # NOT wait for data feed
      try :
        data = json.loads(self.q_data.get(block=False, timeout=1))
        #data = json.loads(self.q_data.recv())
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

  def start(self):
    # kick off the animation
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    if self.config['DATA_FEED_WAIT'] == True:
      timer.start(0)
    else:
      timer.start(self.config['REFRESH_RATE'])
  
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
      QtGui.QApplication.instance().exec_() 
      
## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
  q_data = mp.Queue()  
  gm = GraphMonitor(q_data)
  dr = dr.DataReader(q_data)
  gm.start()
  dr.start()  
