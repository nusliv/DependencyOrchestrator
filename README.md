# Dependency based Orchestrator
A ephemeral script which can be called either from init.d at boot-up or to orchestrate a sequence of events due to an interrupt

I have run into situations where I need init.d to start processes and complete certain tasks. However managing the order of calling is a pain in system V. Dealing with all the file names and renaming if there are dependencies in the middle.. ya its a pain. Wrote this simple script which takes in a list of dependencies for each task and figures out the order to call the tasks using a dependency graph (topological sort). I have also found this useful in managing systems. I also love using it to orchestrate mundane things on my system.

1) Create directories to organize your routines. The routines can be any binary or script.
2) Write your dependencies in a policy file.
3) Call orchestrate.py <-r r1,r2..>

TODO: Take in the policy file name in arguments. This makes it possible to break down the files into smaller pieces for mutually exclusive routines.
