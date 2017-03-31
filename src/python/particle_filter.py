#particle filter for 2D localization
import scipy.stats
import scipy.spatial
import numpy as np
import math
from intersection import *
from initialize import *

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

def bootstrap_resample(centerline, particles, n=500):
	"""
	centerline: kd tree of the centerline
	bootstrap sampling, resample everytime
	given weights for the nodes along centerline, resample these nodes (ie. resample in the most likely places (nodes))
	then do a random walk in particle filter ("fuzz out") so the particles will disperse off of the centerline again (in case individuals are in a room and potentially further away from centerline than 3m)
	require the nodes of centerline for a floor currently on (as a kd tree)
	require the current locations of all particles
	get the closest node on centerline to the particle and increase that node's weight
	resample particles at these nodes
	"""
	#for each particle, get the closest node index on centerline and the index
	ind=[]
	for p in particles:
		dist, index = search_kdtree(centerline, p)
		ind.append(index)

	# get a frequency table of the list of indices
	counts = Counter(ind)

	#normalize the weights
	fact=1.0/sum(counts.itervalues())
	for i in counts:
			counts[i] = counts[i]*fact

	w = counts.values()
	#resample points on centerline using these new weights
	k = counts.keys()
	p_new = np.random.choice(k,n,replace=True,p=w) #now we have n selected indices based on weight (w) in the kd tree, now we find the points 
	#return new x and y points using the resample indices
	x_r = centerline.data[p_new, 0]
	y_r = centerline.data[p_new, 1]

	#return list x_r and y_r
	return x_r, y_r


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

def gaussian(mu, sigma, x):
	"""
	calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
	mu: particle distance to the router
	sigma: standard deviation
	x: distance to the router measured by the phone
	return gaussian probability
	"""
	# calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
	return math.exp(- ((mu - x) ** 2) / (sigma ** 2) / 2.0) / math.sqrt(2.0 * math.pi * (sigma ** 2))

def measurement_prob(x, y, routers):
	"""
	Calculate the measurement probability: how likely a measurement should be
	x,y: current particle coordinates
	routers: df of routers for one time step
	return probability
	"""
	prob = 1.0
	for i in range(routers.shape[0]):
		#calculate distance from particle to the router (x,y)
		dist = calculateDistance(routers.iloc[i]['freq'], routers.iloc[i]['level'])
		#calculate distance participant is predicted to be from the router (x,y)
		#calculate the difference between these two distances
		dx,dy = x-routers.iloc[i]['easting'],y-routers.iloc[i]['northing']
		measure = math.sqrt(dx*dx+dy*dy) 
		prob *= gaussian(dist, 3, measure)
	return prob


def particle_filter(centerline_x_y, observations, N=500, Nmin=250):
	"""
	Most simple version of particle filter, no limitations based on centerline
	centerline_x_y: 2d numpy array of x and y coordinates for nodes of the centerline 
	ie. array([[0, 3],
	       		  [1, 5],
	       		  [2, 1],
	       		  [3, 2]])
	observations: dataframe of router location and strength/freq observed (easting,northing, level, freq, record_time)
	"""
	x,y= initialize(observations, N)
	w = [j / sum([1.]*len(x)) for j in [1.]*len(x)] #weights of the particles, which are equally likely at this point
	for obs in observations.record_time.unique(): #while there are observations (routers) seen
		#df where time stamp is the same as obs
		df = observations.loc[observations['record_time'] == obs]
		#for each particle
		for i in range(N):
			#run particle through the model
			x[i], y[i] = random_walk(x[i],y[i],w[i])
			#reweight the particles based on the new position
			#if the distance to closest point on centerline is greater than 3m, than the point is not useful
			#ignore this, every particle gets a weight now, I will add the snapping to this method 
			#if search_kdtree(mytree, (x[i],y[i])) > 3:
				#w[i] = 0
			#else:
			#weight based on the distance
			#what is the probability of observing a signal d1 m away from the distance particle is from the router  
			w[i] = measurement_prob(x[i], y[i], df)
			# Normalise weights
		s = sum(w)
		crossprod= sum([a**2 for a in w])
		if crossprod != 0 and s !=0: #make sure no division by 0 if weights are too small
			w = [b / s for b in w]
			Neff = 1/crossprod
			if Neff < Nmin:
				#resample (or the other startegy above)
				x = np.random.choice(x,N,replace=True,p=w)
				y = np.random.choice(y,N,replace=True,p=w)
		else:
			x,y=initialize(df, N) #no good particles, reinitialize based on current duty cycle
	return zip(x,y)





