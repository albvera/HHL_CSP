"""
Cluster the nodes using k-means
Returns a list of nodes
"""
import sys, time, gc
from numpy.linalg import norm
from sklearn.cluster import k_means
def cluster(G,n_clusters,n_init=10,tol=0.1,random_state=1259):
	print 'Clustering: ',
	sys.stdout.flush()
	init_time = time.time()
	X = nx.get_node_attributes(G,'XY').values()
	V = nx.get_node_attributes(G,'XY').keys()
	c,_,_=k_means(X,n_clusters=n_clusters,n_init=n_init,tol=tol,random_state=random_state)	# c is a list of cluster centers
	H = []										# H contains the points closest to the cluster centers	
	for i in xrange(0,n_clusters):				# identify each cluster center. Iterative is more stable
		min_v = None
		min_dist = float("inf")
		for j in xrange(0,len(X)):
			d = norm(c[i]-X[j])
			if d<min_dist:
				min_dist=d
				min_v=V[j]
		H.append(min_v)
	H = list(set(H))							# remove duplicates, if any	
	
	X,V,c = None,None,None
	gc.collect()
	minut, secs = divmod(time.time() - init_time, 60)
	print '{:0>2}:{:0>2}'.format(int(minut),int(secs))
	return H

import networkx as nx

def dist_forward(G,v,w):
	return G[v][w]['dist']

def dist_backward(G,v,w):
	return G[w][v]['dist']

"""
If reverse=1, returns predecessors of v
Otherwise, returns successors of v
Requires global variable is_direced
"""
def neighbours(G,v,reverse):
	if not nx.is_directed(G):
		return G.neighbors(v)
	if reverse == 1:
		return G.predecessors(v)
	else:
		return G.successors(v)

"""
Run Dijkstra to obtain all the lengths in the efficient frontier
Receives augmented graph without sink nodes, source, target and B
"""
def dijkstra_frontier(G,s,t,B):
	if t == s:
		return [0]*(B+1)
	lengths,_=nx.single_source_dijkstra(G,(s,B),weight='dist')			
	dist = [float("inf")]*(B+1)
	if (t,B) in lengths:
		dist[0] = lengths[(t,B)]
	for x in xrange(B-1,-1,-1):								# b = B-x
		if (t,x) not in lengths or lengths[(t,x)]>=dist[B-x-1]:
			dist[B-x] = dist[B-x-1]
			continue		
		dist[B-x] = lengths[(t,x)]
	return dist

"""
Receives augmented graph with sink nodes
Runs length query
"""
def dijkstra_sink(G,s,t,b):
	try:
		return int(nx.shortest_path_length(G,(s,b),(t,-1),weight='dist'))
	except:
		return float("inf")	#Nodes are not reachable

def dijkstra_length(G,s,t):
	try:
		return int(nx.shortest_path_length(G,s,t,weight='dist'))
	except:
		return float("inf")	#Nodes are not reachable
