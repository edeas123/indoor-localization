#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 17:23:21 2017

@author: ahmadrahman
"""
from scipy import stats
import mysql.connector
import numpy as np
import pandas as pd

df = pd.read_sql("SELECT device_id,record_time,x_axis,y_axis,z_axis FROM SHED7.accelerometer Limit 0,100000", con=cnx)
df2 = pd.read_sql("SELECT device_id,record_time,bssid,freq,level FROM SHED7.wifi where ssid like 'uofs-%' and level > -81 limit 0,100000", con=cnx)

df3 = pd.merge(left=df2,right=df, on='record_time', how='inner')
df3 =df3.groupby('record_time').first()
df3 = df3.reset_index()

start_end_times=[]
start=''
end =''
variances =[]

for i in range(0,250-4):
    x = []
    y = []
    z = []
    x.append(df3.iloc[i]['x_axis'])
    x.append(df3.iloc[i+1]['x_axis'])
    x.append(df3.iloc[i+2]['x_axis'])
    y.append(df3.iloc[i]['y_axis'])
    y.append(df3.iloc[i+1]['y_axis'])
    y.append(df3.iloc[i+2]['y_axis'])
    z.append(df3.iloc[i]['z_axis'])
    z.append(df3.iloc[i+1]['z_axis'])
    z.append(df3.iloc[i+2]['z_axis'])
    variances.append((np.var(x)+np.var(y)+np.var(z))/3)
    if((np.var(x)+np.var(y)+np.var(z))/3 <= 1):
        start=df3.iloc[i]['record_time']
        end=df3.iloc[i+2]['record_time']
        start_end_times.append([start,end])



print ("Total number of intervals = ",len(start_end_times))
print("max variance = ",np.max(variances))

print("min variance = ",np.min(variances))

print("average variance = ",np.mean(variances))




