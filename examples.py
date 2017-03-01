#!/usr/bin/python
import networkx as nx
from hub_labels import *; from costs import *; from graph_info import *
from plots import *; from ch import *;
from numpy import average, std
import os

if __name__ == '__main__':
	print 'Obtain labels for the regular graph'
	#Load a file named "Data 100". The file is in the same folder
	G= nx.read_gpickle("Data100")
	#Contract using a shortest path cover
	C = contract_spc(G,rank=False,sample=None)
	#Generate an Id_map and create labels
	Id_map = {k: v for v, k in nx.get_node_attributes(G,'ID').iteritems()}
	I,D,N = create_labels(G,Id_map)
	#Write the labels to a file
	write_labels(I,D,N,Id_map,"Labels_Data100")
	#Run a query from node 98 to node 10 with the labels
	print hl_query(I[0][98],D[0][98],I[1][10],D[1][10])
	
	print 'Obtain labels for the augmented graph'
	#Put unit cost in 150 random edges
	randcost(G,150)
	#Create a pruned augmented graph with maximum budget of 5
	B=5
	G_pruned = prune_augmented(G,B,extra_edges=True)
	#Get a sample of 30 nodes
	sample = cluster(G,30)
	#Use the sample to get a rank, but don't contract
	C = contract_spc(G,rank=True,sample=sample)
	#Use the cover to contract the augmented graph
	contract_augmented(G_pruned,C,B)
	#Specify sources and targets in the augmented graph	
	sources = list(itertools.product(G.nodes(),range(0,B+1)))	# nodes (s,b) 
	targets = [(u,0) for u in G.nodes()]						# nodes (t,0)	
	#Generate an Id_map and create labels
	Id_map = {k: v for v, k in nx.get_node_attributes(G_pruned,'ID').iteritems()}
	I,D,N = create_labels(G_pruned,Id_map,sources=sources,targets=targets)
	#Prune the labels
	prune_labels_bootstrap(I,D,N,Id_map,G_pruned,omit_forward=False,extra_edges=True)
	#Run a query from node 98 to node 10 with budget 1
	print hl_query_extra_edges(I,D,98,10,2)
