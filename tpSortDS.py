from collections import deque
import pdb

class Node:
    def __init__(self, key, value, depList):
        self.key = key
        self.value = value
        self.depList = depList
    def __str__(self):
        return 'Node: {}'.format(self.key)
    def __repr__(self):
        return self.__str__()

class TpSortDS:
    """
    This is a generic data structure which store a graph in the internal
    directory 'graph'
    graph is indexed by key. Each key has a tuple of (value, depList)
    value is any data passed by caller, and depList is a list 
    to other nodes in the graph

    It gives routines to do a topological sort on the either graph or
    a single node and its deps.
    """
    graph = {}

    def addNode(self, key, value):
        """
        Add a new node to the graph
        """
        if key in self.graph:
            print(name, 'already exists in the graph')
            raise ValueError
        self.graph[key] = Node(key, value, []) #(value, depList)

    def addDep(self, key, depList):
        if type(depList) is not list:
            print('depList passed is not a valid List')
            raise TypeError
        if key not in self.graph:
            print(key, 'not found in graph')
            raise ValueError

        for dep in depList:
            if dep not in self.graph:
                print(dep, 'not found in graph')
                raise ValueError
            self.graph[key].depList.extend([self.graph[key] for key in depList])

    def getSorted(self, start=None):
        """
        If a start is given only a topological sort on that node 
        and its dependents is done. If it is None, then all nodes are 
        processed
        """
        PROCESSING, DONE = 0, 1
        if start is None:
            toProcess = set(self.graph.values())
        else:
            toProcess = set([self.graph[key] for key in start])
        order, state = deque(), {}

        def dfs(node):
            state[node] = PROCESSING
            for dep in self.graph[node.key].depList:
                if dep not in state: #seen for the first time
                    toProcess.discard(dep)
                    dfs(dep)
                else:  #Already seen
                    if state[dep] == PROCESSING: raise ValueError('Cyclic')
                    if state[dep] == DONE: continue
            order.append(node.value)
            state[node] = DONE

        while toProcess: dfs(toProcess.pop())
        return order

    def getDep(self, key):
        """
        Return a list of dependencies
        """
        return [dep.key for dep in self.graph[key].depList]
