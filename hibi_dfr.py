# use Python3, or else Pool screws up. 
# Checking whether a hibi ring is n-diagonally F-regular. 

# to use, build the hasse diagram of your poset, including - \infty. 
# make the arrows point from smaller nodes to bigger nodes. 

#e.g. 

#>>> import hibi_dfr as hd
#>>> import networkx as nx

#>>> G = nx.DiGraph()
#>>> G.add_edges_from([(1,2), (1, 3), (2, 4), (3, 4), (2, 5), (3, 5)])

# Then, simply run:
#>>> t = hd.GraphsList(G, 2, 3)
#
# First argument is the poset graph, second argument is the p^e you're using, and third argument is
# the tensor power. 




import math
import sys
import networkx as nx
import pdb
import time
from multiprocessing import Pool

def ceil( n ):
    return int(math.ceil(n))

def floor( n ):
    return int(n)

def computeDepth( graph, node, maxNodesList ):
    distsToMax = []

    for maxNode in maxNodesList:
        try:
            distsToMax.append(nx.shortest_path_length(graph, node, maxNode))
        except nx.exception.NetworkXNoPath:
            pass

    return min(distsToMax)

class GraphWithAED:
    _pToTheE = 2
    _nodesList = []
    _maxNodesList = []

    def __init__(self, graph, pToTheE):
        self._pToTheE = pToTheE
        # need to copy values!
        self._base_graph = graph#.copy()
        self._nodesList = list(graph.nodes())
        self._root_to_max_dist = nx.dag_longest_path_length(graph)

        for node in self._base_graph.nodes():
            self._base_graph.nodes[node]['alpha'] = 0
            self._base_graph.nodes[node]['delta'] = 0
            # if no descendants, add to maxNodesList
            if len( nx.descendants(self._base_graph, node)) == 0:
                self._maxNodesList.append(node)

        for node in self._base_graph.nodes():
            self._base_graph.nodes[node]['depth'] = computeDepth(self._base_graph, node, self._maxNodesList)

        for edge in self._base_graph.edges():
            self._base_graph.edges[edge]['epsilon'] = 0


    def updateEpsilons(self):
        for edge in self._base_graph.edges():
            ep = self._base_graph.nodes[edge[1]]['alpha'] >  self._base_graph.nodes[edge[0]]['alpha']
            self._base_graph.edges[edge]['epsilon'] = int(ep)

    def addAlphaHelper(self, nodeIndex):
        # return True if the whole graph overflowed
        # return False otherwise

        curNode = self._nodesList[nodeIndex]

        self._base_graph.nodes[curNode]['alpha'] += 1
        self._base_graph.nodes[curNode]['alpha'] %= self._pToTheE

        nodeIndex +=1 

        if self._base_graph.nodes[curNode]['alpha'] == 0:
            # so this one node overflowed...
            if nodeIndex >= len(self._nodesList):
                #if it was the final node, then the whole graph overflowed. 
                #We stop carrying over the addition and return false
                return True
            # if it was not the final node, then maybe we overflowed the whole graph, 
            # but maybe we did not! Let's ask the next node what it thinks. 
            return self.addAlphaHelper(nodeIndex)
        else:
            # if this node did not overflow, then definitely the whole graph did not. 
            return False
            

    def addAlpha(self):
        # return True and set everything to 0 if did overflow
        # return False if did not
        # x = nx.bfs_successors(self._base_graph, 1)
        flag =  self.addAlphaHelper(0)

        self.updateEpsilons()

        return flag

    def nextDeltaHelper(self, nodeIndex, Ngraph, numCopies):
        curNode = self._nodesList[nodeIndex]

        deltaMin = -self._base_graph.nodes[curNode]['depth']
        deltaMax = Ngraph.nodes[curNode]['value']  - (numCopies - 1) * deltaMin
        deltaLen = deltaMax - deltaMin

        assert(deltaLen >= 0)

        # equalsAsuccessor tells us if we're currently equal to the delta of some node 
        # above us (- epsilon)
        equalsAsuccessor = False
        for node in self._base_graph.successors(curNode): 
            succEpsilon = self._base_graph.edges[(curNode, node)]['epsilon']
            curDelta = self._base_graph.nodes[curNode]['delta']
            succDelta = self._base_graph.nodes[node]['delta'] 

            equalsAsuccessor = equalsAsuccessor or ( curDelta == succDelta - succEpsilon)

        # if we're already as small as a successor's delta - epsilon, then we gotta
        # reset this delta. Otherwise, we can decrease it by 1. 
        if self._base_graph.nodes[curNode]['delta'] == deltaMin or equalsAsuccessor:
            self._base_graph.nodes[curNode]['delta'] = deltaMax
        else:
            self._base_graph.nodes[curNode]['delta'] -= 1
        

        nodeIndex +=1 
        
        if self._base_graph.nodes[curNode]['delta'] == deltaMax:
            # so this one node overflowed...
            if nodeIndex >= len(self._nodesList):
                #if it was the final node, then the whole graph overflowed. 
                #We stop carrying over the addition and return false
                return True
            # if it was not the final node, then maybe we overflowed the whole graph, 
            # but maybe we did not! Let's ask the next node what it thinks. 
            return self.nextDeltaHelper(nodeIndex, Ngraph, numCopies)
        else:
            # if this node did not overflow, then definitely the whole graph did not. 
            return False

    
    def nextDelta(self, Ngraph, numCopies):
        #
        # return True and set everything to min if did overflow
        # return False if did not
        return self.nextDeltaHelper(0, Ngraph, numCopies)

    def initDeltas(self, Ngraph, numCopies):
        for node in self._base_graph.nodes():
            deltaMin = -self._base_graph.nodes[node]['depth']
            deltaMax = Ngraph.nodes[node]['value']  - (numCopies - 1) * deltaMin
            self._base_graph.nodes[node]['delta'] = deltaMax

    def initAlphas(self, startAt = 0):
        for node in self._base_graph.nodes():
            self._base_graph.nodes[node]['alpha'] = startAt

    def printNodes(self):
        for node in self._base_graph.nodes():
            print(self._base_graph.nodes[node])

    def setAlpha(self, alphaPair):
        self._base_graph.nodes[alphaPair[0]]['alpha'] = alphaPair[1]
        self.updateEpsilons()
        # we don't want to updateEpsilons each time we change an individual alpha, 
        # so this function shouldn't be used inside any loops or anything

    def setAlphaList(self, alphaPairList):
        for alphaPair in alphaPairList: 
            self.setAlpha(alphaPair)

class GraphsList:
    def __init__(self, graph, pToTheE, numCopies):
#        self._list = [GraphWithAED(graph, pToTheE)]*numCopies
        self._list = []
        for i in range(numCopies):
            # DO NOT DO [GraphWithAED()]*numCopies
            # BECAUSE THEN EVERYTHING IS THE SAME INSTANTIATION OF THE CLASS
            x = GraphWithAED(graph.copy(), pToTheE)
            self._list.append(x)

        self._NGraph = graph.copy()
        for node in self._NGraph.nodes():
            self._NGraph.nodes[node]['value'] = 0

        self._numCopies = numCopies
        self._pToTheE = pToTheE

    def alphasSumToInts(self):
        for node in self._NGraph.nodes():
            sumSoFar = 0
            for graph in self._list:
                sumSoFar += graph._base_graph.nodes[node]['alpha']
            if sumSoFar % self._pToTheE != 0:
                return False
        return True

    def alphaSumCongruences(self):
        # Return True if the alphas sum  to the correct thing mod q, 
        # which means we care about this choice of alphas
        for node in self._NGraph.nodes():
            sumSoFar = 0
            for graph in self._list:
                sumSoFar += graph._base_graph.nodes[node]['alpha']
            if sumSoFar % self._pToTheE != graph._base_graph.nodes[node]['depth'] % self._pToTheE:
                return False
        return True


    def updateN(self):
        for node in self._NGraph.nodes():
            self._NGraph.nodes[node]['value'] = 0
            for graph in self._list:
                self._NGraph.nodes[node]['value'] += int(graph._base_graph.nodes[node]['alpha'])
            self._NGraph.nodes[node]['value'] = floor( self._NGraph.nodes[node]['value'] / self._pToTheE ) 
            #self._NGraph.nodes[node]['value'] /=  int(self._pToTheE)

    def addAlpha(self, update = True):
        # add alpha to grpah 1
        # if overflow, move on. 
        # if the last one overflowed, return false
        # if not, return true

        listIndex = 0
        lastOverFlowed = True

        # as long as the last table overflowed, and we haven't run out of tables...
        while(listIndex < self._numCopies and lastOverFlowed):
            # add alpha to current table and check if that table overflowed
            lastOverFlowed = self._list[listIndex].addAlpha()
            # on to the next table!
            listIndex += 1

        # update N
        if update:
            self.updateN()
        
        # if we've exited the loop, either we got through all the copies, 
        # or the last one did not overflow yet
        # if it did not overflow yet, we want to keep iterating. so return true. 
        # if the last one DID overflow, then we've gotten through all the copies! and also the last copy
        # overflowed! So we want to stop iterating and return false. 
        return not lastOverFlowed

    # I shouldn't be copying code, but......
    def nextDelta(self):
        # add delta to graph 1
        # if overflow, move on. 
        # if the last one overflowed, return false
        # if not, return true
        listIndex = 0
        lastOverFlowed = True
        while(listIndex < self._numCopies and lastOverFlowed):
            lastOverFlowed = self._list[listIndex].nextDelta(self._NGraph, self._numCopies)
            listIndex += 1

        
        # if we've exited the loop, either we got through all the copies, 
        # or the last one did not overflow yet
        # if it did not overflow yet, we want to keep iterating. so return true. 
        # if the last one DID overflow, then we've gotten through all the copies! and also the last copy
        # overflowed! So we want to stop iterating and return false. 
        return not lastOverFlowed

    def checkDeltas(self):
        # return true if these choices work, false otherwise. 

        # first check the equality on the Ns
        for node in self._NGraph.nodes():
            deltasum = 0
            for graph in self._list:
                deltasum += graph._base_graph.nodes[node]['delta']

            if deltasum != self._NGraph.nodes[node]['value']:
                return False

        # next check the inequality on the epsilons
        for edge in self._NGraph.edges():
            # edge[0] is the smaller node, edge[1] is the larger node. 
            # want to check that smaller node is \geq larger  node - epsilon
            for graph in self._list:
                #
                if graph._base_graph.nodes[edge[0]]['delta'] < graph._base_graph.nodes[edge[1]]['delta'] - graph._base_graph.edges[edge]['epsilon']:
                    return False

        return True

    def checkAllDeltas(self, display=False):
        # put some optimizations here, e.g. check if Ns graph has smaller epsilons 
        # than some alphas graph..
        # for graph in graphs:
        #     if Ngraph < graph:
        #         return true
        # if epsilons are ones you can get from a graph with comparable top nodes ...
        deltaWorked = False
        self.initDeltas()
        deltaWorked = self.checkDeltas()

        while(not deltaWorked and self.nextDelta()):
            deltaWorked = self.checkDeltas()

        if display:
            self.display()

        return deltaWorked


    def display(self):
        ctr = 0
        for graph in self._list:
            print("Printing graph number ", ctr)
            graph.printNodes()
            ctr += 1

    def initDeltas(self):
        for graph in self._list:
            graph.initDeltas(self._NGraph, self._numCopies)

    def initAlphas(self):
        for graph in self._list:
            graph.initAlphas()

    def checkDFR(self, preAdd = 0):
        totalAlphas = float(self._pToTheE)**( len(self._list[0]._nodesList) * self._numCopies) - preAdd
        startTime = time.time()
        curTime = time.time()
        print("Checking if ", self._numCopies,"-DFR")
        print("q = ", self._pToTheE)
        print("Number of alphas to check: ",  totalAlphas)
        print("Progress: ")
        sys.stdout.write("0%")

        if nx.is_arborescence(self._list[0]._base_graph):
            print("No Top Nodes")
            return True
        alphasCount = 0

        for i in range(preAdd):
            self.addAlpha(False)
        self.updateN()

        while(self.addAlpha()):
            # Let's print our current progress:
            alphasCount += 1
            curTime = time.time()
            sys.stdout.write("\r")
            sys.stdout.flush()
            sys.stdout.write("AlphaCount: " + str(alphasCount).zfill(5) + " (" + str( round( alphasCount*100/totalAlphas, 2 ) ) + "%)" )
            curTime = time.time()
            elapsedTime = round(curTime -startTime, 1)
            sys.stdout.write(", ElapsedTime: " + str(elapsedTime))
            aveTimePerAlpha = round(elapsedTime/alphasCount, 3)
            sys.stdout.write(", AveTimePerAlpha: " + str(aveTimePerAlpha))
            remainingTime = floor(aveTimePerAlpha*(totalAlphas -alphasCount ) ) 
            sys.stdout.write(", TimeRemaining(est): " + str(remainingTime).zfill(6) + "  ")

            #sys.stdout.write(str( alphasCount*100/totalAlphas ) + "%" )

            if not self.alphaSumCongruences():
                continue

            #if you checked all the deltas and none of them worked, return False
            if not self.checkAllDeltas():
                print("\nFound some alphas that did not work: \n")
                self.display()
                print("Total time: ", floor(time.time() - startTime))
                return False

        #if you've gone through all the alphas, then it's DFR
        print("\nChecked all the alphas. Found no counterexamples. ")
        print("Total time: ", floor(time.time() - startTime))
        return True

    def setAlpha(self, alphaTriple):
        # (which tensor product, (which alpha, what value))
        self._list[alphaTriple[0]].setAlpha(alphaTriple[1])
        self.updateN()
        # this is inefficient if you're going to use setAlpha a bunch of times in a row
        # luckily, updating N is not very resource-intensive

    def setAlphaList(self, alphaTripleList):
        self.initAlphas()
        for alphaTriple in alphaTripleList: 
            self.setAlpha(alphaTriple)
