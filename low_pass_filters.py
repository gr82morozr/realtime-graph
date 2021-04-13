#!/usr/bin/env python
import os, sys
import math, re, time
import numpy as np
import py3toolbox as tb


class RunningAvarageFilter() :
  """
    The simple running average filter
    - the more samples to average the slower it responses to changess.


  """
  def __init__(self, ravg_count):
    self.ravg_count   = ravg_count;
    self.data_history = None


  def compute(self, data_point) :
    # data_point has to be 1d array/list, keeps stacking to data_history
    # self.data_history is 2D array

    # init data_history
    if type(data_point)  not in [list, tuple] :
      data_point = np.array([[data_point]])
    else:
      data_point = np.array([list(data_point)])
    if self.data_history is None:
      self.data_history = np.zeros( (self.ravg_count,  data_point.shape[1]))

    # stack the data
    self.data_history = np.vstack( (self.data_history , data_point) )
    self.data_history = self.data_history[-self.ravg_count: , :]

    # return the mean values of each column
    return tuple(self.data_history.mean(axis=0))



class ExponentialFilter() :
  """
    The ExponentialFilter is based on given weight (w) as below
    Yn = W × Xn + (1 – W) × Yn–1

    

  """
  def __init__(self, weight):
    # weight has to be between 0 ~ 1
    self.weight = weight
    self.last_filtered = None
    self.filtered      = None
  
  def compute(self, data_point) :
    # data_point has to be 1d array/list, keeps stacking to data_history
    # self.last_filtered is same as data_point

    # init data_history
    if type(data_point)  not in [list, tuple] :
      data_point = np.array([[data_point]])
    else:
      data_point = np.array([list(data_point)])

    if self.last_filtered is None:
      self.last_filtered = np.zeros(data_point.shape)

    self.filtered = data_point * self.weight + (1 -self.weight) * self.last_filtered
    self.last_filtered = self.filtered
    self.filtered = self.filtered.flatten()
    return tuple(self.filtered)

    




if __name__ == '__main__':   
  # 2D array
  tb.pause('RunningAvarageFilter')
  ravg_fltr = RunningAvarageFilter(10)
  for i in range(100):
    print (ravg_fltr.compute([i,i*2]))

  tb.pause('ExponentialFilter')
  ef = ExponentialFilter(0.9)
  for i in range(100):
    print (ef.compute((i, i*2)))
