#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010 Stefano Mazzucco
#
# This file is part of dm3_data_plugin.
#
# dm3_data_plugin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# dm3_data_plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HyperSpy; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

# general functions for reading data from files

import struct

from hyperspy.exceptions import ByteOrderError

# Declare simple TagDataType structures for faster execution.
# The variables are named as following:
# Endianness_type
# Endianness = B (big) or L (little)
# type = (u)short, (u)long, float, double, bool (unsigned char),
# byte (signed char), char

B_short = struct.Struct(u'>h')
L_short = struct.Struct(u'<h')

B_ushort = struct.Struct(u'>H')
L_ushort = struct.Struct(u'<H')

B_long = struct.Struct(u'>l')
L_long = struct.Struct(u'<l')

B_ulong = struct.Struct(u'>L')
L_ulong = struct.Struct(u'<L')

B_float = struct.Struct(u'>f')
L_float = struct.Struct(u'<f')

B_double = struct.Struct(u'>d')
L_double = struct.Struct(u'<d')

B_bool = struct.Struct(u'>B')    # use unsigned char
L_bool = struct.Struct(u'<B')

B_byte = struct.Struct(u'>b')    # use signed char
L_byte = struct.Struct(u'<b')

B_char = struct.Struct(u'>c')
L_char = struct.Struct(u'<c')


def read_short(f, endian):
    u"""Read a 2-Byte integer from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(2)      # hexadecimal representation
        if endian == u'big':
            s = B_short
        elif endian == u'little':
            s = L_short
        return s.unpack(data)[0]  # struct.unpack returns a tuple


def read_ushort(f, endian):
    u"""Read a 2-Byte integer from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(2)
        if endian == u'big':
            s = B_ushort
        elif endian == u'little':
            s = L_ushort
        return s.unpack(data)[0]


def read_long(f, endian):
    u"""Read a 4-Byte integer from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(4)
        if endian == u'big':
            s = B_long
        elif endian == u'little':
            s = L_long
        return s.unpack(data)[0]


def read_ulong(f, endian):
    u"""Read a 4-Byte integer from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(4)
        if endian == u'big':
            s = B_ulong
        elif endian == u'little':
            s = L_ulong
        return s.unpack(data)[0]


def read_float(f, endian):
    u"""Read a 4-Byte floating point from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(4)
        if endian == u'big':
            s = B_float
        elif endian == u'little':
            s = L_float
        return s.unpack(data)[0]


def read_double(f, endian):
    u"""Read a 8-Byte floating point from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(8)
        if endian == u'big':
            s = B_double
        elif endian == u'little':
            s = L_double
        return s.unpack(data)[0]


def read_boolean(f, endian):
    u"""Read a 1-Byte charater from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(1)
        if endian == u'big':
            s = B_bool
        elif endian == u'little':
            s = L_bool
        return s.unpack(data)[0]


def read_byte(f, endian):
    u"""Read a 1-Byte charater from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(1)
        if endian == u'big':
            s = B_byte
        elif endian == u'little':
            s = L_byte
        return s.unpack(data)[0]


def read_char(f, endian):
    u"""Read a 1-Byte charater from file f
    with a given endianness (byte order).
    endian can be either 'big' or 'little'.
    """
    if (endian != u'little') and (endian != u'big'):
        print u'File address:', f.tell()
        raise ByteOrderError(endian)
    else:
        data = f.read(1)
        if endian == u'big':
            s = B_char
        elif endian == u'little':
            s = L_char
        return s.unpack(data)[0]
