import sys
import os
sys.path.append(os.getcwd())

import hibi_dfr as hd
import networkx as nx

G = nx.DiGraph()
#G.add_edges_from([(1,2), (1, 3), (2,4), (3, 5), (4, 6), (5, 7), (3, 6), (2, 7) ])

G.add_edges_from([(1,2), (1,3), (2, 4), (2,5), (3,4), (3,5)])

t = hd.GraphsList(G, 2, 2)

#t.setAlphaList([(0, (2, 2)), (1, (1, 2)), (1, (3, 2)), (1, (5, 2)), (1, (7, 2)), (2, (2, 1)), (2, (7, 1)) ])

#t2 = hd.GraphsList(G2, 2, 3)
#t.checkDFR()

#for i in range(2**9 - 1):
#    t.addAlpha()
#
#t.display()
