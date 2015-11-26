# -*- coding: utf-8 -*-

from hyperspy import docstrings

__doc__ = u"""
HyperSpy: a multi-dimensional data analysis package for Python
==============================================================

Documentation is available in the docstrings and online at
http://hyperspy.org/hyperspy-doc/current/index.html.

All public packages, functions and classes are in :mod:`~hyperspy.api`. All
other packages and modules are for internal consumption and should not be
needed for data analysis.

%s

More details in the :mod:`~hyperspy.api` docstring.

""" % docstrings.START_HSPY

import os

os.environ[u'QT_API'] = u"pyqt"


from . import Release

__all__ = [u"api"]
__version__ = Release.version
