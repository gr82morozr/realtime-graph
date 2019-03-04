#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2015 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


import sys
import math, random

from PyQt5.QtCore import (QPoint, QPointF, QRect, QRectF, QSize, Qt, QTime,
        QTimer)
from PyQt5.QtGui import (QBrush, QColor, QFontMetrics, QImage, QPainter,
        QRadialGradient, QSurfaceFormat)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget

import OpenGL.GL as gl
import py3toolbox as tb
import re


class Bubble(object):
    def __init__(self, position, radius, velocity):
        self.position = position
        self.vel = velocity
        self.radius = radius

        self.innerColor = self.randomColor()
        self.outerColor = self.randomColor()
        self.updateBrush()

    def updateBrush(self):
        gradient = QRadialGradient(QPointF(self.radius, self.radius),
                self.radius, QPointF(self.radius*0.5, self.radius*0.5))

        gradient.setColorAt(0, QColor(255, 255, 255, 255))
        gradient.setColorAt(0.25, self.innerColor)
        gradient.setColorAt(1, self.outerColor)
        self.brush = QBrush(gradient)


    def randomColor(self):
        red = random.randrange(205, 256)
        green = random.randrange(205, 256)
        blue = random.randrange(205, 256)
        alpha = random.randrange(91, 192)

        return QColor(red, green, blue, alpha)

    def move(self, bbox):
        self.position += self.vel
        leftOverflow = self.position.x() - self.radius - bbox.left()
        rightOverflow = self.position.x() + self.radius - bbox.right()
        topOverflow = self.position.y() - self.radius - bbox.top()
        bottomOverflow = self.position.y() + self.radius - bbox.bottom()

        if leftOverflow < 0.0:
            self.position.setX(self.position.x() - 2 * leftOverflow)
            self.vel.setX(-self.vel.x())
        elif rightOverflow > 0.0:
            self.position.setX(self.position.x() - 2 * rightOverflow)
            self.vel.setX(-self.vel.x())

        if topOverflow < 0.0:
            self.position.setY(self.position.y() - 2 * topOverflow)
            self.vel.setY(-self.vel.y())
        elif bottomOverflow > 0.0:
            self.position.setY(self.position.y() - 2 * bottomOverflow)
            self.vel.setY(-self.vel.y())

    def rect(self):
        return QRectF(self.position.x() - self.radius,
                self.position.y() - self.radius, 2 * self.radius,
                2 * self.radius)


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)

        midnight = QTime(0, 0, 0)
        random.seed(midnight.secsTo(QTime.currentTime()))

        self.object = 0
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        self.image = QImage()
        self.bubbles = []
        self.lastPos = QPoint()

        self.trolltechGreen = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.trolltechPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.animationTimer.timeout.connect(self.animate)
        self.animationTimer.start(25)

        self.setAutoFillBackground(False)
        self.setMinimumSize(200, 200)
        self.setWindowTitle("Overpainting a Scene")

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
        # gl = self.context().versionFunctions()
        # gl.initializeOpenGLFunctions()

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
        self.makeCurrent()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()

        self.setClearColor(self.trolltechPurple.darker())
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glEnable(gl.GL_DEPTH_TEST)
        #gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_MULTISAMPLE)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (0.5, 5.0, 7.0, 1.0))

        self.setupViewport(self.width(), self.height())

        gl.glClear(
                gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glTranslated(0.0, 0.0, -10.0)
        gl.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
        gl.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
        gl.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
        gl.glCallList(self.object)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        """
        for bubble in self.bubbles:
            if bubble.rect().intersects(QRectF(event.rect())):
                bubble.drawBubble(painter)
        """
        
        
        self.drawInstructions(painter)
        painter.end()

    def resizeGL(self, width, height):
        self.setupViewport(width, height)

    def showEvent(self, event):
        #self.createBubbles(20 - len(self.bubbles))
        pass
        
    def sizeHint(self):
        return QSize(600, 600)

        

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
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def createBubbles(self, number):
        for i in range(number):
            position = QPointF(self.width()*(0.1 + 0.8*random.random()),
                               self.height()*(0.1 + 0.8*random.random()))
            radius = min(self.width(), self.height())*(0.0125 + 0.0875*random.random())
            velocity = QPointF(self.width()*0.0125*(-0.5 + random.random()),
                               self.height()*0.0125*(-0.5 + random.random()))

            self.bubbles.append(Bubble(position, radius, velocity))

    def animate(self):
        for bubble in self.bubbles:
            bubble.move(self.rect())

        self.update()

    def setupViewport(self, width, height):
        side = min(width, height)
        gl.glViewport((width - side) // 2, (height - side) // 2, side,
                side)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-4, +4, +4, -4, 1.0, 30.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def drawInstructions(self, painter):
        text = "Click and drag with the left mouse button to rotate the Qt " \
                "logo."
        metrics = QFontMetrics(self.font())
        border = max(4, metrics.leading())

        rect = metrics.boundingRect(0, 0, self.width() - 2*border,
                int(self.height()*0.125), Qt.AlignCenter | Qt.TextWordWrap,
                text)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(QRect(0, 0, self.width(), rect.height() + 2*border),
                QColor(0, 0, 0, 127))
        painter.setPen(Qt.white)
        painter.fillRect(QRect(0, 0, self.width(), rect.height() + 2*border),
                QColor(0, 0, 0, 127))
        painter.drawText((self.width() - rect.width())/2, border, rect.width(),
                rect.height(), Qt.AlignCenter | Qt.TextWordWrap, text)

    def setClearColor(self, c):
        gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        gl.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())


if __name__ == '__main__':

    app = QApplication(sys.argv)

    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = GLWidget()
    window.show()
    sys.exit(app.exec_())