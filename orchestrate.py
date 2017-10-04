#!/usr/bin/python3

######################################################################
# File:   orchestrator.py
# Author: Nusli Vakil (nusliv)
# 
# Description: This code creates a dependency graph based on the 
# policy.conf file. The details on how to write the file are provided
# in the comments in the file.
# Based on the rules in the file it can either run all the routines,
# or a single routine can be triggered along with its dependents.
######################################################################


from abc import ABCMeta
from abc import abstractmethod
from tpSortDS import TpSortDS
import re
import sys
import subprocess
from pprint import pprint
import pdb
import getopt

def prRed(prt): print("\033[91m {}\033[00m" .format(prt))
def prGreen(prt): print("\033[92m {}\033[00m" .format(prt))
def prYellow(prt): print("\033[93m {}\033[00m" .format(prt))
def prLightPurple(prt): print("\033[94m {}\033[00m" .format(prt))
def prPurple(prt): print("\033[95m {}\033[00m" .format(prt))
def prCyan(prt): print("\033[96m {}\033[00m" .format(prt))
def prLightGray(prt): print("\033[97m {}\033[00m" .format(prt))
def prBlack(prt): print("\033[98m {}\033[00m" .format(prt))

class TpNode:
    """
    Node for dependency graph
    """
    name = "" #name given to the node
    routine = ""  # routine to run for this node

    def __init__(self, name, routine):
        self.name = name
        self.routine = routine
    def __str__(self):
        return 'TpNode: {}'.format(self.name)
    def __repr__(self):
        return self.__str__()

class State:
    """
    State Machine Interace
    """
    __metaclass__ = ABCMeta

    machine = None
    def __init__(self, machine):
        self.machine = machine

    @abstractmethod
    def processLine(self, line):
        pass

    def changeState(self, state):
        self.machine.state = state    


class InitialState(State):
    """
    No State Defined
    """
    def processLine(self, line):
        print("Error processing line: ", line)
        print("Please place lines under a tag")
        Orchestrator.printUsage()
        raise SyntaxError

class IdState(State):
    """
    No State Defined
    """
    def processLine(self, line):
        m = re.match('^(.+):(.+)$', line)
        if m is None:
            print(line, 'not a valid id')
            raise ValueError
        name, routine = m.groups()
        self.machine.tpSortDS.addNode(name, TpNode(name, routine))

class DepState(State):
    """
    State for reading in the dependencies
    """
    def processLine(self, line):
        m=re.match('^(.+)->(.+)$', line)
        if m is None:
            print(line, 'not a valid dependency')
            raise ValueError
        name, depList = m.groups()
        depList = depList.split(',')
        try:
            self.machine.tpSortDS.addDep(name, depList)
        except ValueError as e:
            print('Error found in depList:', depList)
            raise

class IgnoreDepErrorState(State):
    """
    Ignore Dependency errors for routines under this tag
    """
    def processLine(self, line):
        if line not in self.machine.tpSortDS.graph:
            print(line, 'not found in ID')
            raise ValueError
        self.machine.ignoreDepError.add(line)

class SkipState(State):
    """
    Skip the executing for the following
    """
    def processLine(self, line):
        if line not in self.machine.tpSortDS.graph:
            print(line, 'not found in ID')
            raise ValueError
        self.machine.skipList.add(line)

