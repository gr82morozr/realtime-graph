import math
import numpy as np
from scipy.spatial.transform import Rotation 


def get_rotation_axis_angle(Q,  degrees=False):
  # https://en.wikipedia.org/wiki/Axis%E2%80%93angle_representation#Rotation_vector
  axis = Rotation.from_quat(Q).as_rotvec() 
  angle = np.linalg.norm(axis)
  axis = axis.tolist()
  if degrees : angle = angle * 180 / math.pi

  return angle, axis



def get_euler(Q,degrees=False):
  return Rotation.from_quat(Q).as_euler('xyz', degrees=degrees)

  
def rotate_vector (Q, orig_vect, reverse=False): 
  if reverse != True:
    r = Rotation.from_quat(Q)
  else:
    r = Rotation.from_quat(Q).inv()

  return r.apply(orig_vect)
       
if __name__ == '__main__':   
  
  #r_m = quaternion_rotation_matrix([1.0,0.8,0.2,0.9])
  #print (r_m.shape)

  Q = [1,1,0,1]
  #print ( Rotation.from_quat(Q).as_rotvec() )
  #print (np.linalg.norm(Rotation.from_quat(Q).as_rotvec() ))

  print (get_rotation_axis_angle(Q, degrees=True))
  p,r,y = get_euler(Q)
  print (p,r,y)
  
    