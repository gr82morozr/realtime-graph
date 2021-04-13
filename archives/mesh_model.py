# -*- coding: utf-8 -*-
"""
Simple examples demonstrating the use of GLMeshItem.

"""

## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl

app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('pyqtgraph example: GLMeshItem')
w.setCameraPosition(distance=40)

g = gl.GLGridItem()
g.scale(2,2,1)
w.addItem(g)

import numpy as np


## Example 1:
## Array of vertex positions and array of vertex indexes defining faces
## Colors are specified per-face


# Example 4:
# wireframe

md = gl.MeshData.sphere(rows=20, cols=20)
m4 = gl.GLMeshItem(meshdata=md, smooth=True, drawFaces=False, drawEdges=True, edgeColor=(1,1,1,1))
m4.translate(0,0,0)
w.addItem(m4)


print (md)




    


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()