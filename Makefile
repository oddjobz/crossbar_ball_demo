.PHONEY: all

DELAY=30

export CBREALM = AppRealm
export CBURL = wss://xbr-fx-1.eu-west-2.crossbar.io:443/ws

all:
	@echo 'usage: make run1|run2|run3|run4|run5|run6'

run1:
	python ball.py --node=0 --delay=$(DELAY)

run2:
	python ball.py --node=1 --join=0:R:1 --delay=$(DELAY)

run3:
	python ball.py --node=2 --join=1:R:2 --delay=$(DELAY)

run4:
	python ball.py --node=3 --join=0:D:3 --delay=$(DELAY)

run5:
	python ball.py --node=4 --join=1:D:4,3:R:4 --delay=$(DELAY)

run6:
	python ball.py --node=5 --join=2:D:5,4:R:5 --delay=$(DELAY)
