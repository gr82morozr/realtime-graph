#!/usr/bin/env python

import sys
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
    self.win = pg.GraphicsWindow(size=(800,600), title="Motion Tracker")
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

    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    timer.start(0)


    """
    self.n = 10
    self.m = 100
    self.y = np.linspace(-10, 10, self.n)
    self.x = np.linspace(-10, 10, self.m)
    self.phase = 0

    for i in range(self.n):
      yi = np.array([self.y[i]] * self.m)
      d = np.sqrt(self.x ** 2 + yi ** 2)
      z = 10 * np.cos(d + self.phase) / (d + 1)
      pts = np.vstack([self.x, yi, z]).transpose()
      
    """

  def update(self):
    data = self.q_in.get()
    point = np.array([ [ data['pX'],data['pY'], data['pZ']    ]   ])
    self.lines = np.append(self.lines ,  point , axis=0)  
    self.trace.setData(pos=self.lines, color=pg.glColor((1, 1)), width=5, antialias=True)
    

  def run(self):
    self.app = QApplication.instance()
    if self.app is None:
      self.app = QApplication([])  
    self.init_plot()
    self.q_mon.put(MODULE_NAME)
    QApplication.exec_()
    return


# Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
  v = MotionTracker()
  v.start()