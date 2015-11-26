# -*- coding: utf-8 -*-
# Copyright 2007-2015 The HyperSpy developers
#
# This file is part of  HyperSpy.
#
#  HyperSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  HyperSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with  HyperSpy.  If not, see <http://www.gnu.org/licenses/>.


name = u'hyperspy'

# The commit following to a release must update the version number
# to the version number of the release followed by "+dev", e.g.
# if the version of the last release is 0.4.1 the version of the
# next development version afterwards must be 0.4.1+dev.
# When running setup.py the "+dev" string will be replaced (if possible)
# by the output of "git describe" if git is available or the git
# hash if .git is present.
version = u"0.8.2-152-g401a179-dirty"
description = u"Multidimensional data analysis toolbox"
license = u'GPL v3'

authors = {
    u'all': (u'The HyperSpy developers',
            u'hyperspy-devel@googlegroups.com'), }

url = u'http://hyperspy.org'

download_url = u'http://www.hyperspy.org'
documentation_url = u'http://hyperspy.org/hyperspy-doc/current/index.html'

platforms = [u'Linux', u'Mac OSX', u'Windows XP/2000/NT', u'Windows 95/98/ME']

keywords = [u'EDX',
            u'EELS',
            u'EFTEM',
            u'EMSA',
            u'FEI',
            u'ICA',
            u'PCA',
            u'PES',
            u'STEM',
            u'TEM',
            u'curve fitting',
            u'data analysis',
            u'dm3',
            u'electron energy loss spectroscopy',
            u'electron microscopy',
            u'emi',
            u'energy dispersive x-rays',
            u'hyperspectral',
            u'hyperspectrum',
            u'multidimensional',
            u'hyperspy',
            u'machine learning',
            u'microscopy',
            u'model',
            u'msa',
            u'numpy',
            u'python',
            u'quantification',
            u'scipy',
            u'ser',
            u'spectroscopy',
            u'spectrum image']

info = u"""
    H y p e r S p y
    Version %s

    http://www.hyperspy.org

    """ % version.replace(u'_', u' ')
 
