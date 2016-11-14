# -*- coding: utf-8 -*-
# Copyright 2007-2011 The Hyperspy developers
#
# This file is part of  Hyperspy.
#
#  Hyperspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  Hyperspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with  Hyperspy.  If not, see <http://www.gnu.org/licenses/>.

from hyperspy.component import Component

import numpy as np
from numpy import complex128 as complex_
from scipy.special import jn, yv, kn, gegenbauer
from numpy.polynomial.polynomial import polyval
from scipy.misc import factorial, factorial2
from scipy.interpolate import interp1d
from scipy import constants


def N_eval(l, m, voc):
    gamma = 1 / np.sqrt(1 - voc * voc)
    am = np.abs(m)
    if l - am < 0:
        return complex_(0.0)
    else:
        geg = np.array(gegenbauer(l - am, am + 0.5))[::-1]
        total = np.sqrt(
            (2 * l + 1) * factorial(l - am) / (np.pi * factorial(l + am)))
        total *= factorial2(int(2 * am - 1.)) / ((gamma * voc) ** am)
        total *= polyval(1 / voc, geg)
        return complex_(total)


def get_consts(l, m, v, c):
    voc = v / c
    gamma = 1 / np.sqrt(1 - voc * voc)
    Nn = N_eval(l, m, voc)
    Np = N_eval(l, m + 1.0, voc)
    Nm = N_eval(l, m - 1.0, voc)
    M = complex_(
        Np * np.sqrt((l + m + 1) * (l - m)) + Nm * np.sqrt((l - m + 1) * (l + m)))
    Ca = 1 / (l * (l + 1.0))
    Cb = 1 / (l * (l + 1.0))
    Cb *= np.abs(2 * m * Nn) ** 2.0
    Ca *= np.abs(M / (voc * gamma)) ** 2.0
    return Ca, Cb


def EELS(b, w, v, c, lmax, x1, x2, single=False):
    voc = v / c
    gamma = (1.0 - voc * voc) ** (-0.5)
    ans = 0.
    epsilon = x2 * x2 / (x1 * x1)
    sqx1 = np.sqrt(0.5 * np.pi / x1)
    sqx2 = np.sqrt(0.5 * np.pi / x2)
    k = w / constants.c
    if single:
        lmin = lmax
    else:
        lmin = 1.0
    for l in np.arange(lmin, lmax + 1.0):
        jx1 = sqx1 * jn(l + 0.5, x1)
        jx2 = sqx2 * jn(l + 0.5, x2)
        jx1minus = sqx1 * jn(l - 0.5, x1)
        jx2minus = sqx2 * jn(l - 0.5, x2)
        yx1 = sqx1 * yv(l + 0.5, x1)
        yx1minus = sqx1 * yv(l - 0.5, x1)

        jx1prime = jx1minus - ((l + 1) / x1) * jx1
        jx2prime = jx2minus - ((l + 1) / x2) * jx2
        yx1prime = yx1minus - ((l + 1) / x1) * yx1

        x1jx1prime = jx1 + x1 * jx1prime
        x2jx2prime = jx2 + x2 * jx2prime

        hplusx1 = 1j * jx1 - yx1
        hplusx1prime = 1j * jx1prime - yx1prime
        x1hplusx1prime = hplusx1 + x1 * hplusx1prime

        aa = complex_((- jx1 * x2jx2prime + epsilon * x1jx1prime * jx2) /
                      (hplusx1 * x2jx2prime - epsilon * x1hplusx1prime * jx2))
        bb = complex_((x1 * jx1prime * jx2 - jx1 * x2 * jx2prime) / 
                      (hplusx1 * x2 * jx2prime - x1 * hplusx1prime * jx2))

        for m in np.arange(-l, l + 1.):
            Ca, Cb = get_consts(l, m, v, c)
            tmp = Ca * np.imag(aa) + Cb * np.imag(bb)
            ans += tmp * (kn(m, w * b / (v * gamma)) ** 2.0)
    return np.real(ans)


def get_dielectric(wavelength, mfile, n=True):
    """
    wavelength in um
    mfile : um Re Im
    n : bool, default = True
        if True, recorded value is refractive index
        if False - epsilon
    """
    cxheV = constants.physical_constants[
        'Planck constant in eV s'][0] * constants.c
    if not n:
        wavelength = cxheV / (wavelength * 1e-6)
    tab = np.loadtxt(mfile, skiprows=3)
    Re = np.interp(wavelength, tab[:, 0], tab[:, 1])
    Im = np.interp(wavelength, tab[:, 0], tab[:, 2])
    if n:
        return complex_(Re * Re - Im * Im + 2j * Re * Im)
    else:
        return complex_(Re + 1j * Im)


