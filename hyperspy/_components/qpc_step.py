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


class qpc_step(Component):

    """
    """

    def __init__(self, offset=1.0, gradient=1.0, amplitude=1.0, steepness = 1.0, step = 1.0):
        # Define the parameters
        Component.__init__(self, ('offset', 'gradient', 'amplitude', 'steepness', 'step'))
        # Define the identification name of the component
        self.offset.value = offset
        self.gradient.value = gradient
        self.amplitude.value = amplitude
        self.steepness.value = steepness
        self.step.value = step
        self._position = self.step

        self.offset.grad = self.grad_offset
        self.gradient.grad = self.grad_gradient
        self.amplitude.grad = self.grad_amplitude
        self.steepness.grad = self.grad_steepness
        self.step.grad = self.grad_step
        # Optionally we can set the initial values
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
        
        # Optionally, to boost the optimization speed we can define also define
        # the gradients of the function we the syntax:
        # self.parameter.grad = function
#        self.parameter_1.grad = self.grad_parameter_1
#        self.parameter_2.grad = self.grad_parameter_2
    # Define the function as a function of the already defined parameters, x
    # being the independent variable value
    def function(self, x):
        """
        a + b*x + c/(1 + exp(d*(x-e)))
        """
        a = self.offset.value
        b = self.gradient.value
        c = self.amplitude.value
        d = self.steepness.value
        e = self.step.value
        return a+b*x + c/(1 + np.exp(d*(x-e)))

    # Optionally define the gradients of each parameter
    def grad_offset(self, x):
        return 1.

    def grad_gradient(self, x):
        return x

    def grad_amplitude(self, x):
        d = self.steepness.value
        e = self.step.value
        return 1/(1 + np.exp(d*(x-e)))

    def grad_steepness(self, x):
        c = self.amplitude.value
        d = self.steepness.value
        e = self.step.value

        ede = np.exp(d*e)
        edx = np.exp(d*x)
        temp = (ede + edx)*(ede+edx)
        return (c*(e-x)*ede*edx)/temp

    def grad_step(self, x):
        c = self.amplitude.value
        d = self.steepness.value
        e = self.step.value

        ede = np.exp(d*e)
        edx = np.exp(d*x)
        temp = (ede+edx)*(ede+edx)
        return (c*d*ede*edx)/temp