class Orchestrator:
    """
    This class is responsible for reading the policy and
    being able to run the routines
    """
    policy_file = None
    state_map = {}
    state = None
    tpSortDS = TpSortDS()
    skipList = set()
    ignoreDepError = set()

    def __init__(self, policy_file):
        """
        Reads in a policy_file and initialize the dependency graph
        """
        self.policy_file = policy_file
        self.state_map["initialstate"] = InitialState(self)
        self.state_map["id"] = IdState(self)
        self.state_map["dependency"] = DepState(self)
        self.state_map["ignoredeperror"] = IgnoreDepErrorState(self)
        self.state_map["skip"] = SkipState(self)
        self.state = self.state_map["initialstate"]

    def processFile(self, policy_file=None):
        """
        Process each line
        """
        if policy_file is not None:
            self.policy_file = policy_file
        with open(self.policy_file) as f:
            for line in f:
                line = line.strip()
                line = re.sub(r'\s+', '', line)
                if self.lineIsComment(line): #Ignore comments
                    continue
                state = self.isLineStateChange(line)
                if state is None:
                    self.processLine(line)
                else:
                    self.changeState(state)

    def lineIsComment(self, line):
        """
        Check if line is a comment
        """
        if len(line) is 0 or line[0] == '#':
            return True
        else:
            return False

    def isLineStateChange(self, line):
        """
        Check if line is of format [state]
        retur the state if that is true, else return None
        """
        m = re.match("\[(.+)\]", line)
        if m is None:
            return None
        else:
            (state_name, ) = m.groups()
            state_name = state_name.lower()
            if state_name in self.state_map:
                return self.state_map[state_name]
            else:
                print("{}, not a valid tag".format(state_name))
                raise LookupError


    def run(self, name=None):
        """
        Run routines in the graph. if name is given then only run
        that routine and its dependents
        """
        def depHaveError(node):
            for dep_name in self.tpSortDS.getDep(node.name):
                if dep_name not in errorCode or errorCode[dep_name] != 0:
                    return True
            return False


        errorCode = {}
        skipped = set()
        try:
            order = self.tpSortDS.getSorted(name)
        except KeyError as e:
            print('Please check the name of the routines passed. If passing run_list, make sure there are no spaces')
            sys.exit(1)
        prYellow('Running in the following order:\n{}\n\n'.format([node.name for node in order]))
        for node in order:
            #Skip if listed in skip list
            if node.name in self.skipList:
                skipped.add(node.name)
                prRed('Skipping {}. Found it in skiplist'.format(node.name))
                continue
            if node.name not in self.ignoreDepError and depHaveError(node):
                prRed('Skipping {}. Dependencies had error'.format(node.name))
                skipped.add(node.name)
            else:
                try:
                    errorCode[node.name] = subprocess.call(node.routine)
                except FileNotFoundError as e:
                    sys.stderr.write('routine "{}" not found.\n\
                    Please fix the path associated with the ID {}\n\
                    in the file {}\n'\
                    .format(node.routine, node.name, self.policy_file))
                    sys.exit(1)
                except PermissionError as e:
                    sys.stderr.write('routine "{}" \
                            does not have execute permission.\n'.format(node.routine))
                    sys.exit(1)
        #Print results
        #if len(filter(lambda e: e!=0, errorCode.values())) != 0: #If a non 0 return code exists
        #    prRed('Errors found')
        prYellow('\n\nReturn code for each process:')
        pprint(errorCode)
        if len(skipped) > 0:
            prRed('\n\nTotal skipped: {}'.format(len(skipped)))
            print('Following were skipped due to dependencies failing, or because they were in the skip list.\nIf you would like force a routine to run, please include it under the [ignoreDepErrors] tag.\nTo always skip place under the [skip] tag')
            pprint(skipped)

    def processLine(self, line):
        """
        Call the current state to process the line
        """
        self.state.processLine(line)

    def changeState(self, state):
        """
        Call the current state to change the state machine
        """
        self.state.changeState(state)

    #static def
    def printUsage():
        """
        Print the correct policy_file format here
        """
        print("Error found while parsing policy file.")


def main(argv):
    """
    Main routine
    """

    run_list = None
    try:
        opts, args = getopt.getopt(argv,'hr:',["run_list="])
    except getopt.GetoptError:
        print(sys.argv[0], ' [-r routine1,routine2] [--run_list=routine1,routine2]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('argv[0] [--run_list=routine1,routine2]')
            print('make sure the list of routines is comma seperated and does not have spaces')
            sys.exit()
        elif opt in ('-r', '--run_list'):
            run_list = arg

    orch = Orchestrator('policy.conf')
    orch.processFile()
    if run_list is not None:
        orch.run([run.strip() for run in run_list.split(',')])
    else:
        orch.run()
        #orch.run(['sync_check_chipy'])
    
if __name__=='__main__':
    main(sys.argv[1:])
