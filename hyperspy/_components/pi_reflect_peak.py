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


class Pi_Reflectometry_peak(Component):

    """
    """

    def __init__(self, Z0=50., R=2, C=1., L=1., A=20., D=1.):
        # Define the parameters
        Component.__init__(self, ('Z0', 'R', 'C', 'L', 'A', 'D'))
        # Define the identification name of the component
        self.Z0.value = Z0
        self.R.value = R
        self.C.value = C
        self.L.value = L
        self.A.value = A
        self.D.value = D

        self.Z0.units = 'Ohm'
        self.R.units = 'MOhm'
        self.C.units = 'pF'
        self.D.units = 'pF'
        self.L.units = 'nH'

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

    def function(self, x):
        """
        """
        omega = 2. * np.pi * x
        w = omega
        R = self.R.value * 1e6
        Z0 = self.Z0.value
        C = self.C.value * 1e-12
        L = self.L.value * 1e-9
        A = self.A.value
        D = self.D.value * 1e-12
        # Z = L * w * 1j + R / (1 + 1j * w * C * R)
        Z = (R + 1j * w * L - w * w * D * R * L) / (1j * w * C * R - w *
                                                    w * L * C - 1j * w * w * w * C * D * R * L + 1 + 1j * w * D * R)
        #Zreal = R / (1 + omega*omega*C*C*R*R)
        Gamma = (Z - Z0) / (Z + Z0)

        return A * np.abs(Gamma)

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
