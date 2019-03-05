#!/usr/bin/env python

import sys
import math, random, re, time
import OpenGL.GL as gl
import py3toolbox as tb
import multiprocessing as mp
import serial

from PyQt5.QtCore import (QPoint, QPointF, QRect, QRectF, QSize, Qt, QTime, QTimer)
from PyQt5.QtGui import (QBrush, QColor, QFontMetrics, QImage, QPainter,  QSurfaceFormat)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget

def get_config() :
  config = { 
    "window_w" : 600,
    "window_h" : 400,
    "object_file" : "shuttle4.obj",
    
    "data_channels": {
      "FILE" : {
        "file_name" : "sample_data.csv"
      },
      
      "SERIAL" : {
        "port"      : "COM3",
        "baud_rate" : "15200"
      },
      
      "TCP_SERVER" : {
        "tcp_port"   : 5678
      },
      
      "TCP_CLIENT" : {
        "server_host": "192.168.1.1",
        "tcp_port"   : 5678
      },

      "UDP_SERVER" : {
        "udp_port"   : 5678
      
      },
      
      "UDP_CLIENT" : {
        "server_host": "192.168.1.1",
        "tcp_port"   : 5678
      }
    }
  }
  
  return config



class DataReader(multiprocessing.Process):
  def __init__(self, out_q) :
    multiprocessing.Process.__init__(self)
    self.config = get_config()
    self.out_q  = out_q 
    self.data_dic = {}
    self.data_count = 0
    self.sample_rate = 0
    self.receive_time = time.time()
  
  def read_serial_data(self, serial_port, serial_rate, serial_timeout):  
    if self.config['LOG_SOURCE_DATA'] == True and self.config['FILE_TEST'] == False : 
      tb.rm_file(self.config['DATA_FILE'])
    
    ser = serial.Serial(port=serial_port , baudrate=serial_rate, timeout=serial_timeout)
    print("connected to: " + ser.portstr)
    this_line = ""
  
    while True:
      try :
        one_byte = ser.read(1)
        if len(one_byte) < 1 : continue
        if one_byte == b"\r":    #method should returns bytes
          self.data_count +=1
        #  print (this_line)
          parsed_data = self.parse_csv_data(this_line)
          if parsed_data is not None:
            self.push_out_q(parsed_data)
            if self.config['LOG_SOURCE_DATA'] == True:
              tb.write_file(file_name=self.config['DATA_FILE'], text=this_line + "\n", mode="a")
          this_line = ""      
        else:
          this_line += one_byte.decode('ascii')
   
      except Exception as err:
        print (err)
        time.sleep(1)
        pass         

  def read_network_data(self, host, port) : 
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    while True:
      this_line = client.recv(4096).decode("utf-8")
      parsed_data = self.parse_csv_data(this_line)
      if parsed_data is not None:
        self.push_out_q(parsed_data)
        if self.config['LOG_SOURCE_DATA'] == True:
          tb.write_file(file_name=self.config['DATA_FILE'], text=this_line + "\n", mode="a")
    pass

  def read_file_data(self, data_file):  
    data_fh  = open(data_file, "r")
    for data_line in data_fh.read().splitlines(True):
      if (len(data_line) >= 1) :
        self.push_out_q(self.parse_csv_data(data_line))

    
  def parse_csv_data(self, data_str):
    data_json = None
    for rec in data_str.split(','): 
      if len(rec) < 1 : continue
      m = re.match("\s*(\w+)\s*\=\s*([^\,]+)\s*", rec)
      if m: 
        self.data_dic[m.group(1)] = float(m.group(2).rstrip())
        data_json = json.dumps(self.data_dic)
      else:
        return None
      if  self.config['DEBUG_MODE'] == 'Y' : 
        tb.write_log(self.config['LOG_FILE'],data_json)
    return data_json
  
    
  def push_out_q(self, data_message):
    #self.sample_rate =  int(1 / (time.time() - self.receive_time)) 
    #print ('sample rate = ', self.sample_rate, data_message)
    #self.receive_time = time.time()    
    self.out_q.put(data_message) 
    #self.out_q.send(data_message)
 
  def run(self):  
    #self.create_task_sync_files()
    if self.config['DATA_SOURCE'] == 'FILE':
      self.read_file_data(self.config['DATA_FILE'])
    elif self.config['DATA_SOURCE'] == 'SERIAL' :
      self.read_serial_data(self.config['SERIAL_PORT'],self.config['SERIAL_RATE'], int(self.config['SERIAL_TIMEOUT']))
    elif self.config['DATA_SOURCE'] == 'NETWORK':
      self.read_network_data(self.config['NETWORK_HOST'],self.config['NETWORK_PORT'])
  



  
class Gyro3D(QOpenGLWidget):
  def __init__(self,  q_in=None):
    super(Gyro3D, self).__init__()
    self.config = get_config()
    self.q_in   = q_in
    self.object = 0
    self.xRot   = 0
    self.yRot   = 0
    self.zRot   = 0
  
    self.trolltechGreen = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
    self.trolltechPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

    self.animationTimer = QTimer()
    self.animationTimer.setSingleShot(False)
    self.animationTimer.timeout.connect(self.update)
    self.animationTimer.start(10)

    self.readDataTimer = QTimer()
    self.readDataTimer.setSingleShot(False)
    self.readDataTimer.timeout.connect(self.readData)
    self.readDataTimer.start(15)

    self.setAutoFillBackground(False)
    self.setMinimumSize(200, 200)
    self.setWindowTitle("Gyro 3D Real-time Monitor")
    self.time = time.time()

  def readData(self):
    if self.q_in.qsize()>0 :
      self.setXRotation(self.q_in.get())


  def setXRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.xRot:
      self.xRot = angle

  def setYRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.yRot:
      self.yRot = angle

  def setZRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.zRot:
      self.zRot = angle

  def initializeGL(self):
    self.object = self.makeObject()

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

  def paintEvent(self, event):
    fps = 1 / (time.time() - self.time)
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
    gl.glTranslated(0.0, 0.0, -10.0)
    gl.glRotated(self.xRot , 1.0, 0.0, 0.0)
    gl.glRotated(self.yRot , 0.0, 1.0, 0.0)
    gl.glRotated(self.zRot , 0.0, 0.0, 1.0)
    gl.glCallList(self.object)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()

  

  def resizeGL(self, width, height):
    self.setupViewport(width, height)

  def showEvent(self, event):
    pass
    
  def sizeHint(self):
    return QSize(600, 600)


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
  q_data = mp.Queue()  
  for x in range(36000):  q_data.put(x)
  
  dr = DataReader(q_data)
  gm = GyroMonitor(q_data)
  
  dr.start()
  gm.start()
  
  dr.join()
  gm.join()
  

  