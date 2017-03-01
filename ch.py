import math, networkx as nx
from graph_info import *
import time, progressbar,gc

"""
Uses shortest path covers to contract
Adds nodes greedily to a cover C and then contract in reverse order
If rank=True, then returns the cover when the rank is computed and skips the contraction
If sample is a list of nodes, then computes the cover with nodes from that list only
"""
from collections import defaultdict
def contract_spc(G,rank=False,sample=None):
	nx.set_edge_attributes(G, 'shortcut', 0)		# original edges are not shortcuts
	C = []											# list of nodes in the cover
	n = G.number_of_nodes()
	H = nx.nodes(G)									# list of nodes not included in C
	if sample != None:
		skip = list(set(H)-set(sample))		
	else:
		skip = []
	P = {}											# P[v] is a dict of parents in three rooted at v
	L = {}											# nodes at each level
	Ch = {}											# Ch[v] is a dict of children in the three
	Paths = {}										# Paths[v] dict of paths in the tree
	print 'Computing paths for cover'
	bar = progressbar.ProgressBar()
	for v in bar(H):								# compute all shortest paths
		if v in skip:
			P[v],Paths[v],Ch[v],L[v] = {v:v},{v:[v]},{},{0:v}
		else:
			P[v],Paths[v],Ch[v],L[v] = dijkstra_levels(G,v,0)
	
	print 'Computing SPC'	
	last = None										# last node added to C			
	bar = progressbar.ProgressBar()						
	for i in bar(xrange(n,1,-1)):					
		total_hits = dict.fromkeys(H,0)
		for v in H:									# process paths starting at v
			# remove children of last node added to C
			if last in P[v]:						
				p_last = P[v][last]
				Ch[v][p_last].remove(last)			# delete last node from its parent's list of children
				remove_children_of(last,Ch[v],P[v])

			# count the hits and remove descendants of last
			h = defaultdict(int)					# hits of each node in this tree
			h[v] = 1					
			for l in xrange(len(L[v])-1,0,-1):		# traverse tree bottom-up
				j = 0
				len_L = len(L[v][l])
				while j<len_L:						# nodes in level l
					u = L[v][l][j]
					if u not in P[v]:
						L[v][l].remove(u)			# u is descendant of last, remove it
						len_L -= 1
						continue
					pu = P[v][u]					# parent of u		
					h[u] +=  1						# count the (v,u)-path
					h[pu] = h[pu] + h[u]
					j += 1
			for u in h.keys():
				total_hits[u] = total_hits[u]+h[u]
		
		last = max(total_hits, key = total_hits.get)
		G.node[last]['rank'] = i		
		C.append(last)	
		H.remove(last);	Ch.pop(last, None); L.pop(last, None); P.pop(last, None)
			
	#When the loop ends there is just one node remaining in H
	v = H[0]
	G.node[v]['rank'] = 1
	C.append(v)
	C.reverse()
	P,Paths,Ch,L = None,None,None,None
	gc.collect()
	if rank:
		return C
	
	#Now we contract 
	print 'Contracting'
	H = G.copy()
	bar = progressbar.ProgressBar()
	for i in bar(xrange(0,n)):					
		shortcut(H,C[i] ,G)
	return C

"""
Uses a rank specified by a permutation C of the original nodes to contract an augmented graph
"""
def contract_augmented(G,C,B):
	nx.set_edge_attributes(G, 'shortcut', 0)		# original edges are not shortcuts
	nx.set_node_attributes(G, 'rank', 0)			# rank of sink nodes
	nn = len(C)										# number of original nodes
	H = G.copy()
	rank = 1
	bar = progressbar.ProgressBar()
	
	print 'Contracting augmented graph'
	for i in bar(xrange(0,nn)):
		for b in xrange(B,-1,-1):				
			v = (C[i],b)							# v is to be contracted
			if not G.has_node(v):					# when the augmented graph is pruned some nodes disappear 
				continue
			G.node[v]['rank'] = rank
			rank += 1
			shortcut(H,v,G)

