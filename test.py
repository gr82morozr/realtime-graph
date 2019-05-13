import py3toolbox as tb

rawdata   =  'qW=-0.85,qX=-0.05,qY=-0.05,qZ=-0.53'
matchdata =  tb.re_findall ('(\w+)\=(\-*\d+\.\d*)', rawdata)   



mappeddata = {}
for (k,v) in matchdata:
  mappeddata[k] = v

print (mappeddata)
