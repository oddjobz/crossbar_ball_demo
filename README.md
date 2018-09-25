# Bouncing Ball Demonstration

This demo is designed to demonstrate (visually) multiple cooperating instances of an application
working together using PUB/SUB via a WAMP connection. It will work both in isolation on a local
machine against a remove Crossbar node, and also over Crossbar FX nodes in the Crossbar CFC console.

It is *not* designed to be a demonstration of how to code, if you have the time and/or inclination
and would like to improve the code, PR's would be welcome! There is a deliberate free row at the bottom
of each panel with a view to adding a status bar for example showing the number of balls in each window
and number of throws / catches per second, but for now I'm moving on to the next task.

When running press 'b' to kick off a new ball, or any other key to exit.

#### To install;

Create a virtual environment, then do;
```
pipenv install
```

#### To run;

```
make [instance]
```
For example;
```
make run1
```
The current makefile is designed to cater for a matrix of 3x2 terminal windows, although you are free to 
make up your own layout. Fundamentally you can use the following command line flags;
```
--node=<nn>      # each node must have a unique id
--delay=<nn>     # this is the delay between moves (in ms), default is 50
--join=<node>:<edge>:<node>[,<node>:<edge>:<node>]  # edge = [L,R,U,D]
```
For for example, a simple join between nodes 0 and 1 on the right hand edge of node 0 would be;
```
--join=0:R:1
```
To join node 0 with node 1 on node 0's right hand edge and 0 with 2 on node2's bottom edge;
```
--join=0:R:1,0:D:2
```
If in doubt, take a look at the (working) Makefile .. :)

![balls](https://raw.githubusercontent.com/oddjobz/crossbar_ball_demo/master/balls.png) "Screenshot of application running over six xterm's"