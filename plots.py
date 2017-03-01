import matplotlib.pyplot as plt, networkx as nx, math 
"""
Simple plot of a graph
Assumes that nodes have coordinates as an attribute 'XY'	
"""
def plot(G,name=None,node_size=0.3):
	pos = nx.get_node_attributes(G,'XY')	#get dictionary of positions
	nx.draw(G, pos, node_size=node_size,with_labels=False,linewidths=0.1,arrows=False,width=0.1) 
	if name!=None:
		pylab.savefig('{}.pdf'.format(name))
	plt.show() 

""""
Colours edges depending on an attribute
Attribute takes values: value1, value2, value3(optional)
The colors are: green, blue, red
Example: plot_edge_attributes(G,'shortcut',0,1). If shortcut=0, the edge is plotted green
"""
def plot_edge_attributes(G,attribute,value1,value2,value3=None):
	#Create dictionary of positions
	points = []
	colors = []
	widths = []
	for (u,v) in G.edges():
		if G[u][v][attribute] == value1:
			colors.append('g')
			widths.append(3)
		elif G[u][v][attribute] == value2:
			colors.append('b')
			widths.append(1)
		elif G[u][v][attribute] == value3:
			colors.append('r')
		else:
			colors.append('k')
	for n in xrange(G.number_of_nodes()):
		points.append(G.node[n]['XY'])
	pos = dict(zip(range(len(points)), points)) 
	nx.draw(G, pos,edges=G.edges(),edge_color=colors,width=widths) 
	plt.show() 

""""
Draws a graph and colours nodes according to a numerical attribute
sizes is a dictionary indexed by node
If name!=None, saves the figure as a pdf
If a list of big_nodes is specified, they will be drawn bigger
"""
import matplotlib as mpl
import pylab
def plot_node_attributes(G,sizes,name=None,big_nodes=None):
	colors = []
	node_size = []
	small_nodes = []
	vmin = min(sizes.values())
	vmax = max(sizes.values())
	for u in G.nodes():
		colors.append(sizes[u])
		if big_nodes!=None and u in big_nodes:
			node_size.append(30)
		else:
			node_size.append(10)
	cmap=plt.cm.Reds
	pos = nx.get_node_attributes(G,'XY')
	nx.draw(G, pos,node_size=node_size,node_color=colors,cmap=cmap,vmin=vmin,vmax=vmax,with_labels=False,linewidths=0.1,arrows=False,width=0.1) 
	sm = plt.cm.ScalarMappable(cmap=cmap, norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax))
	sm._A = []
	plt.colorbar(sm)
	if name!=None:
		pylab.savefig('{}.pdf'.format(name),bbox_inches='tight')
	plt.show()
	
"""
Plot histogram of list or dictionary
n_bins is the number of bins to construct the histogram
xticks and yticks are the number of ticks for each axis
"""
import numpy as np
def plot_hist(data,n_bins=30,title="",xlabel="",ylabel="",name=None,xticks=4,yticks=4):
	if isinstance(data,dict):
		data = data.values()
	plt.hist(data,n_bins,alpha=0.5)
	plt.title(title)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	axes = plt.gca()
	plt.yticks(np.ceil(np.linspace(axes.get_ylim()[0],axes.get_ylim()[1], num=yticks+1)[1:]))
	plt.xticks(np.linspace(axes.get_xlim()[0],axes.get_xlim()[1], num=xticks))
	plt.rcParams["font.family"] = "serif"
	plt.rcParams.update({'font.size': 30})
	if name!=None:
		pylab.savefig('{}.pdf'.format(name),bbox_inches='tight')
	plt.show()
