#particle filter for 2D localization
import scipy.stats
import scipy.spatial
import numpy as np
import math
from intersection import *

#kd trees are very useful for range and nearest neighbor searches
#used to determine the distance between a point and the nearest (x,y) in the centerline database
def search_kdtree(t,point):
    """
    	t: the kd tree to search through
    	point: the location of particle to find closest distance to node in centerline
    """
    dist, indexes = t.query(point)
    return dist

def resample(weights):
	#generate particles while there are less than N particles (the number of useful particles we want)
	#if the particle is too far away from centerline, the weight will be zero and resampling will not include these particles
	n = len(weights)
	ind = []
	c = [0.] + [sum(weights[:i+1]) for i in range(n)]
	u0, j = np.random.random(), 0
	for u in [(u0+i)/n for i in range(n)]:
		while u > c[j]:
			j += 1
		ind.append(j-1)
	return ind

def random_walk(x,y,volatility):
	#h=heading
	#random direction from uniform distribution between 0 and 360
	h = np.random.uniform(0, 360)
	#the velocity of the particle is determined by the signal strength last observed and distance particle is from router
	#walk a random distance based on the previous observation
	r = math.radians(h)
	#relax particles according to how far off the particle is from the observed distance
	dx = math.sin(r) * np.random.normal(0, 1)*abs(volatility)
	dy = math.cos(r) * np.random.normal(0, 1)*abs(volatility)
	x += dx
	y += dy
	return x, y


def particle_filter(centerline_x_y, observations, N=1000):
	"""
	centerline_x_y: 2d numpy array of x and y coordinates for nodes of the centerline
	ie. array([[0, 3],
       		   [1, 5],
       		   [2, 1],
       		   [3, 2]])
	observations: dataframe of router location and strength/freq observed (x,y, signal_strength, frequency)
	N: The number of particles to estimate position
	"""
	#get an estimation of building boundaries
	xmin, xmax = np.amin(centerline_x_y[:,0]), np.amax(centerline_x_y[:,0])
	ymin, ymax = np.amin(centerline_x_y[:,1]), np.amax(centerline_x_y[:,1])
	#turn centerline database into a kdtree to easily get nearest neighbour to point
	mytree = scipy.spatial.cKDTree(centerline_x_y)
	#initialize N particles
	#draw from uniform distribution within the building walls using centerline
	x = np.random.uniform(xmin-3, xmax+3, N)
	y = np.random.uniform(ymin-3, ymax+3, N)
	w = [1]*N #weights of the particles, which are equally likely at this point
	for obs in range(0,observations.shape[0]): #while there are observations (routers) seen
		#for each particle
		for i in range(N):
			#run particle through the model
			x[i], y[i] = random_walk(x[i],y[i],observations.iloc[obs][['level']])
			#reweight the particles based on the new position
			#if the distance to closest point on centerline is greater than 3m, than the point is not useful
			if search_kdtree(mytree, (x[i],y[i])) > 3:
				w[i] = 0
			else:
				#calculate distance from particle to the router (x,y)
				d1 = calculateDistance(observations.iloc[obs][['freq']],observations.iloc[obs][['level']])
				#calculate distance participant is predicted to be from the router (x,y)
				#calculate the difference between these two distances
				dx,dy = x[i]-observations.iloc[obs][['easting']],y[i]-observations.iloc[obs][['northing']]
				dist = math.sqrt(dx*dx+dy*dy) 
				diff = abs(math.sqrt(dx*dx+dy*dy) - d1)
				#weight based on the distance
				#what is the probability of observing a signal d1 m away from the distance particle is from the router  
				w[i] = scipy.stats.norm(d1, diff).pdf(dist)
		# Normalise weights
		w <- [x / sum(w) for x in w]
		Neff = 1/sum([x^2 for x in w]) # 1 / crossproduct of w to calculate the number of effective particles
		if Neff < Nmin:
			#np.random.choice(x,n,replace=T,p=w)
			x = [x[j] for j in resample(w)] 
			y = [y[j] for j in resample(w)] 
	
	return zip(x,y)





