Twisted Tutorial
================

This tutorial introduces the [Twisted](https://twistedmatrix.com) networking library for Python. We focus on explaining two concepts which any programmer should understand before trying to make or modify any Twisted application: *asynchronous programming* and *Deferreds*.

If you are already familiar with asynchronous programming (a.k.a. event-driven programming, event-loop programming, reactive programming, the reactor pattern) feel free to jump ahead to [the Twisted-specific stuff](#deferreds).




Other Great Twisted References
------------------------------

The [official Twisted documentation](https://twistedmatrix.com/documents/current/core/index.html) can help you get started understanding how Twisted works, but I've found it to be more useful as an API reference. The resources which I've found that best explain how Twisted is meant to be used are:

- [Krondo Twisted Introduction](http://krondo.com/?page_id=1327)
- [Architecture of Open Source Applications - Twisted](http://www.aosabook.org/en/twisted.html)





The Asynchronous Programming Paradigm
-------------------------------------

### What It Isn't ###

My first mistake when coming to Twisted was not understanding the distinction between multi-threaded programming and asynchronous programming. 

In **multi-threaded programming** the programmer gets work done by managing multiple threads of execution running within a single process. Each of these threads is given some time to run according to the whims of the thread scheduler. (Depending on the programming environment, this scheduler may be in userspace or in the kernel.)

When programming within the multi-threaded paradigm, the programmer must always imagine the possiblity that program execution could jump from one place in one thread to (almost) any other place in any other thread. This can make the programmer's job rather difficult, because it requires that he or she needs to often worry about locking data or carefully synchronizing state between threads.




### What It Is ###

**Asynchronous programming** is quite different. In this paradigm, the programmer must set up a number of event handlers to be executed in response to appropriate triggering events. Ideally, an event handler is a relatively short-running reaction to some occasionally-occurring event (e.g. a system timer, a network message's arrival, and user input). Events happen every once in a while, or they may not happen at all.

There is (generally) just one thread of execution which is handling all of these events. Each event is handled in turn, one-by-one. The whole process looks like this:

(1) The event-loop chooses a single event, call it `ev`, to be handled. This `ev` is chosen from the set of recently fired events, each of which is waiting to be handled.

(2) The event-loop calls the event handler for `ev` (possibly with some just-arrived data). This handler is run to completion.

(3) Upon completion, execution returns to the event loop, and the whole process is repeated.

The key is that in the asynchronous paradigm, the programmer never needs to worry about a scheduler non-deterministically jumping between threads of execution: only one thread is needed to manage a very wide variety of events.

So, one can think of the asynchronous programmer's job in the following way: he or she must give commands which set up the system to react to events shortly after they occur.




### What's in a Name? ###

The Twisted literature seems to usually use the term "asynchronous programming", but I personally, I find the terms **event-driven programming** and **event-loop programming** to be much more descriptive terms for this programming paradigm.




### What's It Good For? ###

Asynchronous programming is a very appealing alternative to multi-threaded programming when trying to solving certain kinds of problems, in particular, when making [I/O-bound systems](http://en.wikipedia.org/wiki/I/O_bound). It is used very often in both GUI programming and networking programming.






Deferreds
---------

[Deferreds](https://twistedmatrix.com/documents/current/core/howto/defer.html) are used by Twisted applications to set up work that needs to be done once an event has occured. Let's get a sense of this abstraction using a few simple examples.


### Deferreds can be fired by a system timer. ###

Consider the [`print_later.py`](print_later.py) program:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{.python}
#!/usr/bin/env python

from __future__ import print_function
from twisted.internet import reactor, task

def print_later(mesg):
    ''' Prints the given `mesg` after 1 second has passed. '''
    task.deferLater(reactor, 1, print, mesg)

print_later("The future is now!")
reactor.run()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By calling `deferLater`, we are setting up some (admittedly trivial) work to be done after a time. In this case, we are telling the `reactor` to wait 1 second before it should call the `print` function with `mesg` as its argument. (If you are familiar with Javascript, then this is just like [`setTimeout()`](http://www.w3schools.com/js/js_timing.asp)

The `reactor` is Twisted's way of implementing the event-loop. It monitors events and executes any callbacks which have been assigned to handle these events. Note that once you call `reactor`, the event-loop takes over. Your program effectively blocks on that line until the reactor shuts down. In our example program, we have not given the reactor any instruction to shut itself down. You can shut it down manually by typing `Ctrl-C`.

When I first read about the `reactor`, it gave me the mental image of a nuclear reactor powering a program. But this is wrong metaphor. The `reactor` is just the object which is there to *react* to and handle events as they occur.




### Twisted application code can create and fire its own deferreds. ###

In the example above, `deferLater` is using a `Deferred` object under the hood in order to perform the callback to `print`. However, this is an extremely limited use of deferreds. In order to understand how they are used more generally, let's rewrite this program as [`print_later_twice.py`](print_later_twice.py) such that we manually construct and fire our deferred.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{.python}
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here we can more clearly see the key momemnts involved in the lifetime of a `Deferred` object:

1. Line 8: A generic `Deferred` object is constructed on line 8.
2. Lines 9-10: A sequence of callback functions is added to this `Deferred`'s *callback-chain*. on lines 9-10.
3. Line 11: The `Deferred` is fired using its `callback()` method with a `result`. (In this case, we are telling `reactor` to fire `d` with `mesg` after 1 second of waiting.)

When the `Deferred` is fired, each callback which has been added to the `Deferred`'s callback-chain will be run, one after the other. The object with which the `Deferred` was fired will be passed as the `result` of the first callback function. The argument to subsequent callbacks will be the return value of the preceeding callback.

In our example, our first callback just passes `result` on to the second callback without any changes. However, it can be useful to think of callbacks as stages in a pipeline to incrementally transform an initial input into some output




### Deferreds use callbacks to process input from a blocking source. ###

In the previous examples, we've explained some of the basics building and using `Deferred` objects and how we can use the reactor to create timer event fire a deferred. However, in `Twisted` applications the most common kind of event which fires a deferred is the arrival of input from some blocking source. An example be input arriving from a network connection.

So, a `Deferred` object is a way of encapsulating

1. a `result` of some process (e.g. network process) that might not be available yet, and
2. a sequence of functions for processing this `result` once it arrives.

It can be useful to think of the callback chain as a sequence of functions called in order to *react* to a `result` *once it becomes available*. When using the Twisted API, is often the reactor's responsibility to fire `Deferred` objects once a `result` becomes available, and it is often the client code which adds functions to the callback chain. The [`blocking_input.py`](blocking_input.py) program illustrates this:


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{.python}

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
