#!/usr/bin/env python

import os,sys,time
import random, math
import numpy as np
import py3toolbox as tb
import multiprocessing as mp
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
import pyqtgraph.opengl as gl
import pyqtgraph as pg

MODULE_NAME = 'MotionTracker'


def get_config():
  return tb.load_json('./config.json')



class MotionTracker(mp.Process):
  def __init__(self, q_in, q_mon):
    mp.Process.__init__(self)
    self.config     = get_config()[MODULE_NAME]
    self.q_in       = q_in
    self.q_mon      = q_mon

   
    self.trace = {}
    self.lines = np.array([ [0,0,0] ])
    

  def init_plot(self):
    self.win = pg.GraphicsWindow(size=(800,600), title="3D Motion Tracker")
    self.win.move(100, 800)
    self.win.addLayout(row=1, col=1) 
    self.w = gl.GLViewWidget()

    layoutgb = QtGui.QGridLayout()
    self.win.setLayout(layoutgb)

    layoutgb.addWidget(self.w,0,0)


    self.w.opts['distance'] = 20
    self.w.setWindowTitle('GL LinePlotItem')
    self.w.setGeometry(0, 110, 1000, 1000)
    self.w.show()

    # create the background grids
    gx = gl.GLGridItem()
    gx.rotate(90, 0, 1, 0)
    gx.translate(-10, 0, 0)
    self.w.addItem(gx)
    gy = gl.GLGridItem()
    gy.rotate(90, 1, 0, 0)
    gy.translate(0, -10, 0)
    self.w.addItem(gy)
    gz = gl.GLGridItem()
    gz.translate(0, 0, -10)
    self.w.addItem(gz)

    
    self.trace = gl.GLLinePlotItem(pos=self.lines, color=pg.glColor((1, 1)), width=5, antialias=True)
    self.w.addItem(self.trace)

    #timer = QtCore.QTimer()
    #timer.timeout.connect(self.update)
    #timer.start(0)

  def update(self):
    try :
      data = self.q_in.get(False)
      if data is not None :
        point = np.array([ [ data['gX'],data['gY'], data['gZ']    ]   ])
        self.lines = np.append(self.lines ,  point , axis=0)  
        self.trace.setData(pos=self.lines, color=pg.glColor((1, 1)), width=5, antialias=True)
    except Exception :
      pass
    

  def run(self):
    self.app = QApplication.instance()
    if self.app is None:
      self.app = QApplication([])  
    self.init_plot()
    
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    timer.start(0)

    self.q_mon.put(MODULE_NAME)
    QApplication.exec_()
    return


"""
#
# 3D Scattor Plot data
#
#
#
"""

class Scatter3DViewer(mp.Process):
  def __init__(self, q_in, q_mon):
    mp.Process.__init__(self)
    self.config     = get_config()[MODULE_NAME]
    self.q_in       = q_in
    self.q_mon      = q_mon


    self.trace = {}
    self.dots = np.array([ [0,0,0]])

  def init_plot(self):
    self.win = pg.GraphicsWindow(size=(800,600), title="Scatter 3D Viewer")
    self.win.move(100, 800)
    self.win.addLayout(row=1, col=1) 
    self.w = gl.GLViewWidget()

    layoutgb = QtGui.QGridLayout()
    self.win.setLayout(layoutgb)

    layoutgb.addWidget(self.w,0,0)


    self.w.opts['distance'] = 400
    self.w.setWindowTitle('GL LinePlotItem')
    self.w.setGeometry(0, 0, 2000, 2000)
    self.w.show()

    # create the background grids
    gx = gl.GLGridItem()
    gx.setSize(200,200,200)
    gx.setColor((0, 255, 0, 80.0))
    #gx.setSpacing(3,3,3)
    gx.rotate(90, 0, 1, 0)
    self.w.addItem(gx)


    gy = gl.GLGridItem()
    gy.setSize(200,200,200)
    gy.setColor((255, 0, 0, 80.0))
    #gy.setSpacing(3,3,3)
    gy.rotate(90, 1, 0, 0)
    self.w.addItem(gy)

    gz = gl.GLGridItem()
    gz.setSize(200,200,200)
    gz.setColor((255, 0, 255, 90.0))
    #gz.setSpacing(3,3,3)
    self.w.addItem(gz)

    
    self.trace = gl.GLScatterPlotItem(pos=self.dots)
    self.w.addItem(self.trace)



  def update(self):
    try :
      data = self.q_in.get(False)
      if data is not None:
        dot = np.array([ [ data['mX'],data['mY'], data['mZ']    ]  ])
        self.dots = np.append(self.dots, dot,   axis=0)  
        self.trace.setData(pos=self.dots, color=(255, 255,0,100), size=2)
    except Exception:
      pass  

  def run(self):
    self.app = QApplication.instance()
    if self.app is None:
      self.app = QApplication([])  
    self.init_plot()
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    timer.start(0)    
    self.q_mon.put(MODULE_NAME)
    QApplication.exec_()
    return




def Scatter3DViewer_demo(): 
  q_in          = mp.Queue()
  q_mon         = mp.Queue()

  p = Scatter3DViewer(q_in =q_in, q_mon=q_mon)
  p.start()
  data = {}
  A = 100
  B = 60
  C = 20
  for alpha in np.arange(0, math.pi,math.pi / 30 ):
    for beta in np.arange(0, math.pi * 2, math.pi / 30 ):
      data["mX"] = A * math.sin(alpha) * math.cos(beta)
      data["mY"] = B * math.sin(alpha) * math.sin(beta)
      data["mZ"] = C * math.cos(alpha)
      q_in.put(data)
      time.sleep(0.01)


 
if __name__ == '__main__':
  Scatter3DViewer_demo()
  print (math.sin(math.pi/4))

  """
  v = MotionTracker(q_in =q_in, q_mon=q_mon)
  v.start()
  dots = np.random.randint(-10,10,size=(1000,3))
  for dot in dots:
    q_in.put(dot)
    time.sleep(0.5)
  """     
  pass