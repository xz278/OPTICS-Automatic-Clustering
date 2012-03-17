'''
Automatic Clustering of Hierarchical Clustering Representations
 
Library Dependencies: numpy, if graphing is desired - matplotlib
OPTICS implementation used has dependencies include numpy, scipy, and hcluster

An implementation of the following algorithm, with some minor add-ons:
J. Sander, X. Qin, Z. Lu, N. Niu, A. Kovarsky, K. Whang, J. Jeon, K. Shim, J. Srivastava, Automatic extraction of clusters from hierarchical clustering representations. Advances in Knowledge Discovery and Data Mining (2003) Springer Berlin / Heidelberg. 567-567
available from http://dx.doi.org/10.1007/3-540-36175-8_8

Implemented in Python by Amy X. Zhang, Cambridge Computer Laboratory.
March 2012
amy.xian.zhang@gmail.com
amyxzhang.wordpress.com
'''


import numpy as NP
import matplotlib.pyplot as plt
from operator import itemgetter
import sys


def isLocalMaxima(index,RPlot,RPoints,nghsize):
    # 0 = point at index is not local maxima
    # 1 = point at index is local maxima
    
    for i in range(1,nghsize+1):
        #process objects to the right of index 
        if index + i < len(RPlot):
            if (RPlot[index] < RPlot[index+i]):
                return 0
            
        #process objects to the left of index 
        if index - i >= 0:
            if (RPlot[index] < RPlot[index-i]):
                return 0
    
    return 1

def findLocalMaxima(RPlot, RPoints, nghsize):
    
    localMaximaPoints = {}
    
    #1st and last points on Reachability Plot are not taken as local maxima points
    for i in range(1,len(RPoints)-1):
        #if the point is a local maxima on the reachability plot with 
        #regard to nghsize, insert it into priority queue and maxima list
        if RPlot[i] > RPlot[i-1] and RPlot[i] >= RPlot[i+1] and isLocalMaxima(i,RPlot,RPoints,nghsize) == 1:
            localMaximaPoints[i] = RPlot[i]
    
    return sorted(localMaximaPoints, key=localMaximaPoints.__getitem__ , reverse=True)
    


def clusterTree(node, parentNode, localMaximaPoints, RPlot, RPoints, min_cluster_size):
    #node is a node or the root of the tree in the first call
    #parentNode is parent node of N or None if node is root of the tree
    #localMaximaPoints is list of local maxima points sorted in descending order of reachability
    if len(localMaximaPoints) == 0:
        return #parentNode is a leaf
    
    #take largest local maximum as possible separation between clusters
    s = localMaximaPoints[0]
    node.assignSplitPoint(s)
    localMaximaPoints = localMaximaPoints[1:]

    #create two new nodes and add to list of nodes
    Node1 = TreeNode(RPoints[node.start:s],node.start,s, node)
    Node2 = TreeNode(RPoints[s+1:node.end],s+1, node.end, node)
    LocalMax1 = []
    LocalMax2 = []

    for i in localMaximaPoints:
        if i < s:
            LocalMax1.append(i)
        if i > s:
            LocalMax2.append(i)
    
    Nodelist = []
    Nodelist.append((Node1,LocalMax1))
    Nodelist.append((Node2,LocalMax2))
    
    #set a lower threshold on how small a significant maxima can be
    significantMin = .003

    if RPlot[s] < significantMin:
        node.assignSplitPoint(-1)
        #if splitpoint is not significant, ignore this split and continue
        clusterTree(node,parentNode, localMaximaPoints, RPlot, RPoints, min_cluster_size)
        return
        
        
	#only check a certain ratio of points in the child nodes formed to the left and right of the maxima
    checkRatio = .65
    checkValue1 = int(NP.round(checkRatio*len(Node1.points)))
    checkValue2 = int(NP.round(checkRatio*len(Node2.points)))
    if checkValue2 == 0:
        checkValue2 = 1
    avgReachValue1 = float(NP.average(RPlot[(Node1.end - checkValue1):Node1.end]))
    avgReachValue2 = float(NP.average(RPlot[Node2.start:(Node2.start + checkValue2)]))

	#the maximum ratio we allow of average height of clusters on the right and left to the local maxima in question
    maximaRatio = .95
	
	#if ratio above exceeds maximaRatio, find which of the clusters to the left and right to reject based on rejectionRatio
    rejectionRatio = .8
	
    if float(avgReachValue1 / float(RPlot[s])) > maximaRatio or float(avgReachValue2 / float(RPlot[s])) > maximaRatio:

        if float(avgReachValue1 / float(RPlot[s])) < rejectionRatio:
          #reject node 2
            Nodelist.remove((Node2, LocalMax2))
        if float(avgReachValue2 / float(RPlot[s])) < rejectionRatio:
          #reject node 1
            Nodelist.remove((Node1, LocalMax1))
        if float(avgReachValue1 / float(RPlot[s])) >= rejectionRatio and float(avgReachValue2 / float(RPlot[s])) >= rejectionRatio:
            node.assignSplitPoint(-1)
            #since splitpoint is not significant, ignore this split and continue (reject both child nodes)
            clusterTree(node,parentNode, localMaximaPoints, RPlot, RPoints, min_cluster_size)
            return
 
    #remove clusters that are too small
    if len(Node1.points) < min_cluster_size:
        #cluster 1 is too small"
        try:
            Nodelist.remove((Node1, LocalMax1))
        except Exception:
            sys.exc_clear()
    if len(Node2.points) < min_cluster_size:
        #cluster 2 is too small
        try:
            Nodelist.remove((Node2, LocalMax2))
        except Exception:
            sys.exc_clear()
    if len(Nodelist) == 0:
        #parentNode will be a leaf
        node.assignSplitPoint(-1)
        return
    
    #check if nodes can be moved up one level - the new cluster created is too similar to its parent
    similaritythreshold = 0.75
    bypassNode = 0
    if parentNode != None:
        sumRP = NP.average(RPlot[node.start:node.end])
        sumParent = NP.average(RPlot[parentNode.start:parentNode.end])
        if float(float(sumRP) / float(sumParent)) > similaritythreshold:
            if float(float(len(node.points)) / float(len(parentNode.points)) ) >= .5:
                parentNode.children.remove(node)
                bypassNode = 1
        else:
            if float(float(len(node.points)) / float(len(parentNode.points)) ) > .9:
                bypassNode = 1
        
    for nl in Nodelist:
        if bypassNode == 1:
            parentNode.addChild(nl[0])
            clusterTree(nl[0], parentNode, nl[1], RPlot, RPoints, min_cluster_size)
        else:
            node.addChild(nl[0])
            clusterTree(nl[0], node, nl[1], RPlot, RPoints, min_cluster_size)
        

def printTree(node, num):
    if node is not None:
        print "Level %d" % num
        print str(node)
        for n in node.children:
            printTree(n, num+1)

def writeTree(fileW, locationMap, RPoints, node, num):
    if node is not None:
        fileW.write("Level " + str(num) + "\n")
        fileW.write(str(node) + "\n")
        for x in range(node.start,node.end):
            item = RPoints[x]
            lon = item[0]
            lat = item[1]
            placeName = locationMap[(lon,lat)]
            s = str(x) + ',' + placeName + ', ' + str(lat) + ', ' + str(lon) + '\n'
            fileW.write(s)
        fileW.write("\n")
        for n in node.children:
            writeTree(fileW, locationMap, RPoints, n, num+1)


def getArray(node,num, arr):
    if node is not None:
        if len(arr) <= num:
            arr.append([])
        try:
            arr[num].append(node)
        except:
            arr[num] = []
            arr[num].append(node)
        for n in node.children:
            getArray(n,num+1,arr)
        return arr
    else:
        return arr


def getLeaves(node, arr):
    if node is not None:
        if node.splitpoint == -1:
            arr.append(node)
        for n in node.children:
            getLeaves(n,arr)
    return arr


def graphTree(root, RPlot):

    fig = plt.figure()
    ax = fig.add_subplot(111)

    a1 = [i for i in range(len(RPlot))]
    ax.vlines(a1, 0, RPlot)
    
    num = .015
    graphNode(root, num, ax)

    plt.savefig('RPlot.png', dpi=None, facecolor='w', edgecolor='w',
      orientation='portrait', papertype=None, format=None,
     transparent=False, bbox_inches=None, pad_inches=0.1)
    plt.show()

            
def graphNode(node, num, ax):
    ax.hlines(num,node.start,node.end,color="red")
    for item in node.children:
        graphNode(item, num - .001, ax)

def automaticCluster(RPlot, RPoints):

	min_cluster_size_ratio = .005
    min_neighborhood_size = 2
	min_maxima_ratio = 0.001

    #remove large values on the reachability plot at the ends
    #ends = 10% on right
    endValue = int(.1 * len(RPlot))
    totalavg = NP.average(RPlot)
    totalSD = NP.std(RPlot)
    boundaryend = len(RPlot) - 1
    for i in range(endValue):
        value = RPlot[len(RPlot)-i-1]
        if value > totalavg + (totalSD*.5):
            boundaryend = len(RPlot) - i
        else:
            break

    RPlot = RPlot[:boundaryend+1]
    RPoints = RPoints[:boundaryend+1]
    
    min_cluster_size = int(min_cluster_size_ratio * len(RPoints))

    if min_cluster_size < 5:
        min_cluster_size = 5
    
    
    nghsize = int(min_maxima_ratio*len(RPoints))

    if nghsize < min_neighborhood_size:
        nghsize = min_neighborhood_size
    
    localMaximaPoints = findLocalMaxima(RPlot, RPoints, nghsize)
    
    rootNode = TreeNode(RPoints, 0, len(RPoints), None)
    clusterTree(rootNode, None, localMaximaPoints, RPlot, RPoints, min_cluster_size)


    return rootNode, RPlot
    

class TreeNode(object):
    def __init__(self, points, start, end, parentNode):
        self.points = points
        self.start = start
        self.end = end
        self.parentNode = parentNode
        self.children = []
        self.splitpoint = -1

    def __str__(self):
        return "start: %d, end %d, split: %d" % (self.start, self.end, self.splitpoint)

        
    def assignSplitPoint(self,splitpoint):
        self.splitpoint = splitpoint

    def addChild(self, child):
        self.children.append(child)