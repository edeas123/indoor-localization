#particle filter for 2D localization
import scipy.stats
import scipy.spatial
import numpy as np
import math
from intersection import *
from initialize import *
import centerline as c
import pandas as pd

#kd trees are very useful for range and nearest neighbor searches
#used to determine the distance between a point and the nearest (x,y) in the centerline database
def search_kdtree(t,point):
    """
    	t: the kd tree to search through
    	point: the location of particle to find closest distance to node in centerline
    """
    dist, indexes = t.query(point)
    return dist, indexes

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
	return math.sqrt(sum([(m_x-y)**2, (m_y-y)**2]))

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
	return total//(len(x)-1)

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
		#how close if the particle to the signal strength distance?
		diff = abs(dist-measure) 
		prob *= 1/diff
	return prob

def particle_filter(observations, init_particles, N=500, Nmin=250, bootstrap=False):
	"""
	Most simple version of particle filter, no limitations based on centerline
	centerline_x_y: 2d numpy array of x and y coordinates for nodes of the centerline 
	ie. array([[0, 3],
	       		  [1, 5],
	       		  [2, 1],
	       		  [3, 2]])
	observations: dataframe of router location and strength/freq observed (easting,northing, level, freq, record_time)
	init_particles: a list of x, y coordinates indicating the initial positions of the particles
	"""
	#initialize the particles
	x,y= [list(c) for c in zip(*init_particles)]
	z = [0.]*N #building and floor info for each particle 
	w = [j / sum([1.]*len(x)) for j in [1.]*len(x)] #weights of the particles, which are equally likely at this point
	particle_lifecycle = []
	for obs in observations.record_time.unique(): #while there are observations (routers) seen
		#df where time stamp is the same as obs
		df = observations.loc[observations['record_time'] == obs]
		#since we are not sure what floor the participant is on, weight each record in the duty cycle by signal strength
		se = pd.Series(1/abs(df.level))
		#add this as a column to df
		df.is_copy = False
		df['weight'] = se.values
		#based on the combined weight of each floor and building
		fl =  df.groupby('floor').sum().reset_index()
		bldg = df.groupby('building').sum().reset_index()
		#create a dictionary of each floor and the weight
		b_dict = bldg[['building','weight']].set_index('building').to_dict()
		f_dict = fl[['floor','weight']].set_index('floor').to_dict()
		#multiply building probability by floor probability
		mul = pd.Series.multiply(df['floor'].map(f_dict['weight']),df['building'].map(b_dict['weight']))
		#get the index of the maximum probability
		index = mul.idxmax()
		#use index to select the row of the data frame and  floor and building
		floor = df.loc[mul.idxmax()]['floor']
		building = df.loc[mul.idxmax()]['building']

		#set a floor and building for the duty cycle time obs
		z = np.asarray([(floor, building, str(df.record_time))] * N)
		#for each particle
		for i in range(N):
			#run particle through the model
			x[i], y[i] = random_walk(x[i],y[i],w[i])
			w[i] = measurement_prob(x[i], y[i], df) #1/difference between router signal strength distance and particle distance from router
			#reweight the particles based on the new position
			#if the distance to closest point on centerline is greater than 3m, than the point is not useful
			#ignore this, every particle gets a weight now, I will add the snapping to this method 
			#if search_kdtree(mytree, (x[i],y[i])) > 3:
				#w[i] = 0
			#else:
			#weight based on the distance
			#what is the probability of observing a signal d1 m away from the distance particle is from the router
		# Normalise weights if not equal to zero
		w = [b / sum(w) for b in w]
		if bootstrap == True:
			#perform bootstrap resampling if bootstrap is true, resampling is done every time and snapped to centerline
			x = np.random.choice(x,N,replace=True,p=w)
			y = np.random.choice(y,N,replace=True,p=w)
			#generate the centerline tree for the floor, building
			tree = scipy.spatial.cKDTree(c.get_points(floor,building))
			x,y = bootstrap_resample(tree, zip(x,y),N)
		
		else: #if not,perform same as below and resample only if the number of particles with effective weights is small
			crossprod= sum([a**2 for a in w])
			if crossprod != 0: #make sure no division by 0 if weights are too small
				Neff = 1/crossprod
				if Neff < Nmin:
					#resample (or the other startegy above)
					x = np.random.choice(x,N,replace=True,p=w)
					y = np.random.choice(y,N,replace=True,p=w)
			else:
				x,y=initialize(df, N) #no good particles, reinitialize based on current duty cycle
		#save particles for the duty cycle in list
		points = np.asarray(zip(x,y))
		particle_lifecycle.append(pd.DataFrame(np.concatenate((points,z), axis=1), columns=['easting', 'northing', 'floor', 'building', 'duty_cycle']))
	return particle_lifecycle



		
