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

u"""Creates Digital Micrograph scripts to generate the dm3 testing files
"""

from __future__ import with_statement
import numpy as np
from io import open
from itertools import izip

dm3_data_types = {
    1: u'<i2',  # 2 byte integer signed ("short")
    2: u'<f4',  # 4 byte real (IEEE 754)
    3: u'<c8',  # 8 byte complex
    5: u'<c8',  # 8 byte complex (packed)
    6: u'<u1',  # 1 byte integer unsigned ("byte")
    7: u'<i4',  # 4 byte integer signed ("long")
    8: np.dtype([(u'R', u'u1'), (u'G', u'u1'), (u'B', u'u1'), (u'A', u'u1')]),
    9: u'<i1',  # byte integer signed
    10: u'<u2',  # 2 byte integer unsigned
    11: u'<u4',  # 4 byte integer unsigned
    12: u'<f8',  # 8 byte real
    13: u'<c16',  # byte complex
    14: u'bool',  # 1 byte binary (ie 0 or 1)
    23: np.dtype([(u'R', u'u1'), (u'G', u'u1'), (u'B', u'u1'), (u'A', u'u1')]),
}

dm4_data_types = {
    1: u'<i2',  # 2 byte integer signed ("short")
    2: u'<f4',  # 4 byte real (IEEE 754)
    3: u'<c8',  # 8 byte complex
    5: u'<c8',  # 8 byte complex (packed)
    6: u'<u1',  # 1 byte integer unsigned ("byte")
    7: u'<i4',  # 4 byte integer signed ("long")
    8: np.dtype([(u'R', u'u1'), (u'G', u'u1'), (u'B', u'u1'), (u'A', u'u1')]),
    9: u'<i1',  # byte integer signed
    10: u'<u2',  # 2 byte integer unsigned
    11: u'<u4',  # 4 byte integer unsigned
    12: u'<f8',  # 8 byte real
    13: u'<c16',  # byte complex
    14: u'bool',  # 1 byte binary (ie 0 or 1)
    23: np.dtype([(u'R', u'u1'), (u'G', u'u1'), (u'B', u'u1'), (u'A', u'u1')]),
    27: u'complex64',  # not numpy: 8-Byte packed complex (FFT data)
    28: u'complex128',  # not numpy: 16-Byte packed complex (FFT data)
}


def generate_1D_files(f, data_types, dmversion):
    for key in data_types.keys():
        f.write(
            u'filename = "'
            u'dm%i_1D_data\\\\test-%i.dm%i"\n'
            u'im := NewImage("test", %i, 2)\n'
            u'im[0,1] = 1\n'
            u'im[1,2] = 2\n'
            u'im.SaveImage(filename)\n' % (dmversion, key, dmversion, key))


def generate_2D_files(f, data_types, dmversion):
    for key in data_types.keys():
        f.write(
            u'filename = "'
            u'dm%i_2D_data\\\\test-%i.dm%i"\n'
            u'im := NewImage("test", %i, 2, 2)\n'
            u'im[0,0,1,1] = 1\n'
            u'im[0,1,1,2] = 2\n'
            u'im[1,0,2,1] = 3\n'
            u'im[1,1,2,2] = 4\n'
            u'im.SaveImage(filename)\n' % (dmversion, key, dmversion, key))


def generate_3D_files(f, data_types, dmversion):
    for key in data_types.keys():
        f.write(
            u'filename = "'
            u'dm%i_3D_data\\\\test-%i.dm%i"\n'
            u'im := NewImage("test", %i, 2, 2,2)\n'
            u'im[0,0,0,1,1,1] = 1\n'
            u'im[1,0,0,2,1,1] = 2\n'
            u'im[0,1,0,1,2,1] = 3\n'
            u'im[1,1,0,2,2,1] = 4\n'
            u'im[0,0,1,1,1,2] = 5\n'
            u'im[1,0,1,2,1,2] = 6\n'
            u'im[0,1,1,1,2,2] = 7\n'
            u'im[1,1,1,2,2,2] = 8\n'
            u'im.SaveImage(filename)\n' % (dmversion, key, dmversion, key))


def generate_4D_files(f, data_types, dmversion):
    for key in data_types.keys():
        f.write(
            u'filename = "'
            u'dm%i_4D_data\\\\test-%i.dm%i"\n'
            u'im := NewImage("test", %i, 2,2,2,2)\n'
            u'im[0,0,0,0,1,1,1,1] = 1\n'
            u'im[1,0,0,0,2,1,1,1] = 2\n'
            u'im[0,1,0,0,1,2,1,1] = 3\n'
            u'im[1,1,0,0,2,2,1,1] = 4\n'
            u'im[0,0,1,0,1,1,2,1] = 5\n'
            u'im[1,0,1,0,2,1,2,1] = 6\n'
            u'im[0,1,1,0,1,2,2,1] = 7\n'
            u'im[1,1,1,0,2,2,2,1] = 8\n'
            u'im[0,0,0,1,1,1,1,2] = 9\n'
            u'im[1,0,0,1,2,1,1,2] = 10\n'
            u'im[0,1,0,1,1,2,1,2] = 11\n'
            u'im[1,1,0,1,2,2,1,2] = 12\n'
            u'im[0,0,1,1,1,1,2,2] = 13\n'
            u'im[1,0,1,1,2,1,2,2] = 14\n'
            u'im[0,1,1,1,1,2,2,2] = 15\n'
            u'im[1,1,1,1,2,2,2,2] = 16\n'
            u'im.SaveImage(filename)\n' % (dmversion, key, dmversion, key))

if __name__ == u'__main__':
    with open(u"generate_dm3_test_files.s", u"w") as f1, open(u"generate_dm4_test_files.s", u"w") as f2:
        f1.write(u'image im\nstring filename\n')
        f2.write(u'image im\nstring filename\n')
        for f, dmv, dt in izip(
                (f1, f2), (3, 4), (dm3_data_types, dm4_data_types)):
            generate_1D_files(f, dt, dmv)
            generate_2D_files(f, dt, dmv)
            generate_3D_files(f, dt, dmv)
            #generate_4D_files(f, dt, dmv)
