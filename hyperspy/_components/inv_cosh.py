# -*- coding: utf-8 -*-
# Copyright 2007-2011 The HyperSpy developers
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

from hyperspy.component import Component
import numpy as np


class inverse_cosh(Component):

    """
    a/(cosh(b(x-x0)))^2
    """

    def __init__(self, width=1, centre=2, A=1):
        # Define the parameters
        Component.__init__(self, ('width', 'centre', 'A'))
        # Define the identification name of the component

        # Optionally we can set the initial values
        self.width.value = width
        self.centre.value = centre
        self.A.value = A
        self._position = self.centre

        self.width.grad = self.grad_width
        self.centre.grad = self.grad_centre
        self.A.grad = self.grad_A
#        self.parameter_1.value = parameter_1
#        self.parameter_1.value = parameter_1

        # The units
#        self.parameter_1.units = 'Tesla'
#        self.parameter_2.units = 'Kociak'

        # Once defined we can give default values to the attribute is we want
        # For example we fix the attribure_1
#        self.parameter_1.attribute_1.free = False
        # And we set the boundaries
#        self.parameter_1.bmin = 0.
#        self.parameter_1.bmax = None

    def function(self, x):
        """
        a/(cosh(b(x-x0)))^2
        """
        a = self.A.value
        b = self.width.value
        x0 = self.centre.value
        tmp = np.cosh(b*(x-x0))
        return a/(tmp*tmp)

    # Optionally define the gradients of each parameter

    def grad_centre(self, x):
        a = self.A.value
        b = self.width.value
        c = self.centre.value
        tmp1 = b*(x-c)
        tmp2 = np.cosh(tmp1)
        return 2*a*b*np.tanh(tmp1) /(tmp2*tmp2)

    def grad_A(self,x):
        a = self.A.value
        b = self.width.value
        c = self.centre.value
        tmp2 = np.cosh(b*(x-c))
        return 1.0 / (tmp2*tmp2)

    def grad_width(self, x):
        a = self.A.value
        b = self.width.value
        c = self.centre.value
        tmp1 = b*(x-c)
        tmp2 = np.cosh(tmp1)
        return 2.0*a*(c-x)*np.tanh(tmp1) /(tmp2*tmp2)
