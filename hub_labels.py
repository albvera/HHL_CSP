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
		query = hl_query_extra_edges 
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
				dist = 0
				w = Id_map[I[reverse][v][j]]					# j-th node in the hub
				if reverse == 0 and v!=w:						# if (w,x) not a sink-node, compute SP (v,b-x)->(w,0)
					dist = query(I,D,v[0],w[0],v[1]-w[1])
				if reverse == 1 and v!=w:						# dist wv and (v,b) is a sink node
					dist = query(I,D,w[0],v[0],w[1])
				if dist<D[reverse][v][j]:
					del I[reverse][v][j]
					del D[reverse][v][j]
					N[reverse][v]-=1
				else:
					j+=1
		gc.collect()	

"""
G is the augmented graph without sink nodes
"""
def prune_forward_labels(I,D,N,Id_map,G,nodes,B):		
	print 'Pruning forward hubs'
	bar = progressbar.ProgressBar()
	dijkstra = nx.single_source_dijkstra
	
	for s in bar(nodes):
		lengths,paths=dijkstra(G,(s,B),weight='dist')	
		visit = {}												# visit[b] = nodes visited from (s,b) in an efficient path
		dist = {}												# dist[t][b] = dist(s,t|b)
		for b in xrange(0,B+1):
			visit[b] = Set()		
		
		#Compute all efficient paths from s
		for t in nodes:
			if t==s:
				continue
			dist[t] = [float("inf")]*(B+1)						# dist[b] = distance with budget b
			for x in xrange(B,-1,-1):
				if (t,x) not in lengths:
					if x<B:
						dist[t][B-x] = dist[t][B-x-1]
					continue		
				if x==B or lengths[(t,x)]<dist[t][B-x-1]:		# path is strictly better than the previous
					visit[B-x].update([(u,y-x) for (u,y) in paths[(t,x)]])
					dist[t][B-x] = lengths[(t,x)]
				else:
					dist[t][B-x] = dist[t][B-x-1]

		#Remove nodes not visited in an efficient path	
		for b in xrange(B,-1,-1):
			for x in xrange (b-1,-1,-1):						# add all the nodes visited with smaller budget
				visit[b].update(visit[x])		
			j = 0
			v = (s,b)
			while j<N[0][v]:
				(w,z) = Id_map[I[0][v][j]]						# j-th node in the hub
				if s==w or ((w,z) in visit[b] and D[0][v][j]<=dist[w][b-z]):
					j+=1
				else:
					del I[0][v][j]
					del D[0][v][j]
					N[0][v]-=1
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
"""
def hl_query_pruned(I,D,s,t,b):
	if s == t:
		return 0
	if (t,0) not in I[1]:
		return float("inf")
	dist = float("inf")
	for x in range(b,-1,-1):
		if (s,x) not in I[0]:
			continue
		d = hl_query(I[0][(s,x)],D[0][(s,x)],I[1][(t,0)],D[1][(t,0)])
		if d<dist:
			dist = d
	return dist	

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
