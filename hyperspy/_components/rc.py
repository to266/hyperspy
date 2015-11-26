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

from __future__ import division
import numpy as np

from hyperspy.component import Component


class RC(Component):

    u"""
    """

    def __init__(self, V=1, V0=0, tau=1.):
        Component.__init__(self, (u'Vmax', u'V0', u'tau'))
        self.Vmax.value, self.V0.value, self.tau.value = V, V0, tau

    def function(self, x):
        u"""
        """
        Vmax = self.Vmax.value
        V0 = self.V0.value
        tau = self.tau.value
        return V0 + Vmax * (1 - np.exp(-x / tau))
