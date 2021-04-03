#!/usr/bin/python


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
app = pg.mkQApp("MultiPlot Speed Test")
 

win = pg.GraphicsWindow(title="Basic plotting")

#plot[0] = pg.plot()

plot = []
plot.append(win.addPlot(1,1,1,1))
plot.append(win.addPlot(1,1,1,1))
plot.append(win.addPlot(2,1,1,1))
plot.append(win.addPlot(3,1,1,1))
plot.append(win.addPlot(1,2,1,1))
plot.append(win.addPlot(2,2,1,1))
plot.append(win.addPlot(3,2,1,1))

plot[0].setWindowTitle('plot[0]')
pg.setConfigOptions(useOpenGL=True)
#pg.setConfigOptions(antialias=True)    

plot[0].setLabel('bottom', 'Index', units='B')

nPlots = 10
nSamples = 200
curves = []
pen=pg.mkPen('g', width=2)
for idx in range(nPlots):
    pen=pg.mkPen(idx,nPlots*1., width=4)
    curve = pg.PlotCurveItem(pen=pen)
    plot[1].addItem(curve)
    plot[2].addItem(curve)
    


    curve.setPos(0,idx*6)
    curves.append(curve)

for p in plot:
    p.setYRange(0, nPlots*6)
    p.setXRange(0, nSamples)
    p.resize(1400,800)

#rgn = pg.LinearRegionItem([nSamples/5.,nSamples/3.])
#plot[0].addItem(rgn)


data = np.random.normal(size=(nPlots*23,nSamples))
ptr = 0
lastTime = time()
fps = None
count = 0
def update():
    global curve, data, ptr, plot, lastTime, fps, nPlots, count
    count += 1

    for i in range(nPlots):
        curves[i].setData(data[(ptr+i)%data.shape[0]])

    ptr += nPlots
    now = time()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0/dt
    else:
        s = np.clip(dt*3., 0, 1)
        fps = fps * (1-s) + (1.0/dt) * s
    plot[0].setTitle('%0.2f fps' % fps)
    #app.processEvents()  ## force complete redraw for every plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    pg.mkQApp().exec_()
