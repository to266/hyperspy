#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# progressbar - Text progressbar library for python
# Copyright (c) 2008 Nilton Volpato
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  a. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#  b. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  c. Neither the name of the author nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


u"""Text progressbar library for python.

This library provides a text mode progressbar. This is tipically used
to display the progress of a long running operation, providing a
visual clue that processing is underway.

The ProgressBar class manages the progress, and the format of the line
is given by a number of widgets. A widget is an object that may
display diferently depending on the state of the progress. There are
three types of widget:
- a string, which always shows itself;
- a ProgressBarWidget, which may return a diferent value every time
it's update method is called; and
- a ProgressBarWidgetHFill, which is like ProgressBarWidget, except it
expands to fill the remaining width of the line.

The progressbar module is very easy to use, yet very powerful. And
automatically supports features like auto-resizing when available.
"""

from __future__ import division
__author__ = u"Nilton Volpato"
__author_email__ = u"first-name dot last-name @ gmail.com"
__date__ = u"2006-05-07"
__version__ = u"2.2"

# Changelog
#
# 2006-05-07: v2.2 fixed bug in windows
# 2005-12-04: v2.1 autodetect terminal width, added start method
# 2005-12-04: v2.0 everything is now a widget (wow!)
# 2005-12-03: v1.0 rewrite using widgets
# 2005-06-02: v0.5 rewrite
# 2004-??-??: v0.1 first version


import sys
import time
from array import array
try:
    from fcntl import ioctl
    import termios
except ImportError:
    pass


def running_from_terminal():
    try:
        # Check if it is running inside IPython
        __IPYTHON__
        # Check that it is available (i.e. that we are not in the
        # standard terminal vs the Notebook, QtConsole...
        # clear_output()
        from IPython.core.interactiveshell import InteractiveShell
        InteractiveShell.instance().display_pub.clear_output
        from IPython.core.display import clear_output
        return False
    except:
        return True


class ProgressBarWidget(object):

    u"""This is an element of ProgressBar formatting.

    The ProgressBar object will call it's update value when an update
    is needed. It's size may change between call, but the results will
    not be good if the size changes drastically and repeatedly.
    """

    def update(self, pbar):
        u"""Returns the string representing the widget.

        The parameter pbar is a reference to the calling ProgressBar,
        where one can access attributes of the class for knowing how
        the update must be made.

        At least this function must be overriden."""
        pass


class ProgressBarWidgetHFill(object):

    u"""This is a variable width element of ProgressBar formatting.

    The ProgressBar object will call it's update value, informing the
    width this object must the made. This is like TeX \\hfill, it will
    expand to fill the line. You can use more than one in the same
    line, and they will all have the same width, and together will
    fill the line.
    """

    def update(self, pbar, width):
        u"""Returns the string representing the widget.

        The parameter pbar is a reference to the calling ProgressBar,
        where one can access attributes of the class for knowing how
        the update must be made. The parameter width is the total
        horizontal width the widget must have.

        At least this function must be overriden."""
        pass


def format_time(seconds):
    return time.strftime(u'%H:%M:%S', time.gmtime(seconds))


class ETA(ProgressBarWidget):

    u"""Widget for the Estimated Time of Arrival"""

    def update(self, pbar):
        if pbar.currval == 0:
            return u'ETA:  --:--:--'
        elif pbar.finished:
            return u'Time: %s' % format_time(pbar.seconds_elapsed)
        else:
            elapsed = pbar.seconds_elapsed
            eta = elapsed * pbar.maxval / pbar.currval - elapsed
            return u'ETA:  %s' % format_time(eta)


class FileTransferSpeed(ProgressBarWidget):

    u"""Widget for showing the transfer speed (useful for file transfer)."""

    def __init__(self):
        self.fmt = u'%6.2f %s'
        self.units = [u'B', u'K', u'M', u'G', u'T', u'P']

    def update(self, pbar):
        if pbar.seconds_elapsed < 2e-6:  # == 0:
            bps = 0.0
        else:
            bps = float(pbar.currval) / pbar.seconds_elapsed
        spd = bps
        for u in self.units:
            if spd < 1000:
                break
            spd /= 1000
        return self.fmt % (spd, u + u'/s')


class RotatingMarker(ProgressBarWidget):

    u"""A rotating marker for filling the bar of progress."""

    def __init__(self, markers=u'|/-\\'):
        self.markers = markers
        self.curmark = -1

    def update(self, pbar):
        if pbar.finished:
            return self.markers[0]
        self.curmark = (self.curmark + 1) % len(self.markers)
        return self.markers[self.curmark]


