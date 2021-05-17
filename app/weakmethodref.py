'''
Weak Method
===========

Adopted from https://github.com/kivy/kivy/issues/6865

The :class:`WeakMethod` is used by the :class:`~kivy.clock.Clock` class to
allow references to a bound method that permits the associated object to
be garbage collected. Please refer to
`examples/core/clock_method.py` for more information.

This WeakMethod class is taken from the recipe
http://code.activestate.com/recipes/81253/, based on the nicodemus version.
Many thanks nicodemus!
'''

import weakref
import sys

if sys.version > '3':

    class WeakMethod:
        '''Implementation of a
        `weakref <http://en.wikipedia.org/wiki/Weak_reference>`_
        for functions and bound methods.
        '''
        def __init__(self, method):
            self.method = None
            self.method_name = None
            try:
                #call_frames = inspect.stack()
                #self.stacktrace= "\n".join([">>>  " + os.path.basename(t.filename) + ":" + str(t.lineno) + " " + t.function for t in call_frames[1:]])
                #self.called_method = method.__func__.__name__
                if method.__self__ is not None:
                    self.method_name = method.__func__.__name__
                    self.proxy = method.__self__ # weakref.proxy(method.__self__)
                else:
                    self.method = method
                    self.proxy = None
            except AttributeError:
                self.method = method
                self.proxy = None

        def do_nothing(self,*args):
            print("do_nothing instead of method ", self.called_method, "generated in:")
            print(self.stacktrace)

        def __call__(self):
            '''Return a new bound-method like the original, or the
            original function if it was just a function or unbound
            method.
            Returns None if the original object doesn't exist.
            '''
            try:
                if self.proxy:
                    return getattr(self.proxy, self.method_name)
            except ReferenceError:
                pass
            return self.do_nothing if self.method is None else self.method

        def is_dead(self):
            '''Returns True if the referenced callable was a bound method and
            the instance no longer exists. Otherwise, return False.
            '''
            try:
                return self.proxy is not None and not bool(dir(self.proxy))
            except ReferenceError:
                print("Callback ", self.called_method, " no longer exists, generated in:")
                print(self.stacktrace)
                return True

        def __eq__(self, other):
            try:
                if type(self) is not type(other):
                    return False
                s = self()
                return s is not None and s == other()
            except:
                return False

        def __repr__(self):
            return '<WeakMethod proxy={} method={} method_name={}>'.format(
                   self.proxy, self.method, self.method_name)

    def fixBugs():
        import kivy.weakmethod as wm

        wm.WeakMethod.is_dead = WeakMethod.is_dead
        wm.WeakMethod.__init__ = WeakMethod.__init__
        wm.WeakMethod.__call__ = WeakMethod.__call__
        wm.WeakMethod.do_nothing = WeakMethod.do_nothing
