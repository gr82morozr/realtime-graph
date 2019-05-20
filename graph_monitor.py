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
from pyqtgraph.Qt import QtGui, QtCore
from collections import deque , defaultdict

def get_config():
  config = {
    '_DATA_SOURCE_'   : ['SERIAL', 'FILE', 'NETWORK'],
    'DATA_SOURCE'     : 'FILE',

    'NETWORK_HOST'    : '192.168.1.142',
    'NETWORK_PORT'    : 80,

   
    'SERIAL_PORT'     : '/dev/ttyUSB3',
    'SERIAL_RATE'     : 500000,
    'SERIAL_TIMEOUT'  : 1,

    'LOG_SOURCE_DATA' : False,
    'DATA_FEED_WAIT'  : True,
    'DROP_FRAME'      : True,
    'REFRESH_RATE'    : 20,


    'DATA_FILE'       : './sample.data',
    'LOG_FILE'        : '/tmp/1.log',
    'FILE_TEST'       : True,

   
    'DEBUG_MODE'      : False,
    'ANTIALIAS'       : True,
    'PEN_WIDTH'       : 0,
    'WIN_SIZE_X'      : 1400,
    'WIN_SIZE_Y'      : 800,
    'WIN_TITLE'       : 'Realtime Data Visualizer',
    'CUSTOM_CONFIG'   : False,
    
    'layouts'          : {
      'win_layout'      : (5,3),
      'boards'          : { 
                            '1'   : { 'layout' : (1,1,1,1), 'max_entries' : 100 },
                            '2'   : { 'layout' : (1,2,1,1), 'max_entries' : 100 },
                            '3'   : { 'layout' : (1,3,1,1), 'max_entries' : 100 },       
                            
                            '4'   : { 'layout' : (2,1,1,1), 'max_entries' : 100 }, 
                            '5'   : { 'layout' : (2,2,1,1), 'max_entries' : 100 },
                            '6'   : { 'layout' : (2,3,1,1), 'max_entries' : 100 }, 
                            
                            '7'   : { 'layout' : (3,1,1,1), 'max_entries' : 100 }, 
                            '8'   : { 'layout' : (3,2,1,1), 'max_entries' : 100 },
                            '9'   : { 'layout' : (3,3,1,1), 'max_entries' : 100 }, 

                            '10'  : { 'layout' : (4,1,1,1), 'max_entries' : 100 }, 
                            '11'  : { 'layout' : (4,2,1,1), 'max_entries' : 100 },
                            '12'  : { 'layout' : (4,3,1,1), 'max_entries' : 100 }, 

                            '13'  : { 'layout' : (5,1,1,3), 'max_entries' : 400 }

                          }
    },

    'data_config'     : { 
                          'ax'      : { 'board_id'    : '1', 'color' : 'b'  },
                          'ay'      : { 'board_id'    : '2', 'color' : 'g'  },
                          'az'      : { 'board_id'    : '3', 'color' : 'r'  },

                          'gx'      : { 'board_id'    : '4', 'color' : 'c'  },
                          'gy'      : { 'board_id'    : '5', 'color' : 'm'  },
                          'gz'      : { 'board_id'    : '6', 'color' : 'y'  },
                          
                          'ax_raw'  : { 'board_id'    : '1', 'color' : (60,60,60)   },
                          'ay_raw'  : { 'board_id'    : '2', 'color' : (60,60,60)   },
                          'az_raw'  : { 'board_id'    : '3', 'color' : (60,60,60)   },

                          'gx_raw'  : { 'board_id'    : '4', 'color' : (60,60,60)   },
                          'gy_raw'  : { 'board_id'    : '5', 'color' : (60,60,60)   },
                          'gz_raw'  : { 'board_id'    : '6', 'color' : (60,60,60)   },
                          
                          'Pitch'   : { 'board_id'    : '7', 'color' : 'r'   },
                          'Yaw'     : { 'board_id'    : '8', 'color' : 'g'   },
                          'Roll'    : { 'board_id'    : '9', 'color' : 'b'   },

                          'err_P'   : { 'board_id'    :'10', 'color' : 'r'   },
                          'err_I'   : { 'board_id'    :'11', 'color' : 'g'   },
                          'err_D'   : { 'board_id'    :'12', 'color' : 'b'   },

                          'Error'     : { 'board_id'    :'13', 'color' : 'w'   },
                          'PID'       : { 'board_id'    :'13', 'color' : 'r'   },
                          'g_int'     : { 'board_id'    :'13', 'color' : 'g'   },
                          'g_pitch'   : { 'board_id'    :'13', 'color' : 'b'   }
                          
                        }
  }
  return config


class GraphMonitor(multiprocessing.Process):
  def __init__(self,in_q=None):
    multiprocessing.Process.__init__(self)
    self.config = get_config()
    self.in_q   = in_q
    self.trace_data = {}

    # data stuff
    self.fps = 0   
        
    # PyQtGRaph stuff
    self.app = QtGui.QApplication([])
    self.win = pg.GraphicsWindow(title="Basic plotting")
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
    self.win.setWindowTitle(self.config['WIN_TITLE'] + ' : ' + str(self.fps ) + ' FPS, Q = ' + str(self.in_q.qsize())  )
    #print (self.fps)

  # update data for charts  
  def update(self):
    # wait for data feed
    if self.config['DATA_FEED_WAIT'] == True:
      data = json.loads(self.in_q.get())
      #data = json.loads(self.in_q.recv())
      if self.config['DROP_FRAME'] == True and self.config['FILE_TEST'] == False and self.in_q.qsize() > int(self.fps / 8) :
        return
      for k in data.keys():
        if k not in self.config['data_config']: continue
        if k not in self.trace_data :
          self.init_trace_data(k)
        self.trace_data[k]['y_data'].append(float(data[k]))     
    else :
      # NOT wait for data feed
      try :
        data = json.loads(self.in_q.get(block=False, timeout=1))
        #data = json.loads(self.in_q.recv())
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

  # Data Reader
  data_q   = multiprocessing.JoinableQueue()
  #reader_pipe, visualizer_conn = Pipe()  
  
  data_reader = DataReader(out_q=data_q)
  data_reader.start()

  # Visulizer
  p = Visualizer(in_q = data_q)
  p.start()