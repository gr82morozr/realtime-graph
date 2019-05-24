import math
from pyquaternion import Quaternion

my_quaternion = Quaternion (0.31,-0.56,-0.29,-0.72)
angle = my_quaternion.angle
u = my_quaternion.axis 
print (angle, u )
