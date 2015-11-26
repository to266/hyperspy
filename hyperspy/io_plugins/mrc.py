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

# The details of the format were taken from
# http://www.biochem.mpg.de/doc_tom/TOM_Release_2008/IOfun/tom_mrcread.html
# and http://ami.scripps.edu/software/mrctools/mrc_specification.php

from __future__ import division
import os

import numpy as np
from traits.api import Undefined

from hyperspy.misc.array_tools import sarray2dict
from io import open


# Plugin characteristics
# ----------------------
format_name = u'MRC'
description = u''
full_support = False
# Recognised file extension
file_extensions = [u'mrc', u'MRC', u'ALI', u'ali']
default_extension = 0

# Writing capabilities
writes = False


def get_std_dtype_list(endianess=u'<'):
    end = endianess
    dtype_list = \
        [
            (u'NX', end + u'u4'),
            (u'NY', end + u'u4'),
            (u'NZ', end + u'u4'),
            (u'MODE', end + u'u4'),
            (u'NXSTART', end + u'u4'),
            (u'NYSTART', end + u'u4'),
            (u'NZSTART', end + u'u4'),
            (u'MX', end + u'u4'),
            (u'MY', end + u'u4'),
            (u'MZ', end + u'u4'),
            (u'Xlen', end + u'f4'),
            (u'Ylen', end + u'f4'),
            (u'Zlen', end + u'f4'),
            (u'ALPHA', end + u'f4'),
            (u'BETA', end + u'f4'),
            (u'GAMMA', end + u'f4'),
            (u'MAPC', end + u'u4'),
            (u'MAPR', end + u'u4'),
            (u'MAPS', end + u'u4'),
            (u'AMIN', end + u'f4'),
            (u'AMAX', end + u'f4'),
            (u'AMEAN', end + u'f4'),
            (u'ISPG', end + u'u2'),
            (u'NSYMBT', end + u'u2'),
            (u'NEXT', end + u'u4'),
            (u'CREATID', end + u'u2'),
            (u'EXTRA', (np.void, 30)),
            (u'NINT', end + u'u2'),
            (u'NREAL', end + u'u2'),
            (u'EXTRA2', (np.void, 28)),
            (u'IDTYPE', end + u'u2'),
            (u'LENS', end + u'u2'),
            (u'ND1', end + u'u2'),
            (u'ND2', end + u'u2'),
            (u'VD1', end + u'u2'),
            (u'VD2', end + u'u2'),
            (u'TILTANGLES', (np.float32, 6)),
            (u'XORIGIN', end + u'f4'),
            (u'YORIGIN', end + u'f4'),
            (u'ZORIGIN', end + u'f4'),
            (u'CMAP', (unicode, 4)),
            (u'STAMP', (unicode, 4)),
            (u'RMS', end + u'f4'),
            (u'NLABL', end + u'u4'),
            (u'LABELS', (unicode, 800)),
        ]

    return dtype_list


def get_fei_dtype_list(endianess=u'<'):
    end = endianess
    dtype_list = [
        (u'a_tilt', end + u'f4'),  # Alpha tilt (deg)
        (u'b_tilt', end + u'f4'),  # Beta tilt (deg)
        # Stage x position (Unit=m. But if value>1, unit=???m)
        (u'x_stage', end + u'f4'),
        # Stage y position (Unit=m. But if value>1, unit=???m)
        (u'y_stage', end + u'f4'),
        # Stage z position (Unit=m. But if value>1, unit=???m)
        (u'z_stage', end + u'f4'),
        # Image shift x (Unit=m. But if value>1, unit=???m)
        (u'x_shift', end + u'f4'),
        # Image shift y (Unit=m. But if value>1, unit=???m)
        (u'y_shift', end + u'f4'),
        (u'defocus', end + u'f4'),  # Defocus Unit=m. But if value>1, unit=???m)
        (u'exp_time', end + u'f4'),  # Exposure time (s)
        (u'mean_int', end + u'f4'),  # Mean value of image
        (u'tilt_axis', end + u'f4'),  # Tilt axis (deg)
        (u'pixel_size', end + u'f4'),  # Pixel size of image (m)
        (u'magnification', end + u'f4'),  # Magnification used
        # Not used (filling up to 128 bytes)
        (u'empty', (np.void, 128 - 13 * 4)),
    ]
    return dtype_list


