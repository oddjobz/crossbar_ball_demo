import os
import time
import argparse
import six
import txaio
from pprint import pformat

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.util import sleep
from autobahn.wamp.types import RegisterOptions
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError

from curses import wrapper, curs_set

stdscr = None
args = None


class ClientSession(ApplicationSession):
    """
    Our WAMP session class .. place your app code here!
    """
    edges = {
        'L': -1,
        'R': -1,
        'U': -1,
        'D': -1
    }
    opposites = {
        'L': 'R',
        'R': 'L',
        'T': 'B',
        'B': 'T'
    }

    def onConnect(self):
        self.join(self.config.realm, [u'anonymous'])

    def onChallenge(self, challenge):
        self.log.info("Challenge for method {authmethod} received", authmethod=challenge.method)
        raise Exception("We haven't asked for authentication!")

    @inlineCallbacks
    def onJoin(self, details):        

        def on_join(params):
            node, edge, target = params
            if node == args.node and int(self.edges[edge]) < 0:
                self.edges[edge] = int(target)
                self.publish('com.demo.join', (target, self.opposites[edge], node))    

        def on_new_ball(ball):
            if ball[0] == int(args.node):
                reactor.callLater(0, self.create_ball, ball)

        if args.join:
            node, edge, target = args.join.split(':')
            self.publish('com.demo.join', (node, edge, target))  

        if int(args.node) == 0:
            reactor.callLater(0, self.create_ball,(args.node, 5,5,1,1))
            reactor.callLater(0, self.create_ball,(args.node, 1,1,1.1,0.9))
            reactor.callLater(0, self.create_ball,(args.node, 10,20,0.8,1.2))
        else:
            reactor.callLater(0, self.create_ball,(args.node, 60,10,-1,-0.5))

        yield self.subscribe(on_new_ball, u'com.demo.new_ball')
        yield self.subscribe(on_join, u'com.demo.join')

    def onLeave(self, details):
        self.log.info("Router session closed ({details})", details=details)
        self.disconnect()

    def onDisconnect(self):
        self.log.info("Router connection closed")
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass

    @inlineCallbacks
    def create_ball(self, ball):
        global stdscr
        maxy, maxx = stdscr.getmaxyx()

        def allowable(x, y, maxx, maxy):
            return int(x) >=0 and int(x) < maxx and int(y) >= 0 and int(y) < maxy

        node, pos_x, pos_y, delta_x, delta_y = ball

        while True:

            try:
                if allowable(pos_x, pos_y, maxx, maxy):
                    stdscr.addstr(int(pos_y), int(pos_x), ' ')

                new_x = pos_x + delta_x
                new_y = pos_y + delta_y
                if new_x >= maxx and self.edges['R'] >= 0:
                    stdscr.refresh()
                    self.publish('com.demo.new_ball', (self.edges['R'], -1, new_y, delta_x, delta_y))
                    return

                if new_x < 0 and self.edges['L'] >= 0:
                    stdscr.refresh()
                    self.publish('com.demo.new_ball', (self.edges['L'], maxx, new_y, delta_x, delta_y))
                    return

                if pos_x + delta_x < 0 or pos_x + delta_x >= maxx:
                    delta_x *= -1
                if pos_y + delta_y < 0 or pos_y + delta_y >= maxy:
                    delta_y *= -1
                pos_x += delta_x
                pos_y += delta_y
                if allowable(pos_x, pos_y, maxx, maxy):
                    stdscr.addstr(int(pos_y), int(pos_x), '@')
                if stdscr.getch() != -1:
                    reactor.stop()
                    return
                yield sleep(0.01)
            except Exception as e:
                print(e)
                reactor.stop()  
def main(screen):
    global stdscr

    stdscr = screen
    stdscr.clear()
    stdscr.nodelay(True)
    stdscr.timeout(15)
    curs_set(0)

if __name__ == '__main__':

    url = os.environ.get('CBURL', u'wss://xbr-fx-2.eu-west-2.crossbar.io/ws')
    realm = os.environ.get('CBREALM', u'AppRealm')

    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='Enable debug output.')

    parser.add_argument('--node',
                        dest='node',
                        type=six.text_type,
                        default='0',
                        help='A unique number to describe this node')

    parser.add_argument('--join',
                        dest='join',
                        type=six.text_type,
                        default='',
                        help='A node join string')

    args = parser.parse_args()
    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    wrapper(main)
    runner = ApplicationRunner(url=url, realm=realm)
    runner.run(ClientSession, auto_reconnect=True)
