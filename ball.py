import os
import argparse
import six
import txaio
import random
import curses
import signal
from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

args = None


class Ball:

    def __init__(self, stdscr, context, x=None, y=None, dx=None, dy=None):
        """
        New balls please!
        """
        self._stdscr = stdscr
        self._context = context
        self._maxy, self._maxx = self._stdscr.getmaxyx()
        self._maxx -= 1
        self._maxy -= 1
        self._x = x if x else random.uniform(0, self._maxx)
        self._y = y if y else random.uniform(0, self._maxy)
        self._dx = dx if dx else random.uniform(0.0, 1)
        self._dy = dy if dy else random.uniform(0.0, 1)
        self.draw(1)
        self._stdscr.getch()

    def resize(self):
        self._maxy, self._maxx = self._stdscr.getmaxyx()
        if self._x >= self._maxx:
            self._x = self._maxx - 2
        if self._y >= self._maxy:
            self._y = self._maxy - 2

    def is_out(self):
        return self._x < 0 or self._y < 0 or self._x >= self._maxx or self._y >= self._maxy

    def move(self, edges):

        moved = False
        if self._x == -1:
            self._x = self._maxx - 1
            moved = True
        if self._y == -1:
            self._y = self._maxy - 1
            moved = True
        if self._x == -2:
            self._x = 0
            moved = True
        if self._y == -2:
            self._y = 0
            moved = True

        if moved:
            return True

        self._x += self._dx
        if self.is_out():
            self._y += self._dy
            if self._dx > 0:
                if edges['R'] > -1:
                    self._x = -2
                    return self.throw(edges['R'])
            else:
                if edges['L'] > -1:
                    self._x = -1
                    return self.throw(edges['L'])

            self._dx *= -1
            self._x += self._dx

        self._y += self._dy
        if self.is_out():
            self._x += self._dx
            if self._dy > 0:
                if edges['D'] > -1:
                    self._y = -2
                    return self.throw(edges['D'])
            else:
                if edges['U'] > -1:
                    self._y = -1
                    return self.throw(edges['U'])

            self._dy *= -1
            self._y += self._dy

        return True

    def hide(self):
        if not self.is_out():
            try:
                self._stdscr.addstr(int(self._y), int(self._x), ' ')
            except Exception:
                return

    def draw(self, node):
        if not self.is_out():
            try:
                self._stdscr.attron(curses.A_BOLD)
                self._stdscr.addstr(int(self._y), int(self._x), '@', curses.color_pair(int(node)+1))
                self._stdscr.attroff(curses.A_BOLD)
            except Exception:
                return

            self._stdscr.refresh()

    def throw(self, node):
        self._context.publish('com.demo.new_ball', (node, self._x, self._y, self._dx, self._dy))
        return False


class BallBouncer:

    _edges = {
        'L': -1,
        'R': -1,
        'U': -1,
        'D': -1
    }

    def __init__(self, context, node):
        self._context = context
        self._node = node
        self._stdscr = curses.initscr()
        self._balls = []
        self._stdscr.clear()
        self._stdscr.nodelay(True)
        self._stdscr.timeout(10)
        self._stdscr.keypad(True)
        curses.noecho()
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def stop(self):
        curses.nocbreak()
        self._stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def new_ball(self):
        self._balls.append(Ball(self._stdscr, self._context))

    def set_edge(self, edge, target):
        if self._edges[edge] == -1:
            self._edges[edge] = int(target)
            return True
        return False

    @inlineCallbacks
    def create(self):
        while True:
            for ball in self._balls:
                ball.hide()
                if not ball.move(self._edges):
                    self._balls.remove(ball)
                else:
                    ball.draw(self._node)
            self._stdscr.refresh()
            yield sleep(0)
            key = self._stdscr.getch()
            if key == 98:
                self.new_ball()
                continue
            if key == curses.KEY_RESIZE:
                maxy, maxx = self._stdscr.getmaxyx()
                self._stdscr.resize(maxy, maxx)
                for ball in self._balls:
                    ball.resize()
                continue
            if key == -1:
                continue
            try:
                self.stop()
                reactor.stop()
            except ReactorNotRunning:
                pass
            return

    def catch(self, ball):
        if int(ball[0]) == int(self._node):
            self._balls.append(Ball(self._stdscr, context=self._context, x=ball[1], y=ball[2], dx=ball[3], dy=ball[4]))


class ClientSession(ApplicationSession):
    """
    Our WAMP session class .. place your app code here!
    """
    opposites = {
        'L': 'R',
        'R': 'L',
        'T': 'B',
        'B': 'T'
    }

    def __init__(self, *arguments, **kwargs):
        self._bouncer = BallBouncer(self, args.node)
        super().__init__(*arguments, **kwargs)

    def onConnect(self):
        self.join(self.config.realm, [u'anonymous'])

    @inlineCallbacks
    def onJoin(self, details):

        def on_join(params):
            node, edge, target = params
            if node == args.node:
                if self._bouncer.set_edge(edge, target):
                    self.publish('com.demo.join', (target, self.opposites[edge], node))

        yield self.subscribe(on_join, u'com.demo.join')

        def on_new_ball(ball):
            reactor.callLater(0, self._bouncer.catch, ball)

        yield self.subscribe(on_new_ball, u'com.demo.new_ball')

        if args.join:
            node, edge, target = args.join.split(':')
            self.publish('com.demo.join', (node, edge, target))

        for i in range(5):
            self._bouncer.new_ball()
        reactor.callLater(0, self._bouncer.create)

    def onLeave(self, details):
        self.log.info("Router session closed ({details})", details=details)
        self.disconnect()

    def onDisconnect(self):
        self.log.info("Router connection closed")
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass


if __name__ == '__main__':

    url = os.environ.get('CBURL', u'wss://xbr-fx-2.eu-west-2.crossbar.io/ws')
    realm = os.environ.get('CBREALM', u'AppRealm')

    parser = argparse.ArgumentParser()
    parser.add_argument('--node', dest='node', type=six.text_type, default='0', help='A unique number to describe this node')
    parser.add_argument('--join', dest='join', type=six.text_type, default='', help='A node join string')
    args = parser.parse_args()
    txaio.start_logging(level='info')
    runner = ApplicationRunner(url=url, realm=realm)
    runner.run(ClientSession, auto_reconnect=True)