class Percentage(ProgressBarWidget):

    u"""Just the percentage done."""

    def update(self, pbar):
        return u'%3d%%' % pbar.percentage()


class Bar(ProgressBarWidgetHFill):

    u"""The bar of progress. It will strech to fill the line."""

    def __init__(self, marker=u'#', left=u'|', right=u'|'):
        self.marker = marker
        self.left = left
        self.right = right

    def _format_marker(self, pbar):
        if isinstance(self.marker, unicode):
            return self.marker
        else:
            return self.marker.update(pbar)

    def update(self, pbar, width):
        percent = pbar.percentage()
        cwidth = width - len(self.left) - len(self.right)
        marked_width = int(percent * cwidth / 100)
        m = self._format_marker(pbar)
        bar = (self.left + (m * marked_width).ljust(int(cwidth)) + self.right)
        return bar


class ReverseBar(Bar):

    u"""The reverse bar of progress, or bar of regress. :)"""

    def update(self, pbar, width):
        percent = pbar.percentage()
        cwidth = width - len(self.left) - len(self.right)
        marked_width = int(percent * cwidth / 100)
        m = self._format_marker(pbar)
        bar = (self.left + (m * marked_width).rjust(int(cwidth)) + self.right)
        return bar

default_widgets = [Percentage(), u' ', Bar()]


class DummyProgressBar(object):

    def __init__(self):
        return

    @staticmethod
    def start():
        return

    @staticmethod
    def finish():
        return

    def next(self):
        return

    @staticmethod
    def update(*args, **kwargs):
        return


class ProgressBar(object):

    u"""This is the ProgressBar class, it updates and prints the bar.

    The term_width parameter may be an integer. Or None, in which case
    it will try to guess it, if it fails it will default to 80 columns.

    The simple use is like this:
    >>> pbar = ProgressBar().start()
    >>> for i in xrange(100):
    ...    # do something
    ...    pbar.update(i+1)
    ...
    >>> pbar.finish()

    But anything you want to do is possible (well, almost anything).
    You can supply different widgets of any type in any order. And you
    can even write your own widgets! There are many widgets already
    shipped and you should experiment with them.

    When implementing a widget update method you may access any
    attribute or function of the ProgressBar object calling the
    widget's update method. The most important attributes you would
    like to access are:
    - currval: current value of the progress, 0 <= currval <= maxval
    - maxval: maximum (and final) value of the progress
    - finished: True if the bar is have finished (reached 100%), False o/w
    - start_time: first time update() method of ProgressBar was called
    - seconds_elapsed: seconds elapsed since start_time
    - percentage(): percentage of the progress (this is a method)
    """

    def __init__(self, maxval=100, widgets=default_widgets,
                 term_width=None,):
        assert maxval >= 0
        maxval = 1 if maxval == 0 else maxval
        self.maxval = maxval
        self.widgets = widgets
        self.signal_set = False
        if term_width is None:
            try:
                self.handle_resize(None, None)
                signal.signal(signal.SIGWINCH, self.handle_resize)
                self.signal_set = True
            except:
                self.term_width = 79
        else:
            self.term_width = term_width

        self.currval = 0
        self.finished = False
        self.prev_percentage = -1
        self.start_time = None
        self.seconds_elapsed = 0
        if running_from_terminal() is False:
            self.print_line = self._print_ipython
            self.fd = sys.stdout
        else:
            self.print_line = self._print_terminal
            self.fd = sys.stderr

    def handle_resize(self, signum, frame):
        h, w = array(u'h', ioctl(self.fd, termios.TIOCGWINSZ, u'\0' * 8))[:2]
        self.term_width = w

    def percentage(self):
        u"""Returns the percentage of the progress."""
        return self.currval * 100.0 / self.maxval

    def _format_widgets(self):
        r = []
        hfill_inds = []
        num_hfill = 0
        currwidth = 0
        for i, w in enumerate(self.widgets):
            if isinstance(w, ProgressBarWidgetHFill):
                r.append(w)
                hfill_inds.append(i)
                num_hfill += 1
            elif isinstance(w, unicode):
                r.append(w)
                currwidth += len(w)
            else:
                weval = w.update(self)
                currwidth += len(weval)
                r.append(weval)
        for iw in hfill_inds:
            r[iw] = r[iw].update(
                self,
                (self.term_width - currwidth) / num_hfill)
        return r

    def _format_line(self):
        return u''.join(self._format_widgets()).ljust(int(self.term_width))

    def _need_update(self):
        return int(self.percentage()) != int(self.prev_percentage)

    def update(self, value):
        u"""Updates the progress bar to a new value."""
        assert 0 <= value <= self.maxval
        self.currval = value
        if not self._need_update() or self.finished:
            return
        if not self.start_time:
            self.start_time = time.time()
        self.seconds_elapsed = time.time() - self.start_time
        self.prev_percentage = self.percentage()
        self.print_line()

    def _print_ipython(self):
        value = self.currval
        print u'\r', self._format_line(),
        sys.stdout.flush()
        if value == self.maxval:
            self.finished = True
            print u"\n"

    def _print_terminal(self):
        value = self.currval
        if value != self.maxval:
            self.fd.write(self._format_line() + u'\r')
        else:
            self.finished = True
            self.fd.write(self._format_line() + u'\n')

    def next(self):
        self.update(self.currval + 1)

    def start(self):
        u"""Start measuring time, and prints the bar at 0%.

        It returns self so you can use it like this:
        >>> pbar = ProgressBar().start()
        >>> for i in xrange(100):
        ...    # do something
        ...    pbar.update(i+1)
        ...
        >>> pbar.finish()
        """
        self.update(0)
        return self

    def finish(self):
        u"""Used to tell the progress is finished."""
        self.update(self.maxval)
        if self.signal_set:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)


