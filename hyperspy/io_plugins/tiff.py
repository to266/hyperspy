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

from __future__ import with_statement
import os
import warnings

import traits.api as t
from hyperspy.misc import rgb_tools
from itertools import izip
try:
    from skimage.external.tifffile import imsave, TiffFile
except ImportError:
    with warnings.catch_warnings():
        warnings.simplefilter(u"ignore")
        from hyperspy.external.tifffile import imsave, TiffFile
    warnings.warn(
        u"Failed to import the optional scikit image package. "
        u"Loading of some compressed images will be slow.\n")


# Plugin characteristics
# ----------------------
format_name = u'TIFF'
description = (u'Import/Export standard image formats Christoph Gohlke\'s '
               u'tifffile library')
full_support = False
file_extensions = [u'tif', u'tiff']
default_extension = 0  # tif


# Writing features
writes = [(2, 0), (2, 1)]
# ----------------------

axes_label_codes = {
    u'X': u"width",
    u'Y': u"height",
    u'S': u"sample",
    u'P': u"plane",
    u'I': u"image series",
    u'Z': u"depth",
    u'C': u"color|em-wavelength|channel",
    u'E': u"ex-wavelength|lambda",
    u'T': u"time",
    u'R': u"region|tile",
    u'A': u"angle",
    u'F': u"phase",
    u'H': u"lifetime",
    u'L': u"exposure",
    u'V': u"event",
    u'Q': t.Undefined,
    u'_': t.Undefined}


def file_writer(filename, signal, **kwds):
    u"""Writes data to tif using Christoph Gohlke's tifffile library

        Parameters
        ----------
        filename: str
        signal: a Signal instance

    """
    data = signal.data
    if signal.is_rgbx is True:
        data = rgb_tools.rgbx2regular_array(data)
        photometric = u"rgb"
    else:
        photometric = u"minisblack"
    if description not in kwds:
        if signal.metadata.General.title:
            kwds[u'description'] = signal.metadata.General.title

    imsave(filename, data,
           software=u"hyperspy",
           photometric=photometric,
           **kwds)


def file_reader(filename, record_by=u'image', **kwds):
    u"""Read data from tif files using Christoph Gohlke's tifffile
    library

    Parameters
    ----------
    filename: str
    record_by: {'image'}
        Has no effect because this format only supports recording by
        image.

    """
    with TiffFile(filename, **kwds) as tiff:
        dc = tiff.asarray()
        axes = tiff.series[0][u'axes']
        if tiff.is_rgb:
            dc = rgb_tools.regular_array2rgbx(dc)
            axes = axes[:-1]
        op = {}
        names = [axes_label_codes[axis] for axis in axes]
        axes = [{u'size': size,
                 u'name': unicode(name),
                 #'scale': scales[i],
                 #'offset' : origins[i],
                 #'units' : unicode(units[i]),
                 }
                for size, name in izip(dc.shape, names)]
        op = {}
        for key, tag in tiff[0].tags.items():
            op[key] = tag.value
    return [
        {
            u'data': dc,
            u'original_metadata': op,
            u'metadata': {
                u'General': {
                    u'original_filename': os.path.split(filename)[1]},
                u"Signal": {
                    u'signal_type': u"",
                    u'record_by': u"image",
                },
            },
        }]
