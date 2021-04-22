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
import math_helper as mh



MODULE_NAME = 'MotionTracker'


def get_config():
  return tb.load_json('./config.json')


"""
#
# Motion Tracker
# - 3D motion tacking
#
#
"""

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
    gz.setColor((0, 0, 255, 160.0))
    #gz.setSpacing(3,3,3)
    self.w.addItem(gz)

    
    self.trace = gl.GLLinePlotItem(pos=self.lines, color=pg.glColor((1, 1)), width=5, antialias=True)
    self.w.addItem(self.trace)


  def update(self):
    try :
      data = self.q_in.get(False)
      if data is not None :
        point = np.array([ [ data['pX'],data['pY'], data['pZ'] ]   ])
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
# - Can be used to check 3D space distributions
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
    gz.setColor((0, 0, 255, 160.0))
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



"""
# ================================================
#
#  Vector 3D viewer 
# - can be used to check object orentations
#
# ================================================
"""

class Vector3Dviewer(mp.Process):
  def __init__(self, q_in, q_mon):
    mp.Process.__init__(self)
    self.config     = get_config()[MODULE_NAME]
    self.q_in       = q_in
    self.q_mon      = q_mon

   
    self.trace_x = {}
    self.trace_y = {}
    self.trace_z = {}
    self.line_x = np.array([ [0,0,0] ])
    self.line_y = np.array([ [0,0,0] ])
    self.line_z = np.array([ [0,0,0] ])
    

  def init_plot(self):
    self.win = pg.GraphicsWindow(size=(800,600), title="3D Motion Tracker")
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
    gx.rotate(90, 0, 1, 0)
    self.w.addItem(gx)

    gy = gl.GLGridItem()
    gy.setSize(200,200,200)
    gy.setColor((255, 0, 0, 80.0))
    gy.rotate(90, 1, 0, 0)
    self.w.addItem(gy)

    gz = gl.GLGridItem()
    gz.setSize(200,200,200)
    gz.setColor((0, 0, 255, 160.0))
    self.w.addItem(gz)

    self.line_x = np.array([ [0,0,0], [40, 0,  0] ])
    self.line_y = np.array([ [0,0,0], [0,  40, 0] ])
    self.line_z = np.array([ [0,0,0], [0,  0, 40] ])
    
    self.trace_x = gl.GLLinePlotItem(pos=self.line_x, color=pg.glColor((255, 0, 0, 160.0)), width=10, antialias=True)
    self.w.addItem(self.trace_x)
    self.trace_y = gl.GLLinePlotItem(pos=self.line_y, color=pg.glColor((0, 255, 0, 160.0)), width=10, antialias=True)
    self.w.addItem(self.trace_y)
    self.trace_z = gl.GLLinePlotItem(pos=self.line_z, color=pg.glColor((0, 0, 255, 160.0)), width=10, antialias=True)
    self.w.addItem(self.trace_z)


  def update(self):
    try :
      data = self.q_in.get(False)
      if data is not None :
        rot_quat = [data["qX"],data["qY"],data["qZ"],data["qW"]]
        
        point_x = np.array([mh.rotate_vector(rot_quat, [1,0,0])]) * 40
        point_y = np.array([mh.rotate_vector(rot_quat, [0,1,0])]) * 40
        point_z = np.array([mh.rotate_vector(rot_quat, [0,0,1])]) * 40

        self.line_x = np.array([ [0,0,0] ])
        self.line_y = np.array([ [0,0,0] ])
        self.line_z = np.array([ [0,0,0] ])
        
        self.line_x = np.append(self.line_x ,  point_x , axis=0)  
        self.line_y = np.append(self.line_y ,  point_y , axis=0)  
        self.line_z = np.append(self.line_z ,  point_z , axis=0)  


        self.trace_x.setData(pos=self.line_x, color=((255, 0, 0, 160.0)), width=10, antialias=True)
        self.trace_y.setData(pos=self.line_y, color=((0, 255, 0, 160.0)), width=10, antialias=True)
        self.trace_z.setData(pos=self.line_z, color=((0, 0, 255, 160.0)), width=10, antialias=True)

    except Exception as err:
      #print (str(err))
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
# ================================================
#
#  Below are demo functions
#
# ================================================
"""
def MotionTracker_demo():
  q_in          = mp.Queue()
  q_mon         = mp.Queue()
  data          = {}
  p = MotionTracker(q_in =q_in, q_mon=q_mon)
  p.start()

  for alpha in np.arange(- math.pi * 6, math.pi * 6 , math.pi / 60 ):
    data["pX"] = math.sin(alpha) * 30
    data["pY"] = math.cos(alpha) * 60
    data["pZ"] = alpha * 5
    q_in.put(data)
    time.sleep(0.01)

def Vector3Dviewer_demo():
  q_in          = mp.Queue()
  q_mon         = mp.Queue()
  data          = {}
  p = Vector3Dviewer(q_in =q_in, q_mon=q_mon)
  p.start()

  for v in np.arange(-1, 1 , 0.001 ):
    data["qX"] = v
    data["qY"] = 1
    data["qZ"] = 1
    data["qW"] = 1
    
    q_in.put(data)
    time.sleep(0.05)


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
  #MotionTracker_demo()
  Vector3Dviewer_demo() 
  #Scatter3DViewer_demo()
  

  """
  v = MotionTracker(q_in =q_in, q_mon=q_mon)
  v.start()
  dots = np.random.randint(-10,10,size=(1000,3))
  for dot in dots:
    q_in.put(dot)
    time.sleep(0.5)
  """     
  pass
