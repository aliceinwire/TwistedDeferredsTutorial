#!/usr/bin/env python

#!/usr/bin/env python

from __future__ import print_function
from twisted.internet import reactor, defer

def print_and_passthrough(result):
    print(result)
    return result

def print_later_twice(mesg):
    ''' Prints the given `mesg` after 1 second has passed. '''
    d = defer.Deferred()
    d.addCallback(print_and_passthough)
    d.addCallback(print_and_passthough)
    reactor.callLater(1, d.callback, mesg)

    print_later_twice("The future is now!")
    reactor.run()