class MyBar(object):

    u"""Encapsulation of a nice progress bar"""

    def __init__(self, text):
        self.text = text

    def init(self, max):
        widgets = [self.text, u' ', Percentage(), u' ', Bar(), u' ', ETA()]
        self.pbar = ProgressBar(widgets=widgets, maxval=max).start()

    def update(self, i):
        self.pbar.update(i)


def progressbar(text=u"calculating", maxval=100, disabled=False):
    u"""
    Returns a useful default progressbar.

    Examples
    --------

    >>> pbar=progressbar(maxval=10000)
    >>> for i in xrange(10000):
            pbar.update(i)
            #do some heavy calculation in each step
    >>> pbar.finish()

    """
    if disabled:
        return DummyProgressBar()
    else:
        widgets = [text, u" ", Percentage(), u' ', Bar(), u' ', ETA()]
        return ProgressBar(widgets=widgets, maxval=maxval).start()


if __name__ == u'__main__':

    def example1():
        widgets = [u'Test: ', Percentage(), u' ', Bar(marker=RotatingMarker()),
                   u' ', ETA(), u' ', FileTransferSpeed()]
        pbar = ProgressBar(widgets=widgets, maxval=10000000).start()
        pbar.clear_output = False
        for i in xrange(1000000):
            # do something
            pbar.update(10 * i + 1)
        pbar.finish()
        print

    def example2():
        class CrazyFileTransferSpeed(FileTransferSpeed):

            u"""It's bigger between 45 and 80 percent"""

            def update(self, pbar):
                if 45 < pbar.percentage() < 80:
                    return u'Bigger Now ' + FileTransferSpeed.update(self, pbar)
                else:
                    return FileTransferSpeed.update(self, pbar)

        widgets = [
            CrazyFileTransferSpeed(),
            u' <<<',
            Bar(),
            u'>>> ',
            Percentage(),
            u' ',
            ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=10000000)
        # maybe do something
        pbar.start()
        for i in xrange(2000000):
            # do something
            pbar.update(5 * i + 1)
        pbar.finish()
        print

    def example3():
        widgets = [Bar(u'>'), u' ', ETA(), u' ', ReverseBar(u'<')]
        pbar = ProgressBar(widgets=widgets, maxval=10000000).start()
        for i in xrange(1000000):
            # do something
            pbar.update(10 * i + 1)
        pbar.finish()
        print

    def example4():
        widgets = [u'Test: ', Percentage(), u' ',
                   Bar(marker=u'0', left=u'[', right=u']'),
                   u' ', ETA(), u' ', FileTransferSpeed()]
        pbar = ProgressBar(widgets=widgets, maxval=500)
        pbar.start()
        for i in xrange(100, 500 + 1, 50):
            time.sleep(0.2)
            pbar.update(i)
        pbar.finish()
        print

    example1()
    example2()
    example3()
    example4()
