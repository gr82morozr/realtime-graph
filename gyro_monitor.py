#!/usr/bin/env python

import sys
import math, random, re, time
import OpenGL.GL as gl
import py3toolbox as tb
import multiprocessing as mp
import data_reader as dr
import PyQt5 as pg



from PyQt5.QtCore import (QPoint, QPointF, QRect, QRectF, QSize, Qt, QTime, QTimer)
from PyQt5.QtGui import (QBrush, QColor, QFontMetrics, QImage, QPainter,  QSurfaceFormat)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtCore

# Rotation Setting 


def get_config():
  return tb.load_json('./config.json')



class Gyro3D(QOpenGLWidget):
  def __init__(self,  q_in=None):
    super(Gyro3D, self).__init__()
    self.config = get_config()['GyroMonitor']
    self.q_in   = q_in
    self.object = 0
    
    self.type   = ""

    self.rX   = 0
    self.rY   = 0
    self.rZ   = 0

    self.qW     = 0
    self.qX     = 0
    self.qY     = 0
    self.qZ     = 0
  
    self.rX     = 0
    self.rY     = 0
    self.rZ     = 0


    self.Yaw    = 0
    self.Pitch  = 0
    self.Roll   = 0


    self.trolltechGreen  = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
    self.trolltechPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

    self.animationTimer = QTimer()
    self.animationTimer.setSingleShot(False)
    self.animationTimer.timeout.connect(self.update)
    self.animationTimer.start(10)

    self.readDataTimer = QTimer()
    self.readDataTimer.setSingleShot(False)
    self.readDataTimer.timeout.connect(self.readData)
    self.readDataTimer.start(15)

    self.setAutoFillBackground(True)
    self.setMinimumSize(200, 200)
    self.setWindowTitle("Gyro 3D Real-time Monitor")
    self.time = time.time()


  def readData(self):
    if self.q_in.qsize()>0 :
      try:
        data = self.q_in.get()
        print ("read ", data)
        #self.setXRotation(data['yaw'])
        #self.setYRotation(data['roll'])
        #self.setZRotation(data['pitch'])


        self.type = data['Type']

        if  self.type == 'QUATERNION' :
          self.qW     = data['qW'] * 180 / 3.1415926
          self.qX     = data['qX']
          self.qY     = data['qY']
          self.qZ     = data['qZ']

        elif self.type == 'EULER' :
          self.rX     = data['rX']
          self.rY     = data['rY']
          self.rZ     = data['rZ']

        elif self.type == 'YPR' :
          self.Yaw    = data['Yaw']
          self.Pitch  = data['Pitch']
          self.Roll   = data['Roll']


      except:
        pass
    
    
    
  def setXRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.rX:
      self.rX = angle

  def setYRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.rY:
      self.rY = angle

  def setZRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.rZ:
      self.rZ = angle

  def initializeGL(self):
    self.object = self.makeObject()

  def mousePressEvent(self, event):
    self.lastPos = event.pos() 

  def mouseMoveEvent(self, event):
    dx = event.x() - self.lastPos.x()
    dy = event.y() - self.lastPos.y()

    if event.buttons() & Qt.LeftButton:
      self.setXRotation(self.rX + 8 * dy)
      self.setYRotation(self.rY + 8 * dx)
    elif event.buttons() & Qt.RightButton:
      self.setXRotation(self.rX + 8 * dy)
      self.setZRotation(self.rZ + 8 * dx)

    self.lastPos = event.pos()

  def paintEvent(self, event):
    fps = int(1 / (time.time() - self.time))
    self.setWindowTitle("Gyro 3D Real-time Monitor : FPS = " + str(fps) + "\t Queue = " + str(self.q_in.qsize()) )

    self.time = time.time()
    self.makeCurrent()
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    self.setClearColor(self.trolltechPurple.darker())
    gl.glShadeModel(gl.GL_SMOOTH)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_LIGHT0)
    gl.glEnable(gl.GL_MULTISAMPLE)
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (0.5, -5.0, 7.0, 1.0)) 
    self.setupViewport(self.width(), self.height())
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    gl.glTranslatef(0.0, 0.0, -10.0)
    
    gl.glScalef(1.2, 1.2, 1.2)


    if  self.type == 'QUATERNION' :
      gl.glRotatef(self.qW        , self.qY, self.qZ, self.qX)
    elif self.type == 'EULER' :
      gl.glRotatef(self.rX        , 1.0, 0.0, 0.0)
      gl.glRotatef(self.rY        , 0.0, 1.0, 0.0)
      gl.glRotatef(self.rZ        , 0.0, 0.0, 1.0)
    elif self.type == 'YPR' :
      gl.glRotatef(self.Roll      , 1.0, 0.0, 0.0)
      gl.glRotatef(self.Yaw       , 0.0, 1.0, 0.0)
      gl.glRotatef(self.Pitch     , 0.0, 0.0, 1.0)

    
    

    gl.glCallList(self.object)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()

  

  def resizeGL(self, width, height):
    self.setupViewport(width, height)

  def showEvent(self, event):
    pass
    
  def sizeHint(self):
    return QSize(800, 600)


  def makeObject(self):
    genList = gl.glGenLists(1)
    gl.glNewList(genList, gl.GL_COMPILE)
    vertices = []
    vnormals = []

    gl.glBegin(gl.GL_TRIANGLES)   
    obj_lines = tb.read_file(file_name=self.config['object_file'],return_type='list')
    for obj_line in obj_lines:
      if obj_line.startswith('v ') : 
        obj_line = obj_line.replace('v ','')
        [x,y,z] = obj_line.split(" ")
        vertices.append ([float(x), float(y),float(z)])
     
      if obj_line.startswith('vn ') : 
        obj_line = obj_line.replace('vn ','')
        [vn_x,vn_y,vn_z] = obj_line.split(" ")
        vnormals.append ([float(vn_x), float(vn_y),float(vn_z)])       

    for obj_line in obj_lines:
      if obj_line.startswith('f ') : 
        obj_line = obj_line.replace('f ','')
        v = re.findall(r"\s*(\d+)\/\/\d+\s*", obj_line)
        vn = re.findall(r"\s*\d+\/\/(\d+)\s*", obj_line)
        gl.glNormal3d(vnormals[int(vn[0])-1][0],vnormals[int(vn[0])-1][1],vnormals[int(vn[0])-1][2])
        gl.glVertex3f(vertices[int(v[0])-1][0],vertices[int(v[0])-1][1],vertices[int(v[0])-1][2])
        gl.glVertex3f(vertices[int(v[1])-1][0],vertices[int(v[1])-1][1],vertices[int(v[1])-1][2])
        gl.glVertex3f(vertices[int(v[2])-1][0],vertices[int(v[2])-1][1],vertices[int(v[2])-1][2])
     
   
    gl.glEnd()
    gl.glEndList()
    return genList
  
    

  def normalizeAngle(self, angle):
    while angle < 0: angle += 360 * 16
    while angle > 360 * 16:  angle -= 360 * 16
    return angle

  def setupViewport(self, width, height):
    side = min(width, height)
    gl.glViewport((width - side) // 2, (height - side) // 2, side,  side)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(-4, +4, +4, -4, 1.0, 30.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)

  def setClearColor(self, c):
    gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

  def setColor(self, c):
    gl.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())

class GyroMonitor(mp.Process):
  def __init__(self,q_in):
    mp.Process.__init__(self)  
    self.q_in = q_in
  
  def run(self):    
    app = QApplication(sys.argv)
    window = Gyro3D(self.q_in)
    window.show()
    sys.exit(app.exec_())
    return



if __name__ == '__main__':
  #q_data = mp.Queue()
  #gm = GyroMonitor(q_data)
  #dr = dr.DataReader(q_data)
  #gm.start()
  #dr.start()  
  pass
  

  

  