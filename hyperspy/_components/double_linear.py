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


class Double_linear(Component):

    """
    """

    def __init__(self, inter=1, height=2, grad1 = 1, grad2 = 1.5):
        # Define the parameters
        Component.__init__(self, ('inter', 'height', 'grad1', 'grad2'))

        self._position = self.height
        self.inter.value = inter
        self.height.value = height
        self.grad1.value = grad1
        self.grad2.value = grad2

        # Once defined we can give default values to the attribute is we want
        # For example we fix the attribure_1
#        self.parameter_1.attribute_1.free = False
        # And we set the boundaries
#        self.parameter_1.bmin = 0.
#        self.parameter_1.bmax = None

        # Optionally, to boost the optimization speed we can define also define
        # the gradients of the function we the syntax:
        # self.parameter.grad = function
#        self.parameter_1.grad = self.grad_parameter_1
#        self.parameter_2.grad = self.grad_parameter_2
    # Define the function as a function of the already defined parameters, x
    # being the independent variable value
    def function(self, x):
        """
        """
        inter = self.inter.value
        h = self.height.value
        a = self.grad1.value
        b = self.grad2.value

        ans = np.empty_like(x)
        ans[x<=inter] = h + (x[x<=inter]-inter)*a
        ans[x>inter] = h + (x[x>inter]-inter)*b
        return ans

    # Optionally define the gradients of each parameter
#    def grad_parameter_1(self, x):
#        """
#        Returns d(function)/d(parameter_1)
#        """
#        return 0
#    def grad_parameter_2(self, x):
#        """
#        Returns d(function)/d(parameter_2)
#        """
#        return x