def get_data_type(index, endianess=u'<'):
    end = endianess
    data_type = [
        end + u'u2',         # 0 = Image     unsigned bytes
        end + u'i2',         # 1 = Image     signed short integer (16 bits)
        end + u'f4',         # 2 = Image     float
        (end + u'i2', 2),    # 3 = Complex   short*2
        end + u'c8',         # 4 = Complex   float*2
    ]
    return data_type[index]


def file_reader(filename, endianess=u'<', **kwds):
    metadata = {}
    f = open(filename, u'rb')
    std_header = np.fromfile(f, dtype=get_std_dtype_list(endianess),
                             count=1)
    fei_header = None
    if std_header[u'NEXT'] / 1024 == 128:
        print u"It seems to contain an extended FEI header"
        fei_header = np.fromfile(f, dtype=get_fei_dtype_list(endianess),
                                 count=1024)
    if f.tell() == 1024 + std_header[u'NEXT']:
        print u"The FEI header was correctly loaded"
    else:
        print u"There was a problem reading the extended header"
        f.seek(1024 + std_header[u'NEXT'])
        fei_header = None
    NX, NY, NZ = std_header[u'NX'], std_header[u'NY'], std_header[u'NZ']
    data = np.memmap(f, mode=u'c', offset=f.tell(),
                     dtype=get_data_type(std_header[u'MODE'], endianess)
                     ).squeeze().reshape((NX, NY, NZ), order=u'F').T

    original_metadata = {u'std_header': sarray2dict(std_header)}
    if fei_header is not None:
        fei_dict = sarray2dict(fei_header,)
        del fei_dict[u'empty']
        original_metadata[u'fei_header'] = fei_dict

    dim = len(data.shape)
    if fei_header is None:
        # The scale is in Amstrongs, we convert it to nm
        scales = [10 * float(std_header[u'Zlen'] / std_header[u'MZ'])
                  if float(std_header[u'MZ']) != 0 else 1,
                  10 * float(std_header[u'Ylen'] / std_header[u'MY'])
                  if float(std_header[u'MY']) != 0 else 1,
                  10 * float(std_header[u'Xlen'] / std_header[u'MX'])
                  if float(std_header[u'MX']) != 0 else 1, ]
        offsets = [10 * float(std_header[u'ZORIGIN']),
                   10 * float(std_header[u'YORIGIN']),
                   10 * float(std_header[u'XORIGIN']), ]

    else:
        # FEI does not use the standard header to store the scale
        # It does store the spatial scale in pixel_size, one per angle in
        # meters
        scales = [1, ] + [fei_header[u'pixel_size'][0] * 10 ** 9, ] * 2
        offsets = [0, ] * 3

    units = [Undefined, u'nm', u'nm']
    names = [u'z', u'y', u'x']
    metadata = {u'General': {u'original_filename': os.path.split(filename)[1]},
                u"Signal": {u'signal_type': u"",
                           u'record_by': u'image', },
                }
    # create the axis objects for each axis
    axes = [
        {
            u'size': data.shape[i],
            u'index_in_array': i,
            u'name': names[i + 3 - dim],
            u'scale': scales[i + 3 - dim],
            u'offset': offsets[i + 3 - dim],
            u'units': units[i + 3 - dim], }
        for i in xrange(dim)]

    dictionary = {u'data': data,
                  u'axes': axes,
                  u'metadata': metadata,
                  u'original_metadata': original_metadata, }

    return [dictionary, ]
