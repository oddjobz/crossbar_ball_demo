.PHONEY: all

# export CBURL=wss://demo1.crossbar.io
# export CBREALM=realm1

all:

run:
	python ball.py --node=0

run-r:
	python ball.py --node=1 --join=0:R:1