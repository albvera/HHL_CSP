import networkx as nx
from graph_info import *
from ch import *
from costs import *
import time, progressbar, gc

"""
Creates hub labels based on hierarchies
The hubs are three-tuples: N(v),I(v),D(v)
N(v)=#items in hub, I(v)=array with id's in hub, D(v) = array with distances
D(v)[k] = dist(v,I(v)[k]) for k=0,...,N(v)-1
I(v) is sorted in increasing order
Each three-tuple can be backward (reverse=1) or forward (reversed=0)
Assumes the nodes have unique ID attribute
List of targets (backward hubs) and sources (forward hubs) can be specified
"""
from array import array

def create_labels(G,Id_map,sources = None, targets = None):
	I,D,N = {},{},{}	
	#I[0] is an dictionary for forward, I[0][v] is an array with the id's of nodes in hubforward(v)
	I[0],I[1] = {},{}
	#D[0] is an dictionary for forward, D[0][v] is an array of distances from node to hub				
	D[0],D[1] = {},{}
	N[0],N[1] = {},{}										# sizes of forward and backward hubs
	objectives = {}											# used to work with sources or targets
	objectives[0] = sources
	objectives[1] = targets
	rank = nx.get_node_attributes(G,'rank')
	ID = nx.get_node_attributes(G,'ID')
	bar = progressbar.ProgressBar()
	print 'Creating labels'
	for v in bar(G.nodes()):		
		for reverse in range(0,2):								
			if objectives[reverse]!= None and v not in objectives[reverse]:
				continue									# v is not an objective (source or target)		
			hub,_ = ch_search(G,v,reverse,rank)				# hub is a dict, keys are nodes visited in the search	
			N[reverse][v] = len(hub)
			I[reverse][v] = sorted({ID[k] for k in hub.keys()})
			D[reverse][v] = []
			for i in I[reverse][v]:			
				w = Id_map[i]
				D[reverse][v].append(hub[w])				# get distance to key			
	return(I,D,N)

"""
Prune labels by bootstrapping hub labels
G is the pruned augmented graph
Not only removes nodes with incorrect label, but also those who are not efficient
Id_map[Id] returns the node with that ID
"""
import operator
def prune_labels_bootstrap(I,D,N,Id_map,G,omit_forward=False,extra_edges=True):		
	if extra_edges:	
		query = hl_query_extra_surplus 
	else:	
		query = hl_query_pruned
	keys = {}
	keys[1] = I[1].keys()
	keys[0] = I[0].keys()
	keys[0].sort(key=operator.itemgetter(1))					# order nodes by ascending budget
	for reverse in range(1,-1,-1):	
		if omit_forward and reverse==0:
			continue
		if reverse == 1:
			print 'Pruning backward hubs'
		else:
			print 'Pruning forward hubs'
		bar = progressbar.ProgressBar()
		for v in bar(keys[reverse]):							# prune the hub of node v
			j = 0
			while j<N[reverse][v]:								
				dist = surplus = 0
				w = Id_map[I[reverse][v][j]]					# j-th node in the hub
				if reverse == 0 and v!=w:						# if (w,x) not a sink-node, compute SP (v,b-x)->(w,0)
					dist,surplus = query(I,D,v[0],w[0],v[1]-w[1])		
				if reverse == 1 and v!=w:						# dist wv and (v,b) is a sink node
					dist,surplus = query(I,D,w[0],v[0],w[1])
				if dist<D[reverse][v][j] or surplus>0:
					del I[reverse][v][j]
					del D[reverse][v][j]
					N[reverse][v]-=1
				else:
					j+=1
		gc.collect()	

"""
Prune labels of not augmented graph
"""
def prune_labels_regular(I,D,N,Id_map):		
	for reverse in range(1,-1,-1):
		if reverse == 1:
			print 'Pruning backward hubs'
		else:
			print 'Pruning forward hubs'
		bar = progressbar.ProgressBar()							
		for v in bar(I[reverse]):								# prune the hub of node v
			j = 0
			while j<N[reverse][v]:
				dist = 0
				w = Id_map[I[reverse][v][j]]					# j-th node in the hub
				if reverse == 0 and v!=w:						
					dist = hl_query(I[0][v],D[0][v],I[1][w],D[1][w])
				if reverse == 1 and v!=w:						
					dist = hl_query(I[0][w],D[0][w],I[1][v],D[1][v])
				if dist<D[reverse][v][j]:
					del I[reverse][v][j]
					del D[reverse][v][j]
					N[reverse][v]-=1
				else:
					j += 1
		gc.collect()

												 				
"""
Runs a query using hub labels
Receives forward, backward hub and starting points
Nf, Nb are integers
Df, Db are arrays of floats 
If, Ib are arrays of id's
"""
def hl_query(If,Df,Ib,Db):
	d = float("inf")	
	i = 0
	j = 0
	Nf = len(If)
	Nb = len(Ib)
	while i<Nf and j<Nb:
		if If[i]==Ib[j]:
			if Df[i]+Db[j] < d:
				d = Df[i]+Db[j]
			i += 1
			j += 1
		elif If[i]<Ib[j]:
			i += 1
		else:
			j += 1
	return d

"""
Receives hubs for pruned augmented graph, source, target and budget
Returns dist(s,t|b) and the surplus of budget 		
"""
def hl_query_pruned(I,D,s,t,b):
	if s == t:
		return 0,0
	if (t,0) not in I[1]:
		return float("inf")
	dist = float("inf")
	surplus = 0
	for x in range(b,-1,-1):
		if (s,x) not in I[0]:
			continue
		d = hl_query(I[0][(s,x)],D[0][(s,x)],I[1][(t,0)],D[1][(t,0)])
		if d<dist:
			dist = d
			surplus = b-x
	return dist,surplus

"""
Receives hubs for pruned augmented graph, source and target
Returns all the efficient distances to s
"""
def hl_query_frontier(I,D,s,t,B):
	if s == t:
		return [0]*(B+1)
	if (t,0) not in I[1]:
		return [float("inf")]*(B+1)	
	dist = [float("inf")]*(B+1)
	if (s,0) in I[0]:
		dist[0] = hl_query(I[0][(s,0)],D[0][(s,0)],I[1][(t,0)],D[1][(t,0)])
	for b in range(1,B+1):
		if (s,b) not in I[0]:
			dist[b] = dist[b-1]
			continue
		d = hl_query(I[0][(s,b)],D[0][(s,b)],I[1][(t,0)],D[1][(t,0)])
		if d<dist[b-1]:
			dist[b] = d
		else:
			dist[b] = dist[b-1]
	return dist		

"""
Receives hubs for pruned augmented graph with extra edges (v,b)->(v,b-1), source, target and budget
"""
def hl_query_extra_edges(I,D,s,t,b):	
	if s == t:
		return 0
	return hl_query(I[0][(s,b)],D[0][(s,b)],I[1][(t,0)],D[1][(t,0)])

"""
Receives hubs for pruned augmented graph with extra edges (v,b)->(v,b-1), source, target and budget
"""
def hl_query_extra_surplus(I,D,s,t,b):	#TODO:implement surplus of budget
	if s == t:
		return 0,0
	return hl_query(I[0][(s,b)],D[0][(s,b)],I[1][(t,0)],D[1][(t,0)]),0

"""
Save labels already constructed
"""
import pickle
def write_labels(I,D,N,Id_map,name):
	with open(name, "wb") as f:
		pickle.dump({'IDs':I, 'Dist':D, 'Size': N, 'Map': Id_map}, f)

"""
Read labels from file and return I,D,N,Id_map
"""
def read_labels(name):
	with open(name, "rb") as f:
		dic = pickle.load(f)
	return dic['IDs'], dic['Dist'], dic['Size'], dic['Map']

from numpy import std
from numpy import average as avg
def stats(N):
	return [max(N.values()),int(avg(N.values())),int(std(N.values()))]
	
"""
Receives hub labels, augmented graph and runs n_queries to measure times
technique can be "frontier", "full_prune" or "partial_prune"
Returns a list with the results
"""
from random import choice
def run_tests(n_queries,B,technique,I,D,GB,G,omit_dijkstra=False,omit_hl=False):
	test_nodes = []												# random (s,t,b) 
	dij_dist = []	
	hl_dist = []	
	times = []
	for k in xrange(0,n_queries):		
		test_nodes.append((choice(G.nodes()),choice(G.nodes()),choice(range(0,B+1))))

	query_hl = hl_query_extra_edges
	query_dijkstra = dijkstra_sink
	if technique == "frontier":
		test_nodes = [(s,t,B) for (s,t,b) in test_nodes]	
		query_hl = hl_query_frontier
		query_dijkstra = dijkstra_frontier

	if not omit_dijkstra:
		init_time = time.time()
		for k in xrange(0,n_queries):
			dij_dist.append(query_dijkstra(GB,test_nodes[k][0],test_nodes[k][1],test_nodes[k][2]))
		times.append((time.time() - init_time)*1000/n_queries)

	if not omit_hl:	
		init_time = time.time()
		for k in xrange(0,n_queries):
			hl_dist.append(query_hl(I,D,test_nodes[k][0],test_nodes[k][1],test_nodes[k][2]))
		times.append((time.time() - init_time)*1000/n_queries)
	
	if not (omit_dijkstra or omit_hl):
		for k in xrange(0,n_queries):
			if dij_dist[k] != hl_dist[k]:
				print 'Error {}: (s,t)={} -- HL:{} -- Dij:{}'.format(k,test_nodes[k],hl_dist[k],dij_dist[k])
	return times
