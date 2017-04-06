#statistics and visualization

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import math
import numpy as np
import pandas as pd

#calculate the mean x,y coord in a group of particles
def get_centroid(x,y):
	"""
	Get the mean point out of all the particles
	x: list of x coordinates
	y: list of y coordinates
	"""
	return sum(x)/len(x), sum(y)/len(y)

#calculate diatance between a particle and the mean
def dist(m_x, m_y, x,y): 
	"""
	Get the distance between a particle and the mean point
	m_x,m_y = mean x,y coordinates
	x: list of x coordinates
	y: list of y coordinates
	"""
	return math.sqrt(sum([(m_x-x)**2, (m_y-y)**2]))

#calculate the variance of particles
def  get_var(m_x, m_y, x, y):
	"""
	Get the variance for the particles
	m: mean x,y coordinate
	x: list of x coordinates
	y: list of y coordinates
	"""
	total=0
	for i in range(0,len(x)):
		total += dist(m_x, m_y, x[i], y[i])**2
	return total/(len(x)-1)

#calculate precision
def get_precision(x,y):
	"""
	Get the precision for a group of particles
	x: list of x coordinates
	y: list of y coordinates
	"""
	mean_x, mean_y = get_centroid(x,y)
	var = get_var(mean_x, mean_y, x, y)
	sd = math.sqrt(var)
	prec = sd/math.sqrt(len(x))
	return prec


#calculate the precision of particles in each duty cycle
#return list to plot for every duty cycle in a line graph and report the average precision

def plot_precision(particle_df):
	precision = []
	for d in df.duty_cycle.unique():
		sl = df.loc[df['duty_cycle'] == d]
		precision.append(get_precision(list(sl['easting']),list(sl['northing'])))

	print "Average precision:" 
	print np.mean(precision)
	return precision


#campus final duty cycle example
#plt.xlim(387707.046599004 , 388593.667122245)
#plt.ylim(5776727.173058612 , 5777131.986368239)
#Thorvalson
#plt.xlim(387973.667757246, 388145.276850465​)
#plt.ylim(5776978.898145395, 5777082.085851771)
#img = mpimg.imread('C:\\Python27\\ArcGIS10.5\\campus.png')
#img = mpimg.imread('C:\\Python27\\ArcGIS10.5\\thor.png')
#plt.imshow(img, extent=[387973.667757246, 388145.276850465, 5776978.898145395, 5777082.085851771])
#obs = obs = df.loc[df['duty_cycle'] == df.duty_cycle.unique()[-1]]
#plt.plot(obs['easting'],obs['northing'],"o")
#plt.show()