"""
Shortcuts node v from graph H
Graph G is the original
"""
from networkx import single_source_dijkstra as dijkstra
def shortcut(H,v,G):
	sucs = H.successors(v)					# successors of v
	if not sucs:							# v has no successors
		H.remove_node(v)
		return
	pred = H.predecessors(v)				# predecessors of v
	if not pred:							# v has no predecessors
		H.remove_node(v)
		return
			
	#Look in H for cutoff
	max_vw = 0								# max dist(v,w)
	for w in H[v]:							# search in successors of v
		if H[v][w]['dist'] > max_vw:
			max_vw = H[v][w]['dist']
	H.remove_node(v)
	for u in pred:
		Lengths,_ = dijkstra(H,u,target=None,cutoff=G[u][v]['dist']+max_vw, weight='dist')
		for w in sucs:
			if u == w or (w in Lengths and Lengths[w]<=G[u][v]['dist']+G[v][w]['dist']):
				continue
			H.add_edge(u,w,dist=G[u][v]['dist']+G[v][w]['dist'])
			G.add_edge(u,w,shortcut=1,dist=G[u][v]['dist']+G[v][w]['dist'])


"""
Runs a CH search, visiting all nodes with higher rank
rank is a dictionary indexed by nodes
The output is a pair (D,P) where D[v] is the distance from start to v and P[v] is the predecessor of v along the shortest path from s to v.
"""
from heapq import heappush, heappop
from itertools import count

def ch_search(G, source, reverse, rank):
	push = heappush
	pop = heappop
	D = {}  								# dictionary of final distances
	parent = {source: source}  				# dictionary of parents
	seen = {source: 0}
	c = count()
	fringe = []  							# use heapq with (distance,label) tuples
	push(fringe, (0, next(c), source))
	if reverse == 0:
		dist = dist_forward
		neighbours = G.successors
	else:
		dist = dist_backward
		neighbours = G.predecessors

	while fringe:
		(d, _, v) = pop(fringe)				# min distance and node
		if v in D:
			continue  						# already searched this node.
		D[v] = d							# settle distance
		N = neighbours(v)
		for w in N:
			if rank[w]<rank[v]:
				continue	
			vw_dist = D[v] + dist(G,v,w)
			if w not in seen or vw_dist < seen[w]:
				seen[w] = vw_dist
				push(fringe, (vw_dist, next(c), w))
				parent[w] = v
	return (D, parent)

"""
Runs Dijkstra from the source
Returns list of parents, paths, children and the level of each node (#hops away from source)
"""
def dijkstra_levels(G, source, reverse):
	push = heappush
	pop = heappop
	D = {}  								# dictionary of final distances
	p = {source: source} 	 				# dictionary of parents
	seen = {source: 0}
	h = {source: 0}							# v is h[v] hops away from the source
	levels = {}								# nodes at each level 0,1,2,...
	paths = {source: [source]}  
	c = count()
	fringe = []  							# use heapq with (distance,label) tuples
	push(fringe, (0, next(c), source))

	if reverse == 0:
		dist = dist_forward
		neighbours = G.successors
	else:
		dist = dist_backward
		neighbours = G.predecessors
	while fringe:
		(d, _, v) = pop(fringe)				# min distance and node
		if v in D:
			continue  						# already searched this node.
		D[v] = d
		hv = h[v]							# settle the level of v
		if hv in levels:
			levels[hv].append(v)
		else:
			levels[hv] = [v] 		

		N = neighbours(v)
		for w in N:	
			vw_dist = D[v] + dist(G,v,w)
			if w not in seen or vw_dist < seen[w]:
				seen[w] = vw_dist
				push(fringe, (vw_dist, next(c), w))
				p[w] = v
				paths[w] = paths[v] + [w]
				h[w] = hv + 1
	
	child = {}
	for l in xrange(1,len(levels)):			# traverse tree top-bottom to determine children
		for u in levels[l]:
			pu = p[u]
			if pu in child:					# if the node already has children
				child[pu].append(u)
			else:
				child[pu] = [u]

	return (p,paths,child,levels)

"""
Remove all children of u in the tree
"""
def remove_children_of(u,Ch,P):
	if u in P:
		P.pop(u,None)
	if 	u not in Ch:			# u has no children
		return

	for v in Ch[u]:
		remove_children_of(v,Ch,P)
	Ch.pop(u,None)