def get_dielectric_function(mfile, kkind='cubic'):
    # assume that the axis is at the same units
    tab = np.loadtxt(mfile)
    re = interp1d(
        tab[:, 0], tab[:, 1], kind=kkind, bounds_error=False, fill_value=np.nan)
    im = interp1d(
        tab[:, 0], tab[:, 2], kind=kkind, bounds_error=False, fill_value=np.nan)
    return re, im


class EELS_peak(Component):

    """
    """

    def __init__(
            self, radius=3e-8, b=4e-8, x0=0, width=1.0, area=1.0, v=2.33e8):
        Component.__init__(self, ('radius', 'b', 'x0', 'width', 'area', 'v'))

        self.radius.value = radius
        self.radius.ext_force_positive = True
        self.b.value = b
        self.b.ext_force_positive = True

        self.x0.value = x0
        self.width.value = width
        self.width.free = False

        self.area.value = area
        self.area.ext_force_positive = True

        self.v.value = v
        self.v.free = False

        self.v.units = 'm/s'
        self.radius.units = 'm'
        self.b.units = 'm'

        self.epsilon = None
        self._eps_file = ''
        self.eps_type_n = True
        self.eps_set = False

        self._eps_en = None
        self._eps_re = None
        self._eps_im = None

        self._ord = 1.
        self._single = False

        self._bulk = np.inf

    @property
    def eps_file(self):
        return self._eps_file

    @eps_file.setter
    def eps_file(self, value):
        if value != '':
            self._eps_file = value
            import copy
            if self.eps_type_n:
# assume epsilon <==> eV and n <==> lambda in files
                tab = np.loadtxt(value, skiprows=3)
                cxheV = constants.physical_constants[
                    'Planck constant in eV s'][0] * constants.c
                self._eps_en = cxheV / copy.deepcopy(tab[:, 0] * 1e-6)
                self._eps_re = copy.deepcopy(tab[:, 1] ** 2 - tab[:, 2] ** 2)
                self._eps_im = copy.deepcopy(tab[:, 1] * tab[:, 2] * 2.0)
            else:
                tab = np.loadtxt(value)
                self._eps_en = copy.deepcopy(tab[:, 0])
                self._eps_re = copy.deepcopy(tab[:, 1])
                self._eps_im = copy.deepcopy(tab[:, 2])

            def epsf(x):
                re = np.interp(
                    x, self._eps_en, self._eps_re, left=self._eps_re[
                        np.argmin(
                            self._eps_en)], right=self._eps_re[
                        np.argmax(
                            self._eps_en)])
                im = np.interp(
                    x, self._eps_en, self._eps_im, left=self._eps_im[
                        np.argmin(
                            self._eps_en)], right=self._eps_im[
                        np.argmax(
                            self._eps_en)])
                return complex_(re + 1j * im)
            self.epsilon = epsf

    def function(self, x):
        """
        This functions it too complicated to explain
        """
        if self.epsilon is None:
            return np.nan

        r = self.radius.value
        b = self.b.value
        x0 = self.x0.value
        width = self.width.value
        area = self.area.value
        v = self.v.value
        ax = (x - x0) * width
        # assume axis (and x, ax, etc) is in eV:
        cxheV = constants.physical_constants[
            'Planck constant in eV s'][0] * constants.c
        wavelength = cxheV / ax
        k = 2 * np.pi / wavelength
        omega = k * constants.c

        epsilon = self.epsilon(ax)
        if np.any(ax > self._bulk):
            epsilon[ax > self._bulk] = epsilon[ax.searchsorted(self._bulk)]

        xx1 = r * k
        xx2 = xx1 * (epsilon) ** 0.5
        res = EELS(b + r, omega, v, constants.c, self._ord, xx1, xx2,
                   self._single) * area
        # res *= constants.e ** 2.0 / (constants.c * constants.hbar)
# to get something of similart orders ofmagnitude:
        res *= 1e12
        res /= omega
        # if  np.any(ax>self._bulk):
        # epsilon[ax> self._bulk].fill(epsilon[ax.searchsorted(self._bulk)])
        # res[ax > self._bulk] = 0.0
        #     res[ax > self._bulk].fill(res[ax.searchsorted(self._bulk)])
        return res
