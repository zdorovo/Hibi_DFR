import sys
import os
sys.path.append(os.getcwd())

import hibi_dfr as hd
import networkx as nx

G = nx.DiGraph()
G.add_edges_from([(1,2), (1, 3), (1, 4), (2, 5), (2, 6), (3, 5), (3, 6),  (4, 5), (3, 6)])
#G.add_edge(1,2)

t = hd.GraphsList(G, 3, 3)
#t.checkDFR(14340000)

#for i in range(2**9 - 1):
#    t.addAlpha()
#
#t.display()
