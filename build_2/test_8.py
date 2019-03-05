#!/usr/bin/env python

import sys
import math
import re,time

from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QOpenGLWidget, QSlider,   QWidget)

import OpenGL.GL as gl
import py3toolbox as tb
import multiprocessing as mp



class Window(QWidget):
  def __init__(self, q_in):
    super(Window, self).__init__()
    self.glWidget = GLWidget()
    self.xSlider = self.createSlider()
    self.ySlider = self.createSlider()
    self.zSlider = self.createSlider()

    self.xSlider.valueChanged.connect(self.glWidget.setXRotation)
    self.glWidget.xRotationChanged.connect(self.xSlider.setValue)
    self.ySlider.valueChanged.connect(self.glWidget.setYRotation)
    self.glWidget.yRotationChanged.connect(self.ySlider.setValue)
    self.zSlider.valueChanged.connect(self.glWidget.setZRotation)
    self.glWidget.zRotationChanged.connect(self.zSlider.setValue)

    mainLayout = QHBoxLayout()
    mainLayout.addWidget(self.glWidget)
    mainLayout.addWidget(self.xSlider)
    mainLayout.addWidget(self.ySlider)
    mainLayout.addWidget(self.zSlider)
    self.setLayout(mainLayout)

    self.xSlider.setValue(15 * 16)
    self.ySlider.setValue(345 * 16)
    self.zSlider.setValue(0 * 16)

    self.setWindowTitle("Hello GL")

  def createSlider(self):
    slider = QSlider(Qt.Vertical)

    slider.setRange(0, 360 * 16)
    slider.setSingleStep(16)
    slider.setPageStep(15 * 16)
    slider.setTickInterval(15 * 16)
    slider.setTickPosition(QSlider.TicksRight)

    return slider


class GLWidget(QOpenGLWidget):
  xRotationChanged = pyqtSignal(int)
  yRotationChanged = pyqtSignal(int)
  zRotationChanged = pyqtSignal(int)

  def __init__(self, parent=None):
    super(GLWidget, self).__init__(parent)
    self.time = time.time()
    self.object = 0
    self.xRot = 0
    self.yRot = 0
    self.zRot = 0

    self.lastPos = QPoint()

    self.trolltechGreen = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
    self.trolltechPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

  def getOpenglInfo(self):
    info = """
      Vendor: {0}
      Renderer: {1}
      OpenGL Version: {2}
      Shader Version: {3}
    """.format(
      gl.glGetString(gl.GL_VENDOR),
      gl.glGetString(gl.GL_RENDERER),
      gl.glGetString(gl.GL_VERSION),
      gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION)
    )

    return info

  def minimumSizeHint(self):
    return QSize(50, 50)

  def sizeHint(self):
    return QSize(800, 800)

  def setXRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.xRot:
      self.xRot = angle
      self.xRotationChanged.emit(angle)
      self.update()

  def setYRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.yRot:
      self.yRot = angle
      self.yRotationChanged.emit(angle)
      self.update()

  def setZRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.zRot:
      self.zRot = angle
      self.zRotationChanged.emit(angle)
      self.update()

  def initializeGL(self):
    print(self.getOpenglInfo())

    self.setClearColor(self.trolltechPurple.darker())
    self.object = self.makeObject()
    gl.glShadeModel(gl.GL_FLAT)
    gl.glEnable(gl.GL_DEPTH_TEST)
    

  def paintGL(self):
    fps = 1 / (time.time() - self.time)
    self.time = time.time() 
    print (fps)
    
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    self.setClearColor(self.trolltechPurple.darker())
    gl.glShadeModel(gl.GL_SMOOTH)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_LIGHT0)
    gl.glEnable(gl.GL_MULTISAMPLE)
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (0.5, -5.0, 7.0, 1.0)) 
    #self.setupViewport(self.width(), self.height())
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    gl.glTranslated(0.0, 0.0, -10.0)
    gl.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
    gl.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
    gl.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
    gl.glCallList(self.object)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()
    
  def resizeGL(self, width, height):
    side = min(width, height)
    if side < 0:
      return

    gl.glViewport((width - side) // 2, (height - side) // 2, side, side)

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(-4, +4, +4, -4, 1.0, 30.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)

  def mousePressEvent(self, event):
    self.lastPos = event.pos()

  def mouseMoveEvent(self, event): 
    dx = event.x() - self.lastPos.x()
    dy = event.y() - self.lastPos.y()

    if event.buttons() & Qt.LeftButton:
      self.setXRotation(self.xRot + 8 * dy)
      self.setYRotation(self.yRot + 8 * dx)
    elif event.buttons() & Qt.RightButton:
      self.setXRotation(self.xRot + 8 * dy)
      self.setZRotation(self.zRot + 8 * dx)

    self.lastPos = event.pos()
  
  def makeObject(self):
    genList = gl.glGenLists(1)
    gl.glNewList(genList, gl.GL_COMPILE)
    vertices = []
    colors   = [(0.0,0.0,1.0), (0.0,1.0,0.0),(1.0,0.0,0.0)]
    vnormals = []
    gl.glBegin(gl.GL_TRIANGLES)   
    
    #gl.glBegin(gl.GL_LINES)    
    
    obj_lines = tb.read_file(file_name='shuttle4.obj',return_type='list')
    for obj_line in obj_lines:
      if obj_line.startswith('v ') : 
        obj_line = obj_line.replace('v ','')
        [x,y,z] = obj_line.split(" ")
        vertices.append ([float(x), float(y),float(z)])
     
      if obj_line.startswith('vn ') : 
        obj_line = obj_line.replace('vn ','')
        [vn_x,vn_y,vn_z] = obj_line.split(" ")
        vnormals.append ([float(vn_x), float(vn_y),float(vn_z)])       

    i = 0
    
    for obj_line in obj_lines:
      if obj_line.startswith('f ') : 
        obj_line = obj_line.replace('f ','')
        v = re.findall(r"\s*(\d+)\/\/\d+\s*", obj_line)
        vn = re.findall(r"\s*\d+\/\/(\d+)\s*", obj_line)
        #print (int(v[0]) + int(v[1]) + int(v[2]))
        i +=1
        gl.glNormal3d(vnormals[int(vn[0])-1][0],vnormals[int(vn[0])-1][1],vnormals[int(vn[0])-1][2])
        gl.glVertex3f(vertices[int(v[0])-1][0],vertices[int(v[0])-1][1],vertices[int(v[0])-1][2])
        gl.glVertex3f(vertices[int(v[1])-1][0],vertices[int(v[1])-1][1],vertices[int(v[1])-1][2])
        gl.glVertex3f(vertices[int(v[2])-1][0],vertices[int(v[2])-1][1],vertices[int(v[2])-1][2])
     
   
    gl.glEnd()
    gl.glEndList()
    return genList

 
  

  def normalizeAngle(self, angle):
    while angle < 0: angle += 360 * 16
    while angle > 360 * 16: angle -= 360 * 16
    return angle

  def setClearColor(self, c):
    gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

  def setColor(self, c):
    gl.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())


if __name__ == '__main__':
  q1 = mp.Queue()  
  app = QApplication(sys.argv)
  window = Window(q1)
  window.show()

  window.glWidget.setXRotation(10)
  sys.exit(app.exec_())
