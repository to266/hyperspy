

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tifffile.py

# Copyright (c) 2008-2014, Christoph Gohlke
# Copyright (c) 2008-2014, The Regents of the University of California
# Produced at the Laboratory for Fluorescence Dynamics
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

u"""Read and write image data from and to TIFF files.

Image and metadata can be read from TIFF, BigTIFF, OME-TIFF, STK, LSM, NIH,
SGI, ImageJ, MicroManager, FluoView, SEQ and GEL files.
Only a subset of the TIFF specification is supported, mainly uncompressed
and losslessly compressed 2**(0 to 6) bit integer, 16, 32 and 64-bit float,
grayscale and RGB(A) images, which are commonly used in bio-scientific imaging.
Specifically, reading JPEG and CCITT compressed image data or EXIF, IPTC, GPS,
and XMP metadata is not implemented.
Only primary info records are read for STK, FluoView, MicroManager, and
NIH image formats.

TIFF, the Tagged Image File Format, is under the control of Adobe Systems.
BigTIFF allows for files greater than 4 GB. STK, LSM, FluoView, SGI, SEQ, GEL,
and OME-TIFF, are custom extensions defined by Molecular Devices (Universal
Imaging Corporation), Carl Zeiss MicroImaging, Olympus, Silicon Graphics
International, Media Cybernetics, Molecular Dynamics, and the Open Microscopy
Environment consortium respectively.

For command line usage run ``python tifffile.py --help``

:Author:
  `Christoph Gohlke <http://www.lfd.uci.edu/~gohlke/>`_

:Organization:
  Laboratory for Fluorescence Dynamics, University of California, Irvine

:Version: 2014.08.24

Requirements
------------
* `CPython 2.7 or 3.4 <http://www.python.org>`_
* `Numpy 1.8.2 <http://www.numpy.org>`_
* `Matplotlib 1.4 <http://www.matplotlib.org>`_ (optional for plotting)
* `Tifffile.c 2013.11.05 <http://www.lfd.uci.edu/~gohlke/>`_
  (recommended for faster decoding of PackBits and LZW encoded strings)

Notes
-----
The API is not stable yet and might change between revisions.

Tested on little-endian platforms only.

Other Python packages and modules for reading bio-scientific TIFF files:

*  `Imread <http://luispedro.org/software/imread>`_
*  `PyLibTiff <http://code.google.com/p/pylibtiff>`_
*  `SimpleITK <http://www.simpleitk.org>`_
*  `PyLSM <https://launchpad.net/pylsm>`_
*  `PyMca.TiffIO.py <http://pymca.sourceforge.net/>`_ (same as fabio.TiffIO)
*  `BioImageXD.Readers <http://www.bioimagexd.net/>`_
*  `Cellcognition.io <http://cellcognition.org/>`_
*  `CellProfiler.bioformats
   <https://github.com/CellProfiler/python-bioformats>`_

Acknowledgements
----------------
*   Egor Zindy, University of Manchester, for cz_lsm_scan_info specifics.
*   Wim Lewis for a bug fix and some read_cz_lsm functions.
*   Hadrien Mary for help on reading MicroManager files.

References
----------
(1)  TIFF 6.0 Specification and Supplements. Adobe Systems Incorporated.
     http://partners.adobe.com/public/developer/tiff/
(2)  TIFF File Format FAQ. http://www.awaresystems.be/imaging/tiff/faq.html
(3)  MetaMorph Stack (STK) Image File Format.
     http://support.meta.moleculardevices.com/docs/t10243.pdf
(4)  Image File Format Description LSM 5/7 Release 6.0 (ZEN 2010).
     Carl Zeiss MicroImaging GmbH. BioSciences. May 10, 2011
(5)  File Format Description - LSM 5xx Release 2.0.
     http://ibb.gsf.de/homepage/karsten.rodenacker/IDL/Lsmfile.doc
(6)  The OME-TIFF format.
     http://www.openmicroscopy.org/site/support/file-formats/ome-tiff
(7)  UltraQuant(r) Version 6.0 for Windows Start-Up Guide.
     http://www.ultralum.com/images%20ultralum/pdf/UQStart%20Up%20Guide.pdf
(8)  Micro-Manager File Formats.
     http://www.micro-manager.org/wiki/Micro-Manager_File_Formats
(9)  Tags for TIFF and Related Specifications. Digital Preservation.
     http://www.digitalpreservation.gov/formats/content/tiff_tags.shtml

Examples
--------
>>> data = numpy.random.rand(5, 301, 219)
>>> imsave('temp.tif', data)

>>> image = imread('temp.tif')
>>> numpy.testing.assert_array_equal(image, data)

>>> with TiffFile('temp.tif') as tif:
...     images = tif.asarray()
...     for page in tif:
...         for tag in page.tags.values():
...             t = tag.name, tag.value
...         image = page.asarray()

"""



from __future__ import division
from __future__ import with_statement
import sys
import os
import re
import glob
import math
import zlib
import time
import json
import struct
import warnings
import tempfile
import datetime
import collections
from fractions import Fraction
from xml.etree import cElementTree as etree

import numpy
from io import open
from itertools import izip

try:
    import _tifffile
except ImportError:
    warnings.warn(
        u"failed to import the optional _tifffile C extension module.\n"
        u"Loading of some compressed images will be slow.\n"
        u"Tifffile.c can be obtained at http://www.lfd.uci.edu/~gohlke/")

__version__ = u'2014.08.24'
__docformat__ = u'restructuredtext en'
__all__ = (u'imsave', u'imread', u'imshow', u'TiffFile', u'TiffWriter',
           u'TiffSequence')


def imsave(filename, data, **kwargs):
    u"""Write image data to TIFF file.

    Refer to the TiffWriter class and member functions for documentation.

    Parameters
    ----------
    filename : str
        Name of file to write.
    data : array_like
        Input image. The last dimensions are assumed to be image depth,
        height, width, and samples.
    kwargs : dict
        Parameters 'byteorder', 'bigtiff', and 'software' are passed to
        the TiffWriter class.
        Parameters 'photometric', 'planarconfig', 'resolution',
        'description', 'compress', 'volume', and 'extratags' are passed to
        the TiffWriter.save function.

    Examples
    --------
    >>> data = numpy.random.rand(2, 5, 3, 301, 219)
    >>> description = u'{"shape": %s}' % str(list(data.shape))
    >>> imsave('temp.tif', data, compress=6,
    ...        extratags=[(270, 's', 0, description, True)])

    """
    tifargs = {}
    for key in (u'byteorder', u'bigtiff', u'software', u'writeshape'):
        if key in kwargs:
            tifargs[key] = kwargs[key]
            del kwargs[key]

    if u'writeshape' not in kwargs:
        kwargs[u'writeshape'] = True
    if u'bigtiff' not in tifargs and data.size * \
            data.dtype.itemsize > 2000 * 2**20:
        tifargs[u'bigtiff'] = True

    with TiffWriter(filename, **tifargs) as tif:
        tif.save(data, **kwargs)


class TiffWriter(object):

    u"""Write image data to TIFF file.

    TiffWriter instances must be closed using the close method, which is
    automatically called when using the 'with' statement.

    Examples
    --------
    >>> data = numpy.random.rand(2, 5, 3, 301, 219)
    >>> with TiffWriter('temp.tif', bigtiff=True) as tif:
    ...     for i in range(data.shape[0]):
    ...         tif.save(data[i], compress=6)

    """
    TYPES = {u'B': 1, u's': 2, u'H': 3, u'I': 4, u'2I': 5, u'b': 6,
             u'h': 8, u'i': 9, u'f': 11, u'd': 12, u'Q': 16, u'q': 17}
    TAGS = {
        u'new_subfile_type': 254, u'subfile_type': 255,
        u'image_width': 256, u'image_length': 257, u'bits_per_sample': 258,
        u'compression': 259, u'photometric': 262, u'fill_order': 266,
        u'document_name': 269, u'image_description': 270, u'strip_offsets': 273,
        u'orientation': 274, u'samples_per_pixel': 277, u'rows_per_strip': 278,
        u'strip_byte_counts': 279, u'x_resolution': 282, u'y_resolution': 283,
        u'planar_configuration': 284, u'page_name': 285, u'resolution_unit': 296,
        u'software': 305, u'datetime': 306, u'predictor': 317, u'color_map': 320,
        u'tile_width': 322, u'tile_length': 323, u'tile_offsets': 324,
        u'tile_byte_counts': 325, u'extra_samples': 338, u'sample_format': 339,
        u'image_depth': 32997, u'tile_depth': 32998}

    def __init__(self, filename, bigtiff=False, byteorder=None,
                 software=u'tifffile.py'):
        u"""Create a new TIFF file for writing.

        Use bigtiff=True when creating files greater than 2 GB.

        Parameters
        ----------
        filename : str
            Name of file to write.
        bigtiff : bool
            If True, the BigTIFF format is used.
        byteorder : {'<', '>'}
            The endianness of the data in the file.
            By default this is the system's native byte order.
        software : str
            Name of the software used to create the image.
            Saved with the first page only.

        """
        if byteorder not in (None, u'<', u'>'):
            raise ValueError(u"invalid byteorder %s" % byteorder)
        if byteorder is None:
            byteorder = u'<' if sys.byteorder == u'little' else u'>'

        self._byteorder = byteorder
        self._software = software

        self._fh = open(filename, u'wb')
        self._fh.write({u'<': 'II', u'>': 'MM'}[byteorder])

        if bigtiff:
            self._bigtiff = True
            self._offset_size = 8
            self._tag_size = 20
            self._numtag_format = u'Q'
            self._offset_format = u'Q'
            self._val_format = u'8s'
            self._fh.write(struct.pack(byteorder + u'HHH', 43, 8, 0))
        else:
            self._bigtiff = False
            self._offset_size = 4
            self._tag_size = 12
            self._numtag_format = u'H'
            self._offset_format = u'I'
            self._val_format = u'4s'
            self._fh.write(struct.pack(byteorder + u'H', 42))

        # first IFD
        self._ifd_offset = self._fh.tell()
        self._fh.write(struct.pack(byteorder + self._offset_format, 0))

    def save(self, data, photometric=None, planarconfig=None, resolution=None,
             description=None, volume=False, writeshape=False, compress=0,
             extratags=()):
        u"""Write image data to TIFF file.

        Image data are written in one stripe per plane.
        Dimensions larger than 2 to 4 (depending on photometric mode, planar
        configuration, and SGI mode) are flattened and saved as separate pages.
        The 'sample_format' and 'bits_per_sample' TIFF tags are derived from
        the data type.

        Parameters
        ----------
        data : array_like
            Input image. The last dimensions are assumed to be image depth,
            height, width, and samples.
        photometric : {'minisblack', 'miniswhite', 'rgb'}
            The color space of the image data.
            By default this setting is inferred from the data shape.
        planarconfig : {'contig', 'planar'}
            Specifies if samples are stored contiguous or in separate planes.
            By default this setting is inferred from the data shape.
            'contig': last dimension contains samples.
            'planar': third last dimension contains samples.
        resolution : (float, float) or ((int, int), (int, int))
            X and Y resolution in dots per inch as float or rational numbers.
        description : str
            The subject of the image. Saved with the first page only.
        compress : int
            Values from 0 to 9 controlling the level of zlib compression.
            If 0, data are written uncompressed (default).
        volume : bool
            If True, volume data are stored in one tile (if applicable) using
            the SGI image_depth and tile_depth tags.
            Image width and depth must be multiple of 16.
            Few software can read this format, e.g. MeVisLab.
        writeshape : bool
            If True, write the data shape to the image_description tag
            if necessary and no other description is given.
        extratags: sequence of tuples
            Additional tags as [(code, dtype, count, value, writeonce)].

            code : int
                The TIFF tag Id.
            dtype : str
                Data type of items in 'value' in Python struct format.
                One of B, s, H, I, 2I, b, h, i, f, d, Q, or q.
            count : int
                Number of data values. Not used for string values.
            value : sequence
                'Count' values compatible with 'dtype'.
            writeonce : bool
                If True, the tag is written to the first page only.

        """
        if photometric not in (None, u'minisblack', u'miniswhite', u'rgb'):
            raise ValueError(u"invalid photometric %s" % photometric)
        if planarconfig not in (None, u'contig', u'planar'):
            raise ValueError(u"invalid planarconfig %s" % planarconfig)
        if not 0 <= compress <= 9:
            raise ValueError(u"invalid compression level %s" % compress)

        fh = self._fh
        byteorder = self._byteorder
        numtag_format = self._numtag_format
        val_format = self._val_format
        offset_format = self._offset_format
        offset_size = self._offset_size
        tag_size = self._tag_size

        data = numpy.asarray(
            data,
            dtype=byteorder +
            data.dtype.char,
            order=u'C')
        data_shape = shape = data.shape
        data = numpy.atleast_2d(data)

        # normalize shape of data
        samplesperpixel = 1
        extrasamples = 0
        if volume and data.ndim < 3:
            volume = False
        if photometric is None:
            if planarconfig:
                photometric = u'rgb'
            elif data.ndim > 2 and shape[-1] in (3, 4):
                photometric = u'rgb'
            elif volume and data.ndim > 3 and shape[-4] in (3, 4):
                photometric = u'rgb'
            elif data.ndim > 2 and shape[-3] in (3, 4):
                photometric = u'rgb'
            else:
                photometric = u'minisblack'
        if planarconfig and len(shape) <= (3 if volume else 2):
            planarconfig = None
            photometric = u'minisblack'
        if photometric == u'rgb':
            if len(shape) < 3:
                raise ValueError(u"not a RGB(A) image")
            if len(shape) < 4:
                volume = False
            if planarconfig is None:
                if shape[-1] in (3, 4):
                    planarconfig = u'contig'
                elif shape[-4 if volume else -3] in (3, 4):
                    planarconfig = u'planar'
                elif shape[-1] > shape[-4 if volume else -3]:
                    planarconfig = u'planar'
                else:
                    planarconfig = u'contig'
            if planarconfig == u'contig':
                data = data.reshape((-1, 1) + shape[(-4 if volume else -3):])
                samplesperpixel = data.shape[-1]
            else:
                data = data.reshape(
                    (-1,) + shape[(-4 if volume else -3):] + (1,))
                samplesperpixel = data.shape[1]
            if samplesperpixel > 3:
                extrasamples = samplesperpixel - 3
        elif planarconfig and len(shape) > (3 if volume else 2):
            if planarconfig == u'contig':
                data = data.reshape((-1, 1) + shape[(-4 if volume else -3):])
                samplesperpixel = data.shape[-1]
            else:
                data = data.reshape(
                    (-1,) + shape[(-4 if volume else -3):] + (1,))
                samplesperpixel = data.shape[1]
            extrasamples = samplesperpixel - 1
        else:
            planarconfig = None
            # remove trailing 1s
            while len(shape) > 2 and shape[-1] == 1:
                shape = shape[:-1]
            if len(shape) < 3:
                volume = False
            if False and (
                    len(shape) > (3 if volume else 2) and shape[-1] < 5 and
                    all(shape[-1] < i
                        for i in shape[(-4 if volume else -3):-1])):
                # DISABLED: non-standard TIFF, e.g. (220, 320, 2)
                planarconfig = u'contig'
                samplesperpixel = shape[-1]
                data = data.reshape((-1, 1) + shape[(-4 if volume else -3):])
            else:
                data = data.reshape(
                    (-1, 1) + shape[(-3 if volume else -2):] + (1,))

        if samplesperpixel == 2:
            warnings.warn(u"writing non-standard TIFF (samplesperpixel 2)")

        if volume and (data.shape[-2] % 16 or data.shape[-3] % 16):
            warnings.warn(u"volume width or length are not multiple of 16")
            volume = False
            data = numpy.swapaxes(data, 1, 2)
            data = data.reshape(
                (data.shape[0] * data.shape[1],) + data.shape[2:])

        # data.shape is now normalized 5D or 6D, depending on volume
        # (pages, planar_samples, (depth,) height, width, contig_samples)
        assert len(data.shape) in (5, 6)
        shape = data.shape

        bytestr = str if sys.version[0] == u'2' else (
            lambda x: str(x) if isinstance(x, unicode) else x)
        tags = []  # list of (code, ifdentry, ifdvalue, writeonce)

        if volume:
            # use tiles to save volume data
            tag_byte_counts = TiffWriter.TAGS[u'tile_byte_counts']
            tag_offsets = TiffWriter.TAGS[u'tile_offsets']
        else:
            # else use strips
            tag_byte_counts = TiffWriter.TAGS[u'strip_byte_counts']
            tag_offsets = TiffWriter.TAGS[u'strip_offsets']

        def pack(fmt, *val):
            return struct.pack(byteorder + fmt, *val)

        def addtag(code, dtype, count, value, writeonce=False):
            # Compute ifdentry & ifdvalue bytes from code, dtype, count, value.
            # Append (code, ifdentry, ifdvalue, writeonce) to tags list.
            code = int(TiffWriter.TAGS.get(code, code))
            try:
                tifftype = TiffWriter.TYPES[dtype]
            except KeyError:
                raise ValueError(u"unknown dtype %s" % dtype)
            rawcount = count
            if dtype == u's':
                value = bytestr(value) + '\0'
                count = rawcount = len(value)
                value = (value, )
            if len(dtype) > 1:
                count *= int(dtype[:-1])
                dtype = dtype[-1]
            ifdentry = [pack(u'HH', code, tifftype),
                        pack(offset_format, rawcount)]
            ifdvalue = None
            if count == 1:
                if isinstance(value, (tuple, list)):
                    value = value[0]
                ifdentry.append(pack(val_format, pack(dtype, value)))
            elif struct.calcsize(dtype) * count <= offset_size:
                ifdentry.append(pack(val_format,
                                     pack(unicode(count) + dtype, *value)))
            else:
                ifdentry.append(pack(offset_format, 0))
                ifdvalue = pack(unicode(count) + dtype, *value)
            tags.append((code, ''.join(ifdentry), ifdvalue, writeonce))

        def rational(arg, max_denominator=1000000):
            # return nominator and denominator from float or two integers
            try:
                f = Fraction.from_float(arg)
            except TypeError:
                f = Fraction(arg[0], arg[1])
            f = f.limit_denominator(max_denominator)
            return f.numerator, f.denominator

        if self._software:
            addtag(u'software', u's', 0, self._software, writeonce=True)
            self._software = None  # only save to first page
        if description:
            addtag(u'image_description', u's', 0, description, writeonce=True)
        elif writeshape and shape[0] > 1 and shape != data_shape:
            addtag(u'image_description', u's', 0,
                   u"shape=(%s)" % (u",".join(u'%i' % i for i in data_shape)),
                   writeonce=True)
        addtag(u'datetime', u's', 0,
               datetime.datetime.now().strftime(u"%Y:%m:%d %H:%M:%S"),
               writeonce=True)
        addtag(u'compression', u'H', 1, 32946 if compress else 1)
        addtag(u'orientation', u'H', 1, 1)
        addtag(u'image_width', u'I', 1, shape[-2])
        addtag(u'image_length', u'I', 1, shape[-3])
        if volume:
            addtag(u'image_depth', u'I', 1, shape[-4])
            addtag(u'tile_depth', u'I', 1, shape[-4])
            addtag(u'tile_width', u'I', 1, shape[-2])
            addtag(u'tile_length', u'I', 1, shape[-3])
        addtag(u'new_subfile_type', u'I', 1, 0 if shape[0] == 1 else 2)
        addtag(u'sample_format', u'H', 1,
               {u'u': 1, u'i': 2, u'f': 3, u'c': 6}[data.dtype.kind])
        addtag(u'photometric', u'H', 1,
               {u'miniswhite': 0, u'minisblack': 1, u'rgb': 2}[photometric])
        addtag(u'samples_per_pixel', u'H', 1, samplesperpixel)
        if planarconfig and samplesperpixel > 1:
            addtag(u'planar_configuration', u'H', 1, 1
                   if planarconfig == u'contig' else 2)
            addtag(u'bits_per_sample', u'H', samplesperpixel,
                   (data.dtype.itemsize * 8, ) * samplesperpixel)
        else:
            addtag(u'bits_per_sample', u'H', 1, data.dtype.itemsize * 8)
        if extrasamples:
            if photometric == u'rgb' and extrasamples == 1:
                addtag(u'extra_samples', u'H', 1, 1)  # associated alpha channel
            else:
                addtag(u'extra_samples', u'H', extrasamples, (0,) * extrasamples)
        if resolution:
            addtag(u'x_resolution', u'2I', 1, rational(resolution[0]))
            addtag(u'y_resolution', u'2I', 1, rational(resolution[1]))
            addtag(u'resolution_unit', u'H', 1, 2)
        addtag(u'rows_per_strip', u'I', 1,
               shape[-3] * (shape[-4] if volume else 1))

        # use one strip or tile per plane
        strip_byte_counts = (data[0, 0].size * data.dtype.itemsize,) * shape[1]
        addtag(tag_byte_counts, offset_format, shape[1], strip_byte_counts)
        addtag(tag_offsets, offset_format, shape[1], (0, ) * shape[1])

        # add extra tags from users
        for t in extratags:
            addtag(*t)
        # the entries in an IFD must be sorted in ascending order by tag code
        tags = sorted(tags, key=lambda x: x[0])

        if not self._bigtiff and (fh.tell() + data.size * data.dtype.itemsize
                                  > 2**31 - 1):
            raise ValueError(u"data too large for non-bigtiff file")

        for pageindex in xrange(shape[0]):
            # update pointer at ifd_offset
            pos = fh.tell()
            fh.seek(self._ifd_offset)
            fh.write(pack(offset_format, pos))
            fh.seek(pos)

            # write ifdentries
            fh.write(pack(numtag_format, len(tags)))
            tag_offset = fh.tell()
            fh.write(''.join(t[1] for t in tags))
            self._ifd_offset = fh.tell()
            fh.write(pack(offset_format, 0))  # offset to next IFD

            # write tag values and patch offsets in ifdentries, if necessary
            for tagindex, tag in enumerate(tags):
                if tag[2]:
                    pos = fh.tell()
                    fh.seek(tag_offset + tagindex * tag_size + offset_size + 4)
                    fh.write(pack(offset_format, pos))
                    fh.seek(pos)
                    if tag[0] == tag_offsets:
                        strip_offsets_offset = pos
                    elif tag[0] == tag_byte_counts:
                        strip_byte_counts_offset = pos
                    fh.write(tag[2])

            # write image data
            data_offset = fh.tell()
            if compress:
                strip_byte_counts = []
                for plane in data[pageindex]:
                    plane = zlib.compress(plane, compress)
                    strip_byte_counts.append(len(plane))
                    fh.write(plane)
            else:
                # if this fails try update Python/numpy
                data[pageindex].tofile(fh)
                fh.flush()

            # update strip and tile offsets and byte_counts if necessary
            pos = fh.tell()
            for tagindex, tag in enumerate(tags):
                if tag[0] == tag_offsets:  # strip or tile offsets
                    if tag[2]:
                        fh.seek(strip_offsets_offset)
                        strip_offset = data_offset
                        for size in strip_byte_counts:
                            fh.write(pack(offset_format, strip_offset))
                            strip_offset += size
                    else:
                        fh.seek(tag_offset + tagindex * tag_size +
                                offset_size + 4)
                        fh.write(pack(offset_format, data_offset))
                elif tag[0] == tag_byte_counts:  # strip or tile byte_counts
                    if compress:
                        if tag[2]:
                            fh.seek(strip_byte_counts_offset)
                            for size in strip_byte_counts:
                                fh.write(pack(offset_format, size))
                        else:
                            fh.seek(tag_offset + tagindex * tag_size +
                                    offset_size + 4)
                            fh.write(pack(offset_format, strip_byte_counts[0]))
                    break
            fh.seek(pos)
            fh.flush()
            # remove tags that should be written only once
            if pageindex == 0:
                tags = [t for t in tags if not t[-1]]

    def close(self):
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def imread(files, **kwargs):
    u"""Return image data from TIFF file(s) as numpy array.

    The first image series is returned if no arguments are provided.

    Parameters
    ----------
    files : str or list
        File name, glob pattern, or list of file names.
    key : int, slice, or sequence of page indices
        Defines which pages to return as array.
    series : int
        Defines which series of pages in file to return as array.
    multifile : bool
        If True (default), OME-TIFF data may include pages from multiple files.
    pattern : str
        Regular expression pattern that matches axes names and indices in
        file names.
    kwargs : dict
        Additional parameters passed to the TiffFile or TiffSequence asarray
        function.

    Examples
    --------
    >>> im = imread('test.tif', key=0)
    >>> im.shape
    (256, 256, 4)
    >>> ims = imread(['test.tif', 'test.tif'])
    >>> ims.shape
    (2, 256, 256, 4)

    """
    kwargs_file = {}
    if u'multifile' in kwargs:
        kwargs_file[u'multifile'] = kwargs[u'multifile']
        del kwargs[u'multifile']
    else:
        kwargs_file[u'multifile'] = True
    kwargs_seq = {}
    if u'pattern' in kwargs:
        kwargs_seq[u'pattern'] = kwargs[u'pattern']
        del kwargs[u'pattern']

    if isinstance(files, unicode) and any(i in files for i in u'?*'):
        files = glob.glob(files)
    if not files:
        raise ValueError(u'no files found')
    if len(files) == 1:
        files = files[0]

    if isinstance(files, unicode):
        with TiffFile(files, **kwargs_file) as tif:
            return tif.asarray(**kwargs)
    else:
        with TiffSequence(files, **kwargs_seq) as imseq:
            return imseq.asarray(**kwargs)


class lazyattr(object):

    u"""Lazy object attribute whose value is computed on first access."""
    __slots__ = (u'func', )

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = self.func(instance)
        if value is NotImplemented:
            return getattr(super(owner, instance), self.func.__name__)
        setattr(instance, self.func.__name__, value)
        return value


class TiffFile(object):

    u"""Read image and metadata from TIFF, STK, LSM, and FluoView files.

    TiffFile instances must be closed using the close method, which is
    automatically called when using the 'with' statement.

    Attributes
    ----------
    pages : list
        All TIFF pages in file.
    series : list of Records(shape, dtype, axes, TiffPages)
        TIFF pages with compatible shapes and types.
    micromanager_metadata: dict
        Extra MicroManager non-TIFF metadata in the file, if exists.

    All attributes are read-only.

    Examples
    --------
    >>> with TiffFile('test.tif') as tif:
    ...     data = tif.asarray()
    ...     data.shape
    (256, 256, 4)

    """

    def __init__(self, arg, name=None, offset=None, size=None,
                 multifile=True, multifile_close=True):
        u"""Initialize instance from file.

        Parameters
        ----------
        arg : str or open file
            Name of file or open file object.
            The file objects are closed in TiffFile.close().
        name : str
            Optional name of file in case 'arg' is a file handle.
        offset : int
            Optional start position of embedded file. By default this is
            the current file position.
        size : int
            Optional size of embedded file. By default this is the number
            of bytes from the 'offset' to the end of the file.
        multifile : bool
            If True (default), series may include pages from multiple files.
            Currently applies to OME-TIFF only.
        multifile_close : bool
            If True (default), keep the handles of other files in multifile
            series closed. This is inefficient when few files refer to
            many pages. If False, the C runtime may run out of resources.

        """
        self._fh = FileHandle(arg, name=name, offset=offset, size=size)
        self.offset_size = None
        self.pages = []
        self._multifile = bool(multifile)
        self._multifile_close = bool(multifile_close)
        self._files = {self._fh.name: self}  # cache of TiffFiles
        try:
            self._fromfile()
        except Exception:
            self._fh.close()
            raise

    @property
    def filehandle(self):
        u"""Return file handle."""
        return self._fh

    @property
    def filename(self):
        u"""Return name of file handle."""
        return self._fh.name

    def close(self):
        u"""Close open file handle(s)."""
        for tif in self._files.values():
            tif._fh.close()
        self._files = {}

    def _fromfile(self):
        u"""Read TIFF header and all page records from file."""
        self._fh.seek(0)
        try:
            self.byteorder = {'II': u'<', 'MM': u'>'}[self._fh.read(2)]
        except KeyError:
            raise ValueError(u"not a valid TIFF file")
        version = struct.unpack(self.byteorder + u'H', self._fh.read(2))[0]
        if version == 43:  # BigTiff
            self.offset_size, zero = struct.unpack(self.byteorder + u'HH',
                                                   self._fh.read(4))
            if zero or self.offset_size != 8:
                raise ValueError(u"not a valid BigTIFF file")
        elif version == 42:
            self.offset_size = 4
        else:
            raise ValueError(u"not a TIFF file")
        self.pages = []
        while True:
            try:
                page = TiffPage(self)
                self.pages.append(page)
            except StopIteration:
                break
        if not self.pages:
            raise ValueError(u"empty TIFF file")

        if self.is_micromanager:
            # MicroManager files contain metadata not stored in TIFF tags.
            self.micromanager_metadata = read_micromanager_metadata(self._fh)

        if self.is_lsm:
            self._fix_lsm_strip_offsets()
            self._fix_lsm_strip_byte_counts()

    def _fix_lsm_strip_offsets(self):
        u"""Unwrap strip offsets for LSM files greater than 4 GB."""
        for series in self.series:
            wrap = 0
            previous_offset = 0
            for page in series.pages:
                strip_offsets = []
                for current_offset in page.strip_offsets:
                    if current_offset < previous_offset:
                        wrap += 2**32
                    strip_offsets.append(current_offset + wrap)
                    previous_offset = current_offset
                page.strip_offsets = tuple(strip_offsets)

    def _fix_lsm_strip_byte_counts(self):
        u"""Set strip_byte_counts to size of compressed data.

        The strip_byte_counts tag in LSM files contains the number of bytes
        for the uncompressed data.

        """
        if not self.pages:
            return
        strips = {}
        for page in self.pages:
            assert len(page.strip_offsets) == len(page.strip_byte_counts)
            for offset, bytecount in izip(page.strip_offsets,
                                         page.strip_byte_counts):
                strips[offset] = bytecount
        offsets = sorted(strips.keys())
        offsets.append(min(offsets[-1] + strips[offsets[-1]], self._fh.size))
        for i, offset in enumerate(offsets[:-1]):
            strips[offset] = min(strips[offset], offsets[i + 1] - offset)
        for page in self.pages:
            if page.compression:
                page.strip_byte_counts = tuple(
                    strips[offset] for offset in page.strip_offsets)

    @lazyattr
    def series(self):
        u"""Return series of TiffPage with compatible shape and properties."""
        if not self.pages:
            return []

        series = []
        page0 = self.pages[0]

        if self.is_ome:
            series = self._omeseries()
        elif self.is_fluoview:
            dims = {'X': u'X', 'Y': u'Y', 'Z': u'Z', 'T': u'T',
                    'WAVELENGTH': u'C', 'TIME': u'T', 'XY': u'R',
                    'EVENT': u'V', 'EXPOSURE': u'L'}
            mmhd = list(reversed(page0.mm_header.dimensions))
            series = [Record(
                axes=u''.join(dims.get(i[0].strip().upper(), u'Q')
                             for i in mmhd if i[1] > 1),
                shape=tuple(int(i[1]) for i in mmhd if i[1] > 1),
                pages=self.pages, dtype=numpy.dtype(page0.dtype))]
        elif self.is_lsm:
            lsmi = page0.cz_lsm_info
            axes = CZ_SCAN_TYPES[lsmi.scan_type]
            if page0.is_rgb:
                axes = axes.replace(u'C', u'').replace(u'XY', u'XYC')
            axes = axes[::-1]
            shape = tuple(getattr(lsmi, CZ_DIMENSIONS[i]) for i in axes)
            pages = [p for p in self.pages if not p.is_reduced]
            series = [Record(axes=axes, shape=shape, pages=pages,
                             dtype=numpy.dtype(pages[0].dtype))]
            if len(pages) != len(self.pages):  # reduced RGB pages
                pages = [p for p in self.pages if p.is_reduced]
                cp = 1
                i = 0
                while cp < len(pages) and i < len(shape) - 2:
                    cp *= shape[i]
                    i += 1
                shape = shape[:i] + pages[0].shape
                axes = axes[:i] + u'CYX'
                series.append(Record(axes=axes, shape=shape, pages=pages,
                                     dtype=numpy.dtype(pages[0].dtype)))
        elif self.is_imagej:
            shape = []
            axes = []
            ij = page0.imagej_tags
            if u'frames' in ij:
                shape.append(ij[u'frames'])
                axes.append(u'T')
            if u'slices' in ij:
                shape.append(ij[u'slices'])
                axes.append(u'Z')
            if u'channels' in ij and not self.is_rgb:
                shape.append(ij[u'channels'])
                axes.append(u'C')
            remain = len(self.pages) // (product(shape) if shape else 1)
            if remain > 1:
                shape.append(remain)
                axes.append(u'I')
            shape.extend(page0.shape)
            axes.extend(page0.axes)
            axes = u''.join(axes)
            series = [Record(pages=self.pages, shape=tuple(shape), axes=axes,
                             dtype=numpy.dtype(page0.dtype))]
        elif self.is_nih:
            if len(self.pages) == 1:
                shape = page0.shape
                axes = page0.axes
            else:
                shape = (len(self.pages),) + page0.shape
                axes = u'I' + page0.axes
            series = [Record(pages=self.pages, shape=shape, axes=axes,
                             dtype=numpy.dtype(page0.dtype))]
        elif page0.is_shaped:
            # TODO: shaped files can contain multiple series
            shape = page0.tags[u'image_description'].value[7:-1]
            shape = tuple(int(i) for i in shape.split(','))
            series = [Record(pages=self.pages, shape=shape,
                             axes=u'Q' * len(shape),
                             dtype=numpy.dtype(page0.dtype))]

        # generic detection of series
        if not series:
            shapes = []
            pages = {}
            for page in self.pages:
                if not page.shape:
                    continue
                shape = page.shape + (page.axes,
                                      page.compression in TIFF_DECOMPESSORS)
                if shape not in pages:
                    shapes.append(shape)
                    pages[shape] = [page]
                else:
                    pages[shape].append(page)
            series = [Record(pages=pages[s],
                             axes=((u'I' + s[-2])
                                   if len(pages[s]) > 1 else s[-2]),
                             dtype=numpy.dtype(pages[s][0].dtype),
                             shape=((len(pages[s]), ) + s[:-2]
                                    if len(pages[s]) > 1 else s[:-2]))
                      for s in shapes]

        # remove empty series, e.g. in MD Gel files
        series = [s for s in series if sum(s.shape) > 0]

        return series

    def asarray(self, key=None, series=None, memmap=False):
        u"""Return image data from multiple TIFF pages as numpy array.

        By default the first image series is returned.

        Parameters
        ----------
        key : int, slice, or sequence of page indices
            Defines which pages to return as array.
        series : int
            Defines which series of pages to return as array.
        memmap : bool
            If True, return an array stored in a binary file on disk
            if possible.

        """
        if key is None and series is None:
            series = 0
        if series is not None:
            pages = self.series[series].pages
        else:
            pages = self.pages

        if key is None:
            pass
        elif isinstance(key, int):
            pages = [pages[key]]
        elif isinstance(key, slice):
            pages = pages[key]
        elif isinstance(key, collections.Iterable):
            pages = [pages[k] for k in key]
        else:
            raise TypeError(u"key must be an int, slice, or sequence")

        if not len(pages):
            raise ValueError(u"no pages selected")

        if self.is_nih:
            if pages[0].is_palette:
                result = stack_pages(pages, colormapped=False, squeeze=False)
                result = numpy.take(pages[0].color_map, result, axis=1)
                result = numpy.swapaxes(result, 0, 1)
            else:
                result = stack_pages(pages, memmap=memmap,
                                     colormapped=False, squeeze=False)
        elif len(pages) == 1:
            return pages[0].asarray(memmap=memmap)
        elif self.is_ome:
            assert not self.is_palette, u"color mapping disabled for ome-tiff"
            if any(p is None for p in pages):
                # zero out missing pages
                firstpage = p for p in pages if p.next()
                nopage = numpy.zeros_like(
                    firstpage.asarray(memmap=False))
            s = self.series[series]
            if memmap:
                with tempfile.NamedTemporaryFile() as fh:
                    result = numpy.memmap(fh, dtype=s.dtype, shape=s.shape)
                    result = result.reshape(-1)
            else:
                result = numpy.empty(s.shape, s.dtype).reshape(-1)
            index = 0

            class KeepOpen(object):
                # keep Tiff files open between consecutive pages

                def __init__(self, parent, close):
                    self.master = parent
                    self.parent = parent
                    self._close = close

                def open(self, page):
                    if self._close and page and page.parent != self.parent:
                        if self.parent != self.master:
                            self.parent.filehandle.close()
                        self.parent = page.parent
                        self.parent.filehandle.open()

                def close(self):
                    if self._close and self.parent != self.master:
                        self.parent.filehandle.close()

            keep = KeepOpen(self, self._multifile_close)
            for page in pages:
                keep.open(page)
                if page:
                    a = page.asarray(memmap=False, colormapped=False,
                                     reopen=False)
                else:
                    a = nopage
                try:
                    result[index:index + a.size] = a.reshape(-1)
                except ValueError, e:
                    warnings.warn(u"ome-tiff: %s" % e)
                    break
                index += a.size
            keep.close()
        else:
            result = stack_pages(pages, memmap=memmap)

        if key is None:
            try:
                result.shape = self.series[series].shape
            except ValueError:
                try:
                    warnings.warn(u"failed to reshape %s to %s" % (
                                  result.shape, self.series[series].shape))
                    # try series of expected shapes
                    result.shape = (-1,) + self.series[series].shape
                except ValueError:
                    # revert to generic shape
                    result.shape = (-1,) + pages[0].shape
        else:
            result.shape = (-1,) + pages[0].shape
        return result

    def _omeseries(self):
        u"""Return image series in OME-TIFF file(s)."""
        root = etree.fromstring(self.pages[0].tags[u'image_description'].value)
        uuid = root.attrib.get(u'UUID', None)
        self._files = {uuid: self}
        dirname = self._fh.dirname
        modulo = {}
        result = []
        for element in root:
            if element.tag.endswith(u'BinaryOnly'):
                warnings.warn(u"ome-xml: not an ome-tiff master file")
                break
            if element.tag.endswith(u'StructuredAnnotations'):
                for annot in element:
                    if not annot.attrib.get(u'Namespace',
                                            u'').endswith(u'modulo'):
                        continue
                    for value in annot:
                        for modul in value:
                            for along in modul:
                                if not along.tag[:-1].endswith(u'Along'):
                                    continue
                                axis = along.tag[-1]
                                newaxis = along.attrib.get(u'Type', u'other')
                                newaxis = AXES_LABELS[newaxis]
                                if u'Start' in along.attrib:
                                    labels = xrange(
                                        int(along.attrib[u'Start']),
                                        int(along.attrib[u'End']) + 1,
                                        int(along.attrib.get(u'Step', 1)))
                                else:
                                    labels = [label.text for label in along
                                              if label.tag.endswith(u'Label')]
                                modulo[axis] = (newaxis, labels)
            if not element.tag.endswith(u'Image'):
                continue
            for pixels in element:
                if not pixels.tag.endswith(u'Pixels'):
                    continue
                atr = pixels.attrib
                dtype = atr.get(u'Type', None)
                axes = u''.join(reversed(atr[u'DimensionOrder']))
                shape = list(int(atr[u'Size' + ax]) for ax in axes)
                size = product(shape[:-2])
                ifds = [None] * size
                for data in pixels:
                    if not data.tag.endswith(u'TiffData'):
                        continue
                    atr = data.attrib
                    ifd = int(atr.get(u'IFD', 0))
                    num = int(atr.get(u'NumPlanes', 1 if u'IFD' in atr else 0))
                    num = int(atr.get(u'PlaneCount', num))
                    idx = [int(atr.get(u'First' + ax, 0)) for ax in axes[:-2]]
                    try:
                        idx = numpy.ravel_multi_index(idx, shape[:-2])
                    except ValueError:
                        # ImageJ produces invalid ome-xml when cropping
                        warnings.warn(u"ome-xml: invalid TiffData index")
                        continue
                    for uuid in data:
                        if not uuid.tag.endswith(u'UUID'):
                            continue
                        if uuid.text not in self._files:
                            if not self._multifile:
                                # abort reading multifile OME series
                                # and fall back to generic series
                                return []
                            fname = uuid.attrib[u'FileName']
                            try:
                                tif = TiffFile(os.path.join(dirname, fname))
                            except (IOError, ValueError):
                                tif.close()
                                warnings.warn(
                                    u"ome-xml: failed to read '%s'" % fname)
                                break
                            self._files[uuid.text] = tif
                            if self._multifile_close:
                                tif.close()
                        pages = self._files[uuid.text].pages
                        try:
                            for i in xrange(num if num else len(pages)):
                                ifds[idx + i] = pages[ifd + i]
                        except IndexError:
                            warnings.warn(u"ome-xml: index out of range")
                        # only process first uuid
                        break
                    else:
                        pages = self.pages
                        try:
                            for i in xrange(num if num else len(pages)):
                                ifds[idx + i] = pages[ifd + i]
                        except IndexError:
                            warnings.warn(u"ome-xml: index out of range")
                if all(i is None for i in ifds):
                    # skip images without data
                    continue
                dtype = i for i in ifds if i.next().dtype
                result.append(Record(axes=axes, shape=shape, pages=ifds,
                                     dtype=numpy.dtype(dtype)))

        for record in result:
            for axis, (newaxis, labels) in modulo.items():
                i = record.axes.index(axis)
                size = len(labels)
                if record.shape[i] == size:
                    record.axes = record.axes.replace(axis, newaxis, 1)
                else:
                    record.shape[i] //= size
                    record.shape.insert(i + 1, size)
                    record.axes = record.axes.replace(axis, axis + newaxis, 1)
            record.shape = tuple(record.shape)

        # squeeze dimensions
        for record in result:
            record.shape, record.axes = squeeze_axes(record.shape, record.axes)

        return result

    def __len__(self):
        u"""Return number of image pages in file."""
        return len(self.pages)

    def __getitem__(self, key):
        u"""Return specified page."""
        return self.pages[key]

    def __iter__(self):
        u"""Return iterator over pages."""
        return iter(self.pages)

    def __str__(self):
        u"""Return string containing information about file."""
        result = [
            self._fh.name.capitalize(),
            format_size(self._fh.size),
            {u'<': u'little endian', u'>': u'big endian'}[self.byteorder]]
        if self.is_bigtiff:
            result.append(u"bigtiff")
        if len(self.pages) > 1:
            result.append(u"%i pages" % len(self.pages))
        if len(self.series) > 1:
            result.append(u"%i series" % len(self.series))
        if len(self._files) > 1:
            result.append(u"%i files" % (len(self._files)))
        return u", ".join(result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @lazyattr
    def fstat(self):
        try:
            return os.fstat(self._fh.fileno())
        except Exception:  # io.UnsupportedOperation
            return None

    @lazyattr
    def is_bigtiff(self):
        return self.offset_size != 4

    @lazyattr
    def is_rgb(self):
        return all(p.is_rgb for p in self.pages)

    @lazyattr
    def is_palette(self):
        return all(p.is_palette for p in self.pages)

    @lazyattr
    def is_mdgel(self):
        return any(p.is_mdgel for p in self.pages)

    @lazyattr
    def is_mediacy(self):
        return any(p.is_mediacy for p in self.pages)

    @lazyattr
    def is_stk(self):
        return all(p.is_stk for p in self.pages)

    @lazyattr
    def is_lsm(self):
        return self.pages[0].is_lsm

    @lazyattr
    def is_imagej(self):
        return self.pages[0].is_imagej

    @lazyattr
    def is_micromanager(self):
        return self.pages[0].is_micromanager

    @lazyattr
    def is_nih(self):
        return self.pages[0].is_nih

    @lazyattr
    def is_fluoview(self):
        return self.pages[0].is_fluoview

    @lazyattr
    def is_ome(self):
        return self.pages[0].is_ome


class TiffPage(object):

    u"""A TIFF image file directory (IFD).

    Attributes
    ----------
    index : int
        Index of page in file.
    dtype : str {TIFF_SAMPLE_DTYPES}
        Data type of image, colormapped if applicable.
    shape : tuple
        Dimensions of the image array in TIFF page,
        colormapped and with one alpha channel if applicable.
    axes : str
        Axes label codes:
        'X' width, 'Y' height, 'S' sample, 'I' image series|page|plane,
        'Z' depth, 'C' color|em-wavelength|channel, 'E' ex-wavelength|lambda,
        'T' time, 'R' region|tile, 'A' angle, 'P' phase, 'H' lifetime,
        'L' exposure, 'V' event, 'Q' unknown, '_' missing
    tags : TiffTags
        Dictionary of tags in page.
        Tag values are also directly accessible as attributes.
    color_map : numpy array
        Color look up table, if exists.
    cz_lsm_scan_info: Record(dict)
        LSM scan info attributes, if exists.
    imagej_tags: Record(dict)
        Consolidated ImageJ description and metadata tags, if exists.
    uic_tags: Record(dict)
        Consolidated MetaMorph STK/UIC tags, if exists.

    All attributes are read-only.

    Notes
    -----
    The internal, normalized '_shape' attribute is 6 dimensional:

    0. number planes  (stk)
    1. planar samples_per_pixel
    2. image_depth Z  (sgi)
    3. image_length Y
    4. image_width X
    5. contig samples_per_pixel

    """

    def __init__(self, parent):
        u"""Initialize instance from file."""
        self.parent = parent
        self.index = len(parent.pages)
        self.shape = self._shape = ()
        self.dtype = self._dtype = None
        self.axes = u""
        self.tags = TiffTags()

        self._fromfile()
        self._process_tags()

    def _fromfile(self):
        u"""Read TIFF IFD structure and its tags from file.

        File cursor must be at storage position of IFD offset and is left at
        offset to next IFD.

        Raises StopIteration if offset (first bytes read) is 0.

        """
        fh = self.parent.filehandle
        byteorder = self.parent.byteorder
        offset_size = self.parent.offset_size

        fmt = {4: u'I', 8: u'Q'}[offset_size]
        offset = struct.unpack(byteorder + fmt, fh.read(offset_size))[0]
        if not offset:
            raise StopIteration()

        # read standard tags
        tags = self.tags
        fh.seek(offset)
        fmt, size = {4: (u'H', 2), 8: (u'Q', 8)}[offset_size]
        try:
            numtags = struct.unpack(byteorder + fmt, fh.read(size))[0]
        except Exception:
            warnings.warn(u"corrupted page list")
            raise StopIteration()

        tagcode = 0
        for _ in xrange(numtags):
            try:
                tag = TiffTag(self.parent)
                # print(tag)
            except TiffTag.Error, e:
                warnings.warn(unicode(e))
                continue
            if tagcode > tag.code:
                # expected for early LSM and tifffile versions
                warnings.warn(u"tags are not ordered by code")
            tagcode = tag.code
            if tag.name not in tags:
                tags[tag.name] = tag
            else:
                # some files contain multiple IFD with same code
                # e.g. MicroManager files contain two image_description
                i = 1
                while True:
                    name = u"%s_%i" % (tag.name, i)
                    if name not in tags:
                        tags[name] = tag
                        break

        pos = fh.tell()

        if self.is_lsm or (self.index and self.parent.is_lsm):
            # correct non standard LSM bitspersample tags
            self.tags[u'bits_per_sample']._correct_lsm_bitspersample(self)

        if self.is_lsm:
            # read LSM info subrecords
            for name, reader in CZ_LSM_INFO_READERS.items():
                try:
                    offset = self.cz_lsm_info[u'offset_' + name]
                except KeyError:
                    continue
                if offset < 8:
                    # older LSM revision
                    continue
                fh.seek(offset)
                try:
                    setattr(self, u'cz_lsm_' + name, reader(fh))
                except ValueError:
                    pass

        elif self.is_stk and u'uic1tag' in tags and not tags[u'uic1tag'].value:
            # read uic1tag now that plane count is known
            uic1tag = tags[u'uic1tag']
            fh.seek(uic1tag.value_offset)
            tags[u'uic1tag'].value = Record(
                read_uic1tag(fh, byteorder, uic1tag.dtype, uic1tag.count,
                             tags[u'uic2tag'].count))
        fh.seek(pos)

    def _process_tags(self):
        u"""Validate standard tags and initialize attributes.

        Raise ValueError if tag values are not supported.

        """
        tags = self.tags
        for code, (name, default, dtype, count, validate) in TIFF_TAGS.items():
            if not (name in tags or default is None):
                tags[name] = TiffTag(code, dtype=dtype, count=count,
                                     value=default, name=name)
            if name in tags and validate:
                try:
                    if tags[name].count == 1:
                        setattr(self, name, validate[tags[name].value])
                    else:
                        setattr(self, name, tuple(
                            validate[value] for value in tags[name].value))
                except KeyError:
                    raise ValueError(u"%s.value (%s) not supported" %
                                     (name, tags[name].value))

        tag = tags[u'bits_per_sample']
        if tag.count == 1:
            self.bits_per_sample = tag.value
        else:
            # LSM might list more items than samples_per_pixel
            value = tag.value[:self.samples_per_pixel]
            if any((v - value[0] for v in value)):
                self.bits_per_sample = value
            else:
                self.bits_per_sample = value[0]

        tag = tags[u'sample_format']
        if tag.count == 1:
            self.sample_format = TIFF_SAMPLE_FORMATS[tag.value]
        else:
            value = tag.value[:self.samples_per_pixel]
            if any((v - value[0] for v in value)):
                self.sample_format = [TIFF_SAMPLE_FORMATS[v] for v in value]
            else:
                self.sample_format = TIFF_SAMPLE_FORMATS[value[0]]

        if u'photometric' not in tags:
            self.photometric = None

        if u'image_depth' not in tags:
            self.image_depth = 1

        if u'image_length' in tags:
            self.strips_per_image = int(math.floor(
                float(self.image_length + self.rows_per_strip - 1) /
                self.rows_per_strip))
        else:
            self.strips_per_image = 0

        key = (self.sample_format, self.bits_per_sample)
        self.dtype = self._dtype = TIFF_SAMPLE_DTYPES.get(key, None)

        if u'image_length' not in self.tags or u'image_width' not in self.tags:
            # some GEL file pages are missing image data
            self.image_length = 0
            self.image_width = 0
            self.image_depth = 0
            self.strip_offsets = 0
            self._shape = ()
            self.shape = ()
            self.axes = u''

        if self.is_palette:
            self.dtype = self.tags[u'color_map'].dtype[1]
            self.color_map = numpy.array(self.color_map, self.dtype)
            dmax = self.color_map.max()
            if dmax < 256:
                self.dtype = numpy.uint8
                self.color_map = self.color_map.astype(self.dtype)
            # else:
            #    self.dtype = numpy.uint8
            #    self.color_map >>= 8
            #    self.color_map = self.color_map.astype(self.dtype)
            self.color_map.shape = (3, -1)

        # determine shape of data
        image_length = self.image_length
        image_width = self.image_width
        image_depth = self.image_depth
        samples_per_pixel = self.samples_per_pixel

        if self.is_stk:
            assert self.image_depth == 1
            planes = self.tags[u'uic2tag'].count
            if self.is_contig:
                self._shape = (planes, 1, 1, image_length, image_width,
                               samples_per_pixel)
                if samples_per_pixel == 1:
                    self.shape = (planes, image_length, image_width)
                    self.axes = u'YX'
                else:
                    self.shape = (planes, image_length, image_width,
                                  samples_per_pixel)
                    self.axes = u'YXS'
            else:
                self._shape = (planes, samples_per_pixel, 1, image_length,
                               image_width, 1)
                if samples_per_pixel == 1:
                    self.shape = (planes, image_length, image_width)
                    self.axes = u'YX'
                else:
                    self.shape = (planes, samples_per_pixel, image_length,
                                  image_width)
                    self.axes = u'SYX'
            # detect type of series
            if planes == 1:
                self.shape = self.shape[1:]
            elif numpy.all(self.uic2tag.z_distance != 0):
                self.axes = u'Z' + self.axes
            elif numpy.all(numpy.diff(self.uic2tag.time_created) != 0):
                self.axes = u'T' + self.axes
            else:
                self.axes = u'I' + self.axes
            # DISABLED
            if self.is_palette:
                assert False, u"color mapping disabled for stk"
        elif self.is_palette:
            samples = 1
            if u'extra_samples' in self.tags:
                samples += len(self.extra_samples)
            if self.is_contig:
                self._shape = (1, 1, image_depth, image_length, image_width,
                               samples)
            else:
                self._shape = (1, samples, image_depth, image_length,
                               image_width, 1)
            if self.color_map.shape[1] >= 2**self.bits_per_sample:
                if image_depth == 1:
                    self.shape = (3, image_length, image_width)
                    self.axes = u'CYX'
                else:
                    self.shape = (3, image_depth, image_length, image_width)
                    self.axes = u'CZYX'
            else:
                warnings.warn(u"palette cannot be applied")
                self.is_palette = False
                if image_depth == 1:
                    self.shape = (image_length, image_width)
                    self.axes = u'YX'
                else:
                    self.shape = (image_depth, image_length, image_width)
                    self.axes = u'ZYX'
        elif self.is_rgb or samples_per_pixel > 1:
            if self.is_contig:
                self._shape = (1, 1, image_depth, image_length, image_width,
                               samples_per_pixel)
                if image_depth == 1:
                    self.shape = (image_length, image_width, samples_per_pixel)
                    self.axes = u'YXS'
                else:
                    self.shape = (image_depth, image_length, image_width,
                                  samples_per_pixel)
                    self.axes = u'ZYXS'
            else:
                self._shape = (1, samples_per_pixel, image_depth,
                               image_length, image_width, 1)
                if image_depth == 1:
                    self.shape = (samples_per_pixel, image_length, image_width)
                    self.axes = u'SYX'
                else:
                    self.shape = (samples_per_pixel, image_depth,
                                  image_length, image_width)
                    self.axes = u'SZYX'
            if False and self.is_rgb and u'extra_samples' in self.tags:
                # DISABLED: only use RGB and first alpha channel if exists
                extra_samples = self.extra_samples
                if self.tags[u'extra_samples'].count == 1:
                    extra_samples = (extra_samples, )
                for exs in extra_samples:
                    if exs in (u'unassalpha', u'assocalpha', u'unspecified'):
                        if self.is_contig:
                            self.shape = self.shape[:-1] + (4,)
                        else:
                            self.shape = (4,) + self.shape[1:]
                        break
        else:
            self._shape = (1, 1, image_depth, image_length, image_width, 1)
            if image_depth == 1:
                self.shape = (image_length, image_width)
                self.axes = u'YX'
            else:
                self.shape = (image_depth, image_length, image_width)
                self.axes = u'ZYX'
        if not self.compression and u'strip_byte_counts' not in tags:
            self.strip_byte_counts = (
                product(self.shape) * (self.bits_per_sample // 8), )

        assert len(self.shape) == len(self.axes)

    def asarray(self, squeeze=True, colormapped=True, rgbonly=False,
                scale_mdgel=False, memmap=False, reopen=True):
        u"""Read image data from file and return as numpy array.

        Raise ValueError if format is unsupported.
        If any of 'squeeze', 'colormapped', or 'rgbonly' are not the default,
        the shape of the returned array might be different from the page shape.

        Parameters
        ----------
        squeeze : bool
            If True, all length-1 dimensions (except X and Y) are
            squeezed out from result.
        colormapped : bool
            If True, color mapping is applied for palette-indexed images.
        rgbonly : bool
            If True, return RGB(A) image without additional extra samples.
        memmap : bool
            If True, use numpy.memmap to read arrays from file if possible.
            For use on 64 bit systems and files with few huge contiguous data.
        reopen : bool
            If True and the parent file handle is closed, the file is
            temporarily re-opened (and closed if no exception occurs).
        scale_mdgel : bool
            If True, MD Gel data will be scaled according to the private
            metadata in the second TIFF page. The dtype will be float32.

        """
        if not self._shape:
            return

        if self.dtype is None:
            raise ValueError(u"data type not supported: %s%i" % (
                self.sample_format, self.bits_per_sample))
        if self.compression not in TIFF_DECOMPESSORS:
            raise ValueError(u"cannot decompress %s" % self.compression)
        tag = self.tags[u'sample_format']
        if tag.count != 1 and any((i - tag.value[0] for i in tag.value)):
            raise ValueError(u"sample formats don't match %s" % unicode(tag.value))

        fh = self.parent.filehandle
        closed = fh.closed
        if closed:
            if reopen:
                fh.open()
            else:
                raise IOError(u"file handle is closed")

        dtype = self._dtype
        shape = self._shape
        image_width = self.image_width
        image_length = self.image_length
        image_depth = self.image_depth
        typecode = self.parent.byteorder + dtype
        bits_per_sample = self.bits_per_sample

        if self.is_tiled:
            if u'tile_offsets' in self.tags:
                byte_counts = self.tile_byte_counts
                offsets = self.tile_offsets
            else:
                byte_counts = self.strip_byte_counts
                offsets = self.strip_offsets
            tile_width = self.tile_width
            tile_length = self.tile_length
            tile_depth = self.tile_depth if u'tile_depth' in self.tags else 1
            tw = (image_width + tile_width - 1) // tile_width
            tl = (image_length + tile_length - 1) // tile_length
            td = (image_depth + tile_depth - 1) // tile_depth
            shape = (shape[0], shape[1],
                     td * tile_depth, tl * tile_length, tw * tile_width, shape[-1])
            tile_shape = (tile_depth, tile_length, tile_width, shape[-1])
            runlen = tile_width
        else:
            byte_counts = self.strip_byte_counts
            offsets = self.strip_offsets
            runlen = image_width

        if any(o < 2 for o in offsets):
            raise ValueError(u"corrupted page")

        if memmap and self._is_memmappable(rgbonly, colormapped):
            result = fh.memmap_array(typecode, shape, offset=offsets[0])
        elif self.is_contiguous:
            fh.seek(offsets[0])
            result = fh.read_array(typecode, product(shape))
            result = result.astype(u'=' + dtype)
        else:
            if self.is_contig:
                runlen *= self.samples_per_pixel
            if bits_per_sample in (8, 16, 32, 64, 128):
                if (bits_per_sample * runlen) % 8:
                    raise ValueError(u"data and sample size mismatch")

                def unpack(x):
                    try:
                        return numpy.fromstring(x, typecode)
                    except ValueError, e:
                        # strips may be missing EOI
                        warnings.warn(u"unpack: %s" % e)
                        xlen = ((len(x) // (bits_per_sample // 8))
                                * (bits_per_sample // 8))
                        return numpy.fromstring(x[:xlen], typecode)

            elif isinstance(bits_per_sample, tuple):
                def unpack(x):
                    return unpackrgb(x, typecode, bits_per_sample)
            else:
                def unpack(x):
                    return unpackints(x, typecode, bits_per_sample, runlen)

            decompress = TIFF_DECOMPESSORS[self.compression]
            if self.compression == u'jpeg':
                table = self.jpeg_tables if u'jpeg_tables' in self.tags else ''
                decompress = lambda x: decodejpg(x, table, self.photometric)

            if self.is_tiled:
                result = numpy.empty(shape, dtype)
                tw, tl, td, pl = 0, 0, 0, 0
                for offset, bytecount in izip(offsets, byte_counts):
                    fh.seek(offset)
                    tile = unpack(decompress(fh.read(bytecount)))
                    tile.shape = tile_shape
                    if self.predictor == u'horizontal':
                        numpy.cumsum(tile, axis=-2, dtype=dtype, out=tile)
                    result[0, pl, td:td + tile_depth,
                           tl:tl + tile_length, tw:tw + tile_width, :] = tile
                    del tile
                    tw += tile_width
                    if tw >= shape[4]:
                        tw, tl = 0, tl + tile_length
                        if tl >= shape[3]:
                            tl, td = 0, td + tile_depth
                            if td >= shape[2]:
                                td, pl = 0, pl + 1
                result = result[...,
                                :image_depth, :image_length, :image_width, :]
            else:
                strip_size = (self.rows_per_strip * self.image_width *
                              self.samples_per_pixel)
                result = numpy.empty(shape, dtype).reshape(-1)
                index = 0
                for offset, bytecount in izip(offsets, byte_counts):
                    fh.seek(offset)
                    strip = fh.read(bytecount)
                    strip = decompress(strip)
                    strip = unpack(strip)
                    size = min(result.size, strip.size, strip_size,
                               result.size - index)
                    result[index:index + size] = strip[:size]
                    del strip
                    index += size

        result.shape = self._shape

        if self.predictor == u'horizontal' and not (self.is_tiled and not
                                                   self.is_contiguous):
            # work around bug in LSM510 software
            if not (self.parent.is_lsm and not self.compression):
                numpy.cumsum(result, axis=-2, dtype=dtype, out=result)

        if colormapped and self.is_palette:
            if self.color_map.shape[1] >= 2**bits_per_sample:
                # FluoView and LSM might fail here
                result = numpy.take(self.color_map,
                                    result[:, 0, :, :, :, 0], axis=1)
        elif rgbonly and self.is_rgb and u'extra_samples' in self.tags:
            # return only RGB and first alpha channel if exists
            extra_samples = self.extra_samples
            if self.tags[u'extra_samples'].count == 1:
                extra_samples = (extra_samples, )
            for i, exs in enumerate(extra_samples):
                if exs in (u'unassalpha', u'assocalpha', u'unspecified'):
                    if self.is_contig:
                        result = result[..., [0, 1, 2, 3 + i]]
                    else:
                        result = result[:, [0, 1, 2, 3 + i]]
                    break
            else:
                if self.is_contig:
                    result = result[..., :3]
                else:
                    result = result[:, :3]

        if squeeze:
            try:
                result.shape = self.shape
            except ValueError:
                warnings.warn(u"failed to reshape from %s to %s" % (
                    unicode(result.shape), unicode(self.shape)))

        if scale_mdgel and self.parent.is_mdgel:
            # MD Gel stores private metadata in the second page
            tags = self.parent.pages[1]
            if tags.md_file_tag in (2, 128):
                scale = tags.md_scale_pixel
                scale = scale[0] / scale[1]  # rational
                result = result.astype(u'float32')
                if tags.md_file_tag == 2:
                    result **= 2  # squary root data format
                result *= scale

        if closed:
            # TODO: file remains open if an exception occurred above
            fh.close()
        return result

    def _is_memmappable(self, rgbonly, colormapped):
        u"""Return if image data in file can be memory mapped."""
        if not self.parent.filehandle.is_file or not self.is_contiguous:
            return False
        return not (self.predictor or
                    (rgbonly and u'extra_samples' in self.tags) or
                    (colormapped and self.is_palette) or
                    ({u'big': u'>', u'little': u'<'}[sys.byteorder] !=
                     self.parent.byteorder))

    @lazyattr
    def is_contiguous(self):
        u"""Return offset and size of contiguous data, else None.

        Excludes prediction and colormapping.

        """
        if self.compression or self.bits_per_sample not in (8, 16, 32, 64):
            return
        if self.is_tiled:
            if (self.image_width != self.tile_width or
                    self.image_length % self.tile_length or
                    self.tile_width % 16 or self.tile_length % 16):
                return
            if (u'image_depth' in self.tags and u'tile_depth' in self.tags and
                (self.image_length != self.tile_length or
                 self.image_depth % self.tile_depth)):
                return
            offsets = self.tile_offsets
            byte_counts = self.tile_byte_counts
        else:
            offsets = self.strip_offsets
            byte_counts = self.strip_byte_counts
        if len(offsets) == 1:
            return offsets[0], byte_counts[0]
        if self.is_stk or all(offsets[i] + byte_counts[i] == offsets[i + 1]
                              # no data/ignore offset
                              or byte_counts[i + 1] == 0
                              for i in xrange(len(offsets) - 1)):
            return offsets[0], sum(byte_counts)

    def __str__(self):
        u"""Return string containing information about page."""
        s = u', '.join(s for s in (
            u' x '.join(unicode(i) for i in self.shape),
            unicode(numpy.dtype(self.dtype)),
            u'%s bit' % unicode(self.bits_per_sample),
            self.photometric if u'photometric' in self.tags else u'',
            self.compression if self.compression else u'raw',
            u'|'.join(t[3:] for t in (
                u'is_stk', u'is_lsm', u'is_nih', u'is_ome', u'is_imagej',
                u'is_micromanager', u'is_fluoview', u'is_mdgel', u'is_mediacy',
                u'is_sgi', u'is_reduced', u'is_tiled',
                u'is_contiguous') if getattr(self, t))) if s)
        return u"Page %i: %s" % (self.index, s)

    def __getattr__(self, name):
        u"""Return tag value."""
        if name in self.tags:
            value = self.tags[name].value
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    @lazyattr
    def uic_tags(self):
        u"""Consolidate UIC tags."""
        if not self.is_stk:
            raise AttributeError(u"uic_tags")
        tags = self.tags
        result = Record()
        result.number_planes = tags[u'uic2tag'].count
        if u'image_description' in tags:
            result.plane_descriptions = self.image_description.split('\x00')
        if u'uic1tag' in tags:
            result.update(tags[u'uic1tag'].value)
        if u'uic3tag' in tags:
            result.update(tags[u'uic3tag'].value)  # wavelengths
        if u'uic4tag' in tags:
            result.update(tags[u'uic4tag'].value)  # override uic1 tags
        uic2tag = tags[u'uic2tag'].value
        result.z_distance = uic2tag.z_distance
        result.time_created = uic2tag.time_created
        result.time_modified = uic2tag.time_modified
        try:
            result.datetime_created = [
                julian_datetime(*dt) for dt in
                izip(uic2tag.date_created, uic2tag.time_created)]
            result.datetime_modified = [
                julian_datetime(*dt) for dt in
                izip(uic2tag.date_modified, uic2tag.time_modified)]
        except ValueError, e:
            warnings.warn(u"uic_tags: %s" % e)
        return result

    @lazyattr
    def imagej_tags(self):
        u"""Consolidate ImageJ metadata."""
        if not self.is_imagej:
            raise AttributeError(u"imagej_tags")
        tags = self.tags
        if u'image_description_1' in tags:
            # MicroManager
            result = imagej_description(tags[u'image_description_1'].value)
        else:
            result = imagej_description(tags[u'image_description'].value)
        if u'imagej_metadata' in tags:
            try:
                result.update(imagej_metadata(
                    tags[u'imagej_metadata'].value,
                    tags[u'imagej_byte_counts'].value,
                    self.parent.byteorder))
            except Exception, e:
                warnings.warn(unicode(e))
        return Record(result)

    @lazyattr
    def is_rgb(self):
        u"""True if page contains a RGB image."""
        return (u'photometric' in self.tags and
                self.tags[u'photometric'].value == 2)

    @lazyattr
    def is_contig(self):
        u"""True if page contains a contiguous image."""
        return (u'planar_configuration' in self.tags and
                self.tags[u'planar_configuration'].value == 1)

    @lazyattr
    def is_palette(self):
        u"""True if page contains a palette-colored image and not OME or STK."""
        try:
            # turn off color mapping for OME-TIFF and STK
            if self.is_stk or self.is_ome or self.parent.is_ome:
                return False
        except IndexError:
            pass  # OME-XML not found in first page
        return (u'photometric' in self.tags and
                self.tags[u'photometric'].value == 3)

    @lazyattr
    def is_tiled(self):
        u"""True if page contains tiled image."""
        return u'tile_width' in self.tags

    @lazyattr
    def is_reduced(self):
        u"""True if page is a reduced image of another image."""
        return bool(self.tags[u'new_subfile_type'].value & 1)

    @lazyattr
    def is_mdgel(self):
        u"""True if page contains md_file_tag tag."""
        return u'md_file_tag' in self.tags

    @lazyattr
    def is_mediacy(self):
        u"""True if page contains Media Cybernetics Id tag."""
        return (u'mc_id' in self.tags and
                self.tags[u'mc_id'].value.startswith('MC TIFF'))

    @lazyattr
    def is_stk(self):
        u"""True if page contains UIC2Tag tag."""
        return u'uic2tag' in self.tags

    @lazyattr
    def is_lsm(self):
        u"""True if page contains LSM CZ_LSM_INFO tag."""
        return u'cz_lsm_info' in self.tags

    @lazyattr
    def is_fluoview(self):
        u"""True if page contains FluoView MM_STAMP tag."""
        return u'mm_stamp' in self.tags

    @lazyattr
    def is_nih(self):
        u"""True if page contains NIH image header."""
        return u'nih_image_header' in self.tags

    @lazyattr
    def is_sgi(self):
        u"""True if page contains SGI image and tile depth tags."""
        return u'image_depth' in self.tags and u'tile_depth' in self.tags

    @lazyattr
    def is_ome(self):
        u"""True if page contains OME-XML in image_description tag."""
        return (u'image_description' in self.tags and self.tags[
            u'image_description'].value.startswith('<?xml version='))

    @lazyattr
    def is_shaped(self):
        u"""True if page contains shape in image_description tag."""
        return (u'image_description' in self.tags and self.tags[
            u'image_description'].value.startswith('shape=('))

    @lazyattr
    def is_imagej(self):
        u"""True if page contains ImageJ description."""
        return (
            (u'image_description' in self.tags and
             self.tags[u'image_description'].value.startswith('ImageJ=')) or
            (u'image_description_1' in self.tags and  # Micromanager
             self.tags[u'image_description_1'].value.startswith('ImageJ=')))

    @lazyattr
    def is_micromanager(self):
        u"""True if page contains Micro-Manager metadata."""
        return u'micromanager_metadata' in self.tags


class TiffTag(object):

    u"""A TIFF tag structure.

    Attributes
    ----------
    name : string
        Attribute name of tag.
    code : int
        Decimal code of tag.
    dtype : str
        Datatype of tag data. One of TIFF_DATA_TYPES.
    count : int
        Number of values.
    value : various types
        Tag data as Python object.
    value_offset : int
        Location of value in file, if any.

    All attributes are read-only.

    """
    __slots__ = (u'code', u'name', u'count', u'dtype', u'value', u'value_offset',
                 u'_offset', u'_value', u'_type')

    class Error(Exception):
        pass

    def __init__(self, arg, **kwargs):
        u"""Initialize instance from file or arguments."""
        self._offset = None
        if hasattr(arg, u'_fh'):
            self._fromfile(arg)
        else:
            self._fromdata(arg, **kwargs)

    def _fromdata(self, code, dtype, count, value, name=None):
        u"""Initialize instance from arguments."""
        self.code = int(code)
        self.name = name if name else unicode(code)
        self.dtype = TIFF_DATA_TYPES[dtype]
        self.count = int(count)
        self.value = value
        self._value = value
        self._type = dtype

    def _fromfile(self, parent):
        u"""Read tag structure from open file. Advance file cursor."""
        fh = parent.filehandle
        byteorder = parent.byteorder
        self._offset = fh.tell()
        self.value_offset = self._offset + parent.offset_size + 4

        fmt, size = {4: (u'HHI4s', 12), 8: (u'HHQ8s', 20)}[parent.offset_size]
        data = fh.read(size)
        code, dtype = struct.unpack(byteorder + fmt[:2], data[:4])
        count, value = struct.unpack(byteorder + fmt[2:], data[4:])
        self._value = value
        self._type = dtype

        if code in TIFF_TAGS:
            name = TIFF_TAGS[code][0]
        elif code in CUSTOM_TAGS:
            name = CUSTOM_TAGS[code][0]
        else:
            name = unicode(code)

        try:
            dtype = TIFF_DATA_TYPES[self._type]
        except KeyError:
            raise TiffTag.Error(u"unknown tag data type %i" % self._type)

        fmt = u'%s%i%s' % (byteorder, count * int(dtype[0]), dtype[1])
        size = struct.calcsize(fmt)
        if size > parent.offset_size or code in CUSTOM_TAGS:
            pos = fh.tell()
            tof = {4: u'I', 8: u'Q'}[parent.offset_size]
            self.value_offset = offset = struct.unpack(
                byteorder +
                tof,
                value)[0]
            if offset < 0 or offset > parent.filehandle.size:
                raise TiffTag.Error(u"corrupt file - invalid tag value offset")
            elif offset < 4:
                raise TiffTag.Error(u"corrupt value offset for tag %i" % code)
            fh.seek(offset)
            if code in CUSTOM_TAGS:
                readfunc = CUSTOM_TAGS[code][1]
                value = readfunc(fh, byteorder, dtype, count)
                if isinstance(value, dict):  # numpy.core.records.record
                    value = Record(value)
            elif code in TIFF_TAGS or dtype[-1] == u's':
                value = struct.unpack(fmt, fh.read(size))
            else:
                value = read_numpy(fh, byteorder, dtype, count)
            fh.seek(pos)
        else:
            value = struct.unpack(fmt, value[:size])

        if code not in CUSTOM_TAGS and code not in (273, 279, 324, 325):
            # scalar value if not strip/tile offsets/byte_counts
            if len(value) == 1:
                value = value[0]

        if (dtype.endswith(u's') and isinstance(value, str)
                and self._type != 7):
            # TIFF ASCII fields can contain multiple strings,
            # each terminated with a NUL
            value = stripascii(value)

        self.code = code
        self.name = name
        self.dtype = dtype
        self.count = count
        self.value = value

    def _correct_lsm_bitspersample(self, parent):
        u"""Correct LSM bitspersample tag.

        Old LSM writers may use a separate region for two 16-bit values,
        although they fit into the tag value element of the tag.

        """
        if self.code == 258 and self.count == 2:
            # TODO: test this. Need example file.
            warnings.warn(u"correcting LSM bitspersample tag")
            fh = parent.filehandle
            tof = {4: u'<I', 8: u'<Q'}[parent.offset_size]
            self.value_offset = struct.unpack(tof, self._value)[0]
            fh.seek(self.value_offset)
            self.value = struct.unpack(u"<HH", fh.read(4))

    def as_str(self):
        u"""Return value as human readable string."""
        return ((unicode(self.value).split(u'\n', 1)[0]) if (self._type != 7)
                else u'<undefined>')

    def __str__(self):
        u"""Return string containing information about tag."""
        return u' '.join(unicode(getattr(self, s)) for s in self.__slots__)


class TiffSequence(object):

    u"""Sequence of image files.

    The data shape and dtype of all files must match.

    Properties
    ----------
    files : list
        List of file names.
    shape : tuple
        Shape of image sequence.
    axes : str
        Labels of axes in shape.

    Examples
    --------
    >>> tifs = TiffSequence("test.oif.files/*.tif")
    >>> tifs.shape, tifs.axes
    ((2, 100), 'CT')
    >>> data = tifs.asarray()
    >>> data.shape
    (2, 100, 256, 256)

    """
    _patterns = {
        u'axes': ur"""
            # matches Olympus OIF and Leica TIFF series
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))?
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))?
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))?
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))?
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))?
            _?(?:(q|l|p|a|c|t|x|y|z|ch|tp)(\d{1,4}))?
            """}

    class ParseError(Exception):
        pass

    def __init__(self, files, imread=TiffFile, pattern=u'axes',
                 *args, **kwargs):
        u"""Initialize instance from multiple files.

        Parameters
        ----------
        files : str, or sequence of str
            Glob pattern or sequence of file names.
        imread : function or class
            Image read function or class with asarray function returning numpy
            array from single file.
        pattern : str
            Regular expression pattern that matches axes names and sequence
            indices in file names.
            By default this matches Olympus OIF and Leica TIFF series.

        """
        if isinstance(files, unicode):
            files = natural_sorted(glob.glob(files))
        files = list(files)
        if not files:
            raise ValueError(u"no files found")
        # if not os.path.isfile(files[0]):
        #    raise ValueError("file not found")
        self.files = files

        if hasattr(imread, u'asarray'):
            # redefine imread
            _imread = imread

            def imread(fname, *args, **kwargs):
                with _imread(fname) as im:
                    return im.asarray(*args, **kwargs)

        self.imread = imread

        self.pattern = self._patterns.get(pattern, pattern)
        try:
            self._parse()
            if not self.axes:
                self.axes = u'I'
        except self.ParseError:
            self.axes = u'I'
            self.shape = (len(files),)
            self._start_index = (0,)
            self._indices = tuple((i,) for i in xrange(len(files)))

    def __str__(self):
        u"""Return string with information about image sequence."""
        return u"\n".join([
            self.files[0],
            u'* files: %i' % len(self.files),
            u'* axes: %s' % self.axes,
            u'* shape: %s' % unicode(self.shape)])

    def __len__(self):
        return len(self.files)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        pass

    def asarray(self, memmap=False, *args, **kwargs):
        u"""Read image data from all files and return as single numpy array.

        If memmap is True, return an array stored in a binary file on disk.
        The args and kwargs parameters are passed to the imread function.

        Raise IndexError or ValueError if image shapes don't match.

        """
        im = self.imread(self.files[0], *args, **kwargs)
        shape = self.shape + im.shape
        if memmap:
            with tempfile.NamedTemporaryFile() as fh:
                result = numpy.memmap(fh, dtype=im.dtype, shape=shape)
        else:
            result = numpy.zeros(shape, dtype=im.dtype)
        result = result.reshape(-1, *im.shape)
        for index, fname in izip(self._indices, self.files):
            index = [i - j for i, j in izip(index, self._start_index)]
            index = numpy.ravel_multi_index(index, self.shape)
            im = self.imread(fname, *args, **kwargs)
            result[index] = im
        result.shape = shape
        return result

    def _parse(self):
        u"""Get axes and shape from file names."""
        if not self.pattern:
            raise self.ParseError(u"invalid pattern")
        pattern = re.compile(self.pattern, re.IGNORECASE | re.VERBOSE)
        matches = pattern.findall(self.files[0])
        if not matches:
            raise self.ParseError(u"pattern doesn't match file names")
        matches = matches[-1]
        if len(matches) % 2:
            raise self.ParseError(u"pattern doesn't match axis name and index")
        axes = u''.join(m for m in matches[::2] if m)
        if not axes:
            raise self.ParseError(u"pattern doesn't match file names")

        indices = []
        for fname in self.files:
            matches = pattern.findall(fname)[-1]
            if axes != u''.join(m for m in matches[::2] if m):
                raise ValueError(u"axes don't match within the image sequence")
            indices.append([int(m) for m in matches[1::2] if m])
        shape = tuple(numpy.max(indices, axis=0))
        start_index = tuple(numpy.min(indices, axis=0))
        shape = tuple(i - j + 1 for i, j in izip(shape, start_index))
        if product(shape) != len(self.files):
            warnings.warn(u"files are missing. Missing data are zeroed")

        self.axes = axes.upper()
        self.shape = shape
        self._indices = indices
        self._start_index = start_index


class Record(dict):

    u"""Dictionary with attribute access.

    Can also be initialized with numpy.core.records.record.

    """
    __slots__ = ()

    def __init__(self, arg=None, **kwargs):
        if kwargs:
            arg = kwargs
        elif arg is None:
            arg = {}
        try:
            dict.__init__(self, arg)
        except (TypeError, ValueError):
            for i, name in enumerate(arg.dtype.names):
                v = arg[i]
                self[name] = v if v.dtype.char != u'S' else stripnull(v)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __str__(self):
        u"""Pretty print Record."""
        s = []
        lists = []
        for k in sorted(self):
            try:
                if k.startswith(u'_'):  # does not work with byte
                    continue
            except AttributeError:
                pass
            v = self[k]
            if isinstance(v, (list, tuple)) and len(v):
                if isinstance(v[0], Record):
                    lists.append((k, v))
                    continue
                elif isinstance(v[0], TiffPage):
                    v = [i.index for i in v if i]
            s.append(
                (u"* %s: %s" % (k, unicode(v))).split(u"\n", 1)[0]
                [:PRINT_LINE_LEN].rstrip())
        for k, v in lists:
            l = []
            for i, w in enumerate(v):
                l.append(u"* %s[%i]\n  %s" % (k, i,
                                             unicode(w).replace(u"\n", u"\n  ")))
            s.append(u'\n'.join(l))
        return u'\n'.join(s)


class TiffTags(Record):

    u"""Dictionary of TiffTag with attribute access."""

    def __str__(self):
        u"""Return string with information about all tags."""
        s = []
        for tag in sorted(self.values(), key=lambda x: x.code):
            typecode = u"%i%s" % (tag.count * int(tag.dtype[0]), tag.dtype[1])
            line = u"* %i %s (%s) %s" % (
                tag.code, tag.name, typecode, tag.as_str())
            s.append(line[:PRINT_LINE_LEN].lstrip())
        return u'\n'.join(s)


class FileHandle(object):

    u"""Binary file handle.

    * Handle embedded files (for CZI within CZI files).
    * Allow to re-open closed files (for multi file formats such as OME-TIFF).
    * Read numpy arrays and records from file like objects.

    Only binary read, seek, tell, and close are supported on embedded files.
    When initialized from another file handle, do not use it unless this
    FileHandle is closed.

    Attributes
    ----------
    name : str
        Name of the file.
    path : str
        Absolute path to file.
    size : int
        Size of file in bytes.
    is_file : bool
        If True, file has a filno and can be memory mapped.

    All attributes are read-only.

    """
    __slots__ = (u'_fh', u'_arg', u'_mode', u'_name', u'_dir',
                 u'_offset', u'_size', u'_close', u'is_file')

    def __init__(self, arg, mode=u'rb', name=None, offset=None, size=None):
        u"""Initialize file handle from file name or another file handle.

        Parameters
        ----------
        arg : str, File, or FileHandle
            File name or open file handle.
        mode : str
            File open mode in case 'arg' is a file name.
        name : str
            Optional name of file in case 'arg' is a file handle.
        offset : int
            Optional start position of embedded file. By default this is
            the current file position.
        size : int
            Optional size of embedded file. By default this is the number
            of bytes from the 'offset' to the end of the file.

        """
        self._fh = None
        self._arg = arg
        self._mode = mode
        self._name = name
        self._dir = u''
        self._offset = offset
        self._size = size
        self._close = True
        self.is_file = False
        self.open()

    def open(self):
        u"""Open or re-open file."""
        if self._fh:
            return  # file is open

        if isinstance(self._arg, unicode):
            # file name
            self._arg = os.path.abspath(self._arg)
            self._dir, self._name = os.path.split(self._arg)
            self._fh = open(self._arg, self._mode)
            self._close = True
            if self._offset is None:
                self._offset = 0
        elif isinstance(self._arg, FileHandle):
            # FileHandle
            self._fh = self._arg._fh
            if self._offset is None:
                self._offset = 0
            self._offset += self._arg._offset
            self._close = False
            if not self._name:
                if self._offset:
                    name, ext = os.path.splitext(self._arg._name)
                    self._name = u"%s@%i%s" % (name, self._offset, ext)
                else:
                    self._name = self._arg._name
            self._dir = self._arg._dir
        else:
            # open file object
            self._fh = self._arg
            if self._offset is None:
                self._offset = self._arg.tell()
            self._close = False
            if not self._name:
                try:
                    self._dir, self._name = os.path.split(self._fh.name)
                except AttributeError:
                    self._name = u"Unnamed stream"

        if self._offset:
            self._fh.seek(self._offset)

        if self._size is None:
            pos = self._fh.tell()
            self._fh.seek(self._offset, 2)
            self._size = self._fh.tell()
            self._fh.seek(pos)

        try:
            self._fh.fileno()
            self.is_file = True
        except Exception:
            self.is_file = False

    def read(self, size=-1):
        u"""Read 'size' bytes from file, or until EOF is reached."""
        if size < 0 and self._offset:
            size = self._size
        return self._fh.read(size)

    def memmap_array(self, dtype, shape, offset=0, mode=u'r', order=u'C'):
        u"""Return numpy.memmap of data stored in file."""
        if not self.is_file:
            raise ValueError(u"Can not memory map file without fileno.")
        return numpy.memmap(self._fh, dtype=dtype, mode=mode,
                            offset=self._offset + offset,
                            shape=shape, order=order)

    def read_array(self, dtype, count=-1, sep=u""):
        u"""Return numpy array from file.

        Work around numpy issue #2230, "numpy.fromfile does not accept
        StringIO object" https://github.com/numpy/numpy/issues/2230.

        """
        try:
            return numpy.fromfile(self._fh, dtype, count, sep)
        except IOError:
            if count < 0:
                size = self._size
            else:
                size = count * numpy.dtype(dtype).itemsize
            data = self._fh.read(size)
            return numpy.fromstring(data, dtype, count, sep)

    def read_record(self, dtype, shape=1, byteorder=None):
        u"""Return numpy record from file."""
        try:
            rec = numpy.rec.fromfile(self._fh, dtype, shape,
                                     byteorder=byteorder)
        except Exception:
            dtype = numpy.dtype(dtype)
            if shape is None:
                shape = self._size // dtype.itemsize
            size = product(sequence(shape)) * dtype.itemsize
            data = self._fh.read(size)
            return numpy.rec.fromstring(data, dtype, shape,
                                        byteorder=byteorder)
        return rec[0] if shape == 1 else rec

    def tell(self):
        u"""Return file's current position."""
        return self._fh.tell() - self._offset

    def seek(self, offset, whence=0):
        u"""Set file's current position."""
        if self._offset:
            if whence == 0:
                self._fh.seek(self._offset + offset, whence)
                return
            elif whence == 2:
                self._fh.seek(self._offset + self._size + offset, 0)
                return
        self._fh.seek(offset, whence)

    def close(self):
        u"""Close file."""
        if self._close and self._fh:
            self._fh.close()
            self._fh = None
            self.is_file = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, name):
        u"""Return attribute from underlying file object."""
        if self._offset:
            warnings.warn(
                u"FileHandle: '%s' not implemented for embedded files" % name)
        return getattr(self._fh, name)

    @property
    def name(self):
        return self._name

    @property
    def dirname(self):
        return self._dir

    @property
    def path(self):
        return os.path.join(self._dir, self._name)

    @property
    def size(self):
        return self._size

    @property
    def closed(self):
        return self._fh is None


def read_bytes(fh, byteorder, dtype, count):
    u"""Read tag data from file and return as byte string."""
    dtype = u'b' if dtype[-1] == u's' else byteorder + dtype[-1]
    return fh.read_array(dtype, count).tostring()


def read_numpy(fh, byteorder, dtype, count):
    u"""Read tag data from file and return as numpy array."""
    dtype = u'b' if dtype[-1] == u's' else byteorder + dtype[-1]
    return fh.read_array(dtype, count)


def read_json(fh, byteorder, dtype, count):
    u"""Read JSON tag data from file and return as object."""
    data = fh.read(count)
    try:
        return json.loads(unicode(stripnull(data), u'utf-8'))
    except ValueError:
        warnings.warn(u"invalid JSON `%s`" % data)


def read_mm_header(fh, byteorder, dtype, count):
    u"""Read MM_HEADER tag from file and return as numpy.rec.array."""
    return fh.read_record(MM_HEADER, byteorder=byteorder)


def read_mm_stamp(fh, byteorder, dtype, count):
    u"""Read MM_STAMP tag from file and return as numpy.array."""
    return fh.read_array(byteorder + u'f8', 8)


def read_uic1tag(fh, byteorder, dtype, count, plane_count=None):
    u"""Read MetaMorph STK UIC1Tag from file and return as dictionary.

    Return empty dictionary if plane_count is unknown.

    """
    assert dtype in (u'2I', u'1I') and byteorder == u'<'
    result = {}
    if dtype == u'2I':
        # pre MetaMorph 2.5 (not tested)
        values = fh.read_array(u'<u4', 2 * count).reshape(count, 2)
        result = {u'z_distance': values[:, 0] / values[:, 1]}
    elif plane_count:
        for i in xrange(count):
            tagid = struct.unpack(u'<I', fh.read(4))[0]
            if tagid in (28, 29, 37, 40, 41):
                # silently skip unexpected tags
                fh.read(4)
                continue
            name, value = read_uic_tag(fh, tagid, plane_count, offset=True)
            result[name] = value
    return result


def read_uic2tag(fh, byteorder, dtype, plane_count):
    u"""Read MetaMorph STK UIC2Tag from file and return as dictionary."""
    assert dtype == u'2I' and byteorder == u'<'
    values = fh.read_array(u'<u4', 6 * plane_count).reshape(plane_count, 6)
    return {
        u'z_distance': values[:, 0] / values[:, 1],
        u'date_created': values[:, 2],  # julian days
        u'time_created': values[:, 3],  # milliseconds
        u'date_modified': values[:, 4],  # julian days
        u'time_modified': values[:, 5],  # milliseconds
    }


def read_uic3tag(fh, byteorder, dtype, plane_count):
    u"""Read MetaMorph STK UIC3Tag from file and return as dictionary."""
    assert dtype == u'2I' and byteorder == u'<'
    values = fh.read_array(u'<u4', 2 * plane_count).reshape(plane_count, 2)
    return {u'wavelengths': values[:, 0] / values[:, 1]}


def read_uic4tag(fh, byteorder, dtype, plane_count):
    u"""Read MetaMorph STK UIC4Tag from file and return as dictionary."""
    assert dtype == u'1I' and byteorder == u'<'
    result = {}
    while True:
        tagid = struct.unpack(u'<H', fh.read(2))[0]
        if tagid == 0:
            break
        name, value = read_uic_tag(fh, tagid, plane_count, offset=False)
        result[name] = value
    return result


def read_uic_tag(fh, tagid, plane_count, offset):
    u"""Read a single UIC tag value from file and return tag name and value.

    UIC1Tags use an offset.

    """
    def read_int(count=1):
        value = struct.unpack(u'<%iI' % count, fh.read(4 * count))
        return value[0] if count == 1 else value

    try:
        name, dtype = UIC_TAGS[tagid]
    except KeyError:
        # unknown tag
        return u'_tagid_%i' % tagid, read_int()

    if offset:
        pos = fh.tell()
        if dtype not in (int, None):
            off = read_int()
            if off < 8:
                warnings.warn(u"invalid offset for uic tag '%s': %i"
                              % (name, off))
                return name, off
            fh.seek(off)

    if dtype is None:
        # skip
        name = u'_' + name
        value = read_int()
    elif dtype is int:
        # int
        value = read_int()
    elif dtype is Fraction:
        # fraction
        value = read_int(2)
        value = value[0] / value[1]
    elif dtype is julian_datetime:
        # datetime
        value = julian_datetime(*read_int(2))
    elif dtype is read_uic_image_property:
        # ImagePropertyEx
        value = read_uic_image_property(fh)
    elif dtype is unicode:
        # pascal string
        size = read_int()
        if 0 <= size < 2**10:
            value = struct.unpack(u'%is' % size, fh.read(size))[0][:-1]
            value = stripnull(value)
        elif offset:
            value = u''
            warnings.warn(u"corrupt string in uic tag '%s'" % name)
        else:
            raise ValueError(u"invalid string size %i" % size)
    elif dtype == u'%ip':
        # sequence of pascal strings
        value = []
        for i in xrange(plane_count):
            size = read_int()
            if 0 <= size < 2**10:
                string = struct.unpack(u'%is' % size, fh.read(size))[0][:-1]
                string = stripnull(string)
                value.append(string)
            elif offset:
                warnings.warn(u"corrupt string in uic tag '%s'" % name)
            else:
                raise ValueError(u"invalid string size %i" % size)
    else:
        # struct or numpy type
        dtype = u'<' + dtype
        if u'%i' in dtype:
            dtype = dtype % plane_count
        if u'(' in dtype:
            # numpy type
            value = fh.read_array(dtype, 1)[0]
            if value.shape[-1] == 2:
                # assume fractions
                value = value[..., 0] / value[..., 1]
        else:
            # struct format
            value = struct.unpack(dtype, fh.read(struct.calcsize(dtype)))
            if len(value) == 1:
                value = value[0]

    if offset:
        fh.seek(pos + 4)

    return name, value


def read_uic_image_property(fh):
    u"""Read UIC ImagePropertyEx tag from file and return as dict."""
    # TODO: test this
    size = struct.unpack(u'B', fh.read(1))[0]
    name = struct.unpack(u'%is' % size, fh.read(size))[0][:-1]
    flags, prop = struct.unpack(u'<IB', fh.read(5))
    if prop == 1:
        value = struct.unpack(u'II', fh.read(8))
        value = value[0] / value[1]
    else:
        size = struct.unpack(u'B', fh.read(1))[0]
        value = struct.unpack(u'%is' % size, fh.read(size))[0]
    return dict(name=name, flags=flags, value=value)


def read_cz_lsm_info(fh, byteorder, dtype, count):
    u"""Read CS_LSM_INFO tag from file and return as numpy.rec.array."""
    assert byteorder == u'<'
    magic_number, structure_size = struct.unpack(u'<II', fh.read(8))
    if magic_number not in (50350412, 67127628):
        raise ValueError(u"not a valid CS_LSM_INFO structure")
    fh.seek(-8, 1)

    if structure_size < numpy.dtype(CZ_LSM_INFO).itemsize:
        # adjust structure according to structure_size
        cz_lsm_info = []
        size = 0
        for name, dtype in CZ_LSM_INFO:
            size += numpy.dtype(dtype).itemsize
            if size > structure_size:
                break
            cz_lsm_info.append((name, dtype))
    else:
        cz_lsm_info = CZ_LSM_INFO

    return fh.read_record(cz_lsm_info, byteorder=byteorder)


def read_cz_lsm_floatpairs(fh):
    u"""Read LSM sequence of float pairs from file and return as list."""
    size = struct.unpack(u'<i', fh.read(4))[0]
    return fh.read_array(u'<2f8', count=size)


def read_cz_lsm_positions(fh):
    u"""Read LSM positions from file and return as list."""
    size = struct.unpack(u'<I', fh.read(4))[0]
    return fh.read_array(u'<2f8', count=size)


def read_cz_lsm_time_stamps(fh):
    u"""Read LSM time stamps from file and return as list."""
    size, count = struct.unpack(u'<ii', fh.read(8))
    if size != (8 + 8 * count):
        raise ValueError(u"lsm_time_stamps block is too short")
    # return struct.unpack('<%dd' % count, fh.read(8*count))
    return fh.read_array(u'<f8', count=count)


def read_cz_lsm_event_list(fh):
    u"""Read LSM events from file and return as list of (time, type, text)."""
    count = struct.unpack(u'<II', fh.read(8))[1]
    events = []
    while count > 0:
        esize, etime, etype = struct.unpack(u'<IdI', fh.read(16))
        etext = stripnull(fh.read(esize - 16))
        events.append((etime, etype, etext))
        count -= 1
    return events


def read_cz_lsm_scan_info(fh):
    u"""Read LSM scan information from file and return as Record."""
    block = Record()
    blocks = [block]
    unpack = struct.unpack
    if 0x10000000 != struct.unpack(u'<I', fh.read(4))[0]:
        # not a Recording sub block
        raise ValueError(u"not a lsm_scan_info structure")
    fh.read(8)
    while True:
        entry, dtype, size = unpack(u'<III', fh.read(12))
        if dtype == 2:
            # ascii
            value = stripnull(fh.read(size))
        elif dtype == 4:
            # long
            value = unpack(u'<i', fh.read(4))[0]
        elif dtype == 5:
            # rational
            value = unpack(u'<d', fh.read(8))[0]
        else:
            value = 0
        if entry in CZ_LSM_SCAN_INFO_ARRAYS:
            blocks.append(block)
            name = CZ_LSM_SCAN_INFO_ARRAYS[entry]
            newobj = []
            setattr(block, name, newobj)
            block = newobj
        elif entry in CZ_LSM_SCAN_INFO_STRUCTS:
            blocks.append(block)
            newobj = Record()
            block.append(newobj)
            block = newobj
        elif entry in CZ_LSM_SCAN_INFO_ATTRIBUTES:
            name = CZ_LSM_SCAN_INFO_ATTRIBUTES[entry]
            setattr(block, name, value)
        elif entry == 0xffffffff:
            # end sub block
            block = blocks.pop()
        else:
            # unknown entry
            setattr(block, u"entry_0x%x" % entry, value)
        if not blocks:
            break
    return block


def read_nih_image_header(fh, byteorder, dtype, count):
    u"""Read NIH_IMAGE_HEADER tag from file and return as numpy.rec.array."""
    a = fh.read_record(NIH_IMAGE_HEADER, byteorder=byteorder)
    a = a.newbyteorder(byteorder)
    a.xunit = a.xunit[:a._xunit_len]
    a.um = a.um[:a._um_len]
    return a


def read_micromanager_metadata(fh):
    u"""Read MicroManager non-TIFF settings from open file and return as dict.

    The settings can be used to read image data without parsing the TIFF file.

    Raise ValueError if file does not contain valid MicroManager metadata.

    """
    fh.seek(0)
    try:
        byteorder = {'II': u'<', 'MM': u'>'}[fh.read(2)]
    except IndexError:
        raise ValueError(u"not a MicroManager TIFF file")

    results = {}
    fh.seek(8)
    (index_header, index_offset, display_header, display_offset,
     comments_header, comments_offset, summary_header, summary_length
     ) = struct.unpack(byteorder + u"IIIIIIII", fh.read(32))

    if summary_header != 2355492:
        raise ValueError(u"invalid MicroManager summary_header")
    results[u'summary'] = read_json(fh, byteorder, None, summary_length)

    if index_header != 54773648:
        raise ValueError(u"invalid MicroManager index_header")
    fh.seek(index_offset)
    header, count = struct.unpack(byteorder + u"II", fh.read(8))
    if header != 3453623:
        raise ValueError(u"invalid MicroManager index_header")
    data = struct.unpack(byteorder + u"IIIII" * count, fh.read(20 * count))
    results[u'index_map'] = {
        u'channel': data[::5], u'slice': data[1::5], u'frame': data[2::5],
        u'position': data[3::5], u'offset': data[4::5]}

    if display_header != 483765892:
        raise ValueError(u"invalid MicroManager display_header")
    fh.seek(display_offset)
    header, count = struct.unpack(byteorder + u"II", fh.read(8))
    if header != 347834724:
        raise ValueError(u"invalid MicroManager display_header")
    results[u'display_settings'] = read_json(fh, byteorder, None, count)

    if comments_header != 99384722:
        raise ValueError(u"invalid MicroManager comments_header")
    fh.seek(comments_offset)
    header, count = struct.unpack(byteorder + u"II", fh.read(8))
    if header != 84720485:
        raise ValueError(u"invalid MicroManager comments_header")
    results[u'comments'] = read_json(fh, byteorder, None, count)

    return results


def imagej_metadata(data, bytecounts, byteorder):
    u"""Return dict from ImageJ metadata tag value."""
    _str = unicode if sys.version_info[0] < 3 else lambda x: unicode(x, u'cp1252')

    def read_string(data, byteorder):
        return _str(stripnull(data[0 if byteorder == u'<' else 1::2]))

    def read_double(data, byteorder):
        return struct.unpack(byteorder + (u'd' * (len(data) // 8)), data)

    def read_bytes(data, byteorder):
        # return struct.unpack('b' * len(data), data)
        return numpy.fromstring(data, u'uint8')

    metadata_types = {  # big endian
        'info': (u'info', read_string),
        'labl': (u'labels', read_string),
        'rang': (u'ranges', read_double),
        'luts': (u'luts', read_bytes),
        'roi ': (u'roi', read_bytes),
        'over': (u'overlays', read_bytes)}
    metadata_types.update(  # little endian
        dict((k[::-1], v) for k, v in metadata_types.items()))

    if not bytecounts:
        raise ValueError(u"no ImageJ metadata")

    if not data[:4] in ('IJIJ', 'JIJI'):
        raise ValueError(u"invalid ImageJ metadata")

    header_size = bytecounts[0]
    if header_size < 12 or header_size > 804:
        raise ValueError(u"invalid ImageJ metadata header size")

    ntypes = (header_size - 4) // 8
    header = struct.unpack(byteorder + u'4sI' * ntypes, data[4:4 + ntypes * 8])
    pos = 4 + ntypes * 8
    counter = 0
    result = {}
    for mtype, count in izip(header[::2], header[1::2]):
        values = []
        name, func = metadata_types.get(mtype, (_str(mtype), read_bytes))
        for _ in xrange(count):
            counter += 1
            pos1 = pos + bytecounts[counter]
            values.append(func(data[pos:pos1], byteorder))
            pos = pos1
        result[name.strip()] = values[0] if count == 1 else values
    return result


def imagej_description(description):
    u"""Return dict from ImageJ image_description tag."""
    def _bool(val):
        return {'true': True, 'false': False}[val.lower()]

    _str = unicode if sys.version_info[0] < 3 else lambda x: unicode(x, u'cp1252')
    result = {}
    for line in description.splitlines():
        try:
            key, val = line.split('=')
        except Exception:
            continue
        key = key.strip()
        val = val.strip()
        for dtype in (int, float, _bool, _str):
            try:
                val = dtype(val)
                break
            except Exception:
                pass
        result[_str(key)] = val
    return result


def _replace_by(module_function, package=None, warn=False):
    u"""Try replace decorated function by module.function."""
    try:
        from importlib import import_module
    except ImportError:
        warnings.warn(u'could not import module importlib')
        return lambda func: func

    def decorate(func, module_function=module_function, warn=warn):
        try:
            module, function = module_function.split(u'.')
            if not package:
                module = import_module(module)
            else:
                module = import_module(u'.' + module, package=package)
            func, oldfunc = getattr(module, function), func
            globals()[u'__old_' + func.__name__] = oldfunc
        except Exception:
            if warn:
                warnings.warn(u"failed to import %s" % module_function)
        return func

    return decorate


def decodejpg(encoded, tables='', photometric=None,
              ycbcr_subsampling=None, ycbcr_positioning=None):
    u"""Decode JPEG encoded byte string (using _czifile extension module)."""
    import _czifile
    image = _czifile.decodejpg(encoded, tables)
    if photometric == u'rgb' and ycbcr_subsampling and ycbcr_positioning:
        # TODO: convert YCbCr to RGB
        pass
    return image.tostring()


@_replace_by(u'_tifffile.decodepackbits')
def decodepackbits(encoded):
    u"""Decompress PackBits encoded byte string.

    PackBits is a simple byte-oriented run-length compression scheme.

    """
    func = ord if sys.version[0] == u'2' else lambda x: x
    result = []
    result_extend = result.extend
    i = 0
    try:
        while True:
            n = func(encoded[i]) + 1
            i += 1
            if n < 129:
                result_extend(encoded[i:i + n])
                i += n
            elif n > 129:
                result_extend(encoded[i:i + 1] * (258 - n))
                i += 1
    except IndexError:
        pass
    return ''.join(result) if sys.version[0] == u'2' else str(result)


@_replace_by(u'_tifffile.decodelzw')
def decodelzw(encoded):
    u"""Decompress LZW (Lempel-Ziv-Welch) encoded TIFF strip (byte string).

    The strip must begin with a CLEAR code and end with an EOI code.

    This is an implementation of the LZW decoding algorithm described in (1).
    It is not compatible with old style LZW compressed files like quad-lzw.tif.

    """
    len_encoded = len(encoded)
    bitcount_max = len_encoded * 8
    unpack = struct.unpack

    if sys.version[0] == u'2':
        newtable = [unichr(i) for i in xrange(256)]
    else:
        newtable = [str([i]) for i in xrange(256)]
    newtable.extend((0, 0))

    def next_code():
        u"""Return integer of `bitw` bits at `bitcount` position in encoded."""
        start = bitcount // 8
        s = encoded[start:start + 4]
        try:
            code = unpack(u'>I', s)[0]
        except Exception:
            code = unpack(u'>I', s + '\x00' * (4 - len(s)))[0]
        code <<= bitcount % 8
        code &= mask
        return code >> shr

    switchbitch = {  # code: bit-width, shr-bits, bit-mask
        255: (9, 23, int(9 * u'1' + u'0' * 23, 2)),
        511: (10, 22, int(10 * u'1' + u'0' * 22, 2)),
        1023: (11, 21, int(11 * u'1' + u'0' * 21, 2)),
        2047: (12, 20, int(12 * u'1' + u'0' * 20, 2)), }
    bitw, shr, mask = switchbitch[255]
    bitcount = 0

    if len_encoded < 4:
        raise ValueError(u"strip must be at least 4 characters long")

    if next_code() != 256:
        raise ValueError(u"strip must begin with CLEAR code")

    code = 0
    oldcode = 0
    result = []
    result_append = result.append
    while True:
        code = next_code()  # ~5% faster when inlining this function
        bitcount += bitw
        if code == 257 or bitcount >= bitcount_max:  # EOI
            break
        if code == 256:  # CLEAR
            table = newtable[:]
            table_append = table.append
            lentable = 258
            bitw, shr, mask = switchbitch[255]
            code = next_code()
            bitcount += bitw
            if code == 257:  # EOI
                break
            result_append(table[code])
        else:
            if code < lentable:
                decoded = table[code]
                newcode = table[oldcode] + decoded[:1]
            else:
                newcode = table[oldcode]
                newcode += newcode[:1]
                decoded = newcode
            result_append(decoded)
            table_append(newcode)
            lentable += 1
        oldcode = code
        if lentable in switchbitch:
            bitw, shr, mask = switchbitch[lentable]

    if code != 257:
        warnings.warn(u"unexpected end of lzw stream (code %i)" % code)

    return ''.join(result)


@_replace_by(u'_tifffile.unpackints')
def unpackints(data, dtype, itemsize, runlen=0):
    u"""Decompress byte string to array of integers of any bit size <= 32.

    Parameters
    ----------
    data : byte str
        Data to decompress.
    dtype : numpy.dtype or str
        A numpy boolean or integer type.
    itemsize : int
        Number of bits per integer.
    runlen : int
        Number of consecutive integers, after which to start at next byte.

    """
    if itemsize == 1:  # bitarray
        data = numpy.fromstring(data, u'|B')
        data = numpy.unpackbits(data)
        if runlen % 8:
            data = data.reshape(-1, runlen + (8 - runlen % 8))
            data = data[:, :runlen].reshape(-1)
        return data.astype(dtype)

    dtype = numpy.dtype(dtype)
    if itemsize in (8, 16, 32, 64):
        return numpy.fromstring(data, dtype)
    if itemsize < 1 or itemsize > 32:
        raise ValueError(u"itemsize out of range: %i" % itemsize)
    if dtype.kind not in u"biu":
        raise ValueError(u"invalid dtype")

    itembytes = i for i in (1, 2, 4, 8) if 8 * i >= itemsize.next()
    if itembytes != dtype.itemsize:
        raise ValueError(u"dtype.itemsize too small")
    if runlen == 0:
        runlen = len(data) // itembytes
    skipbits = runlen * itemsize % 8
    if skipbits:
        skipbits = 8 - skipbits
    shrbits = itembytes * 8 - itemsize
    bitmask = int(itemsize * u'1' + u'0' * shrbits, 2)
    dtypestr = u'>' + dtype.char  # dtype always big endian?

    unpack = struct.unpack
    l = runlen * (len(data) * 8 // (runlen * itemsize + skipbits))
    result = numpy.empty((l, ), dtype)
    bitcount = 0
    for i in xrange(len(result)):
        start = bitcount // 8
        s = data[start:start + itembytes]
        try:
            code = unpack(dtypestr, s)[0]
        except Exception:
            code = unpack(dtypestr, s + '\x00' * (itembytes - len(s)))[0]
        code <<= bitcount % 8
        code &= bitmask
        result[i] = code >> shrbits
        bitcount += itemsize
        if (i + 1) % runlen == 0:
            bitcount += skipbits
    return result


def unpackrgb(data, dtype=u'<B', bitspersample=(5, 6, 5), rescale=True):
    u"""Return array from byte string containing packed samples.

    Use to unpack RGB565 or RGB555 to RGB888 format.

    Parameters
    ----------
    data : byte str
        The data to be decoded. Samples in each pixel are stored consecutively.
        Pixels are aligned to 8, 16, or 32 bit boundaries.
    dtype : numpy.dtype
        The sample data type. The byteorder applies also to the data stream.
    bitspersample : tuple
        Number of bits for each sample in a pixel.
    rescale : bool
        Upscale samples to the number of bits in dtype.

    Returns
    -------
    result : ndarray
        Flattened array of unpacked samples of native dtype.

    Examples
    --------
    >>> data = struct.pack('BBBB', 0x21, 0x08, 0xff, 0xff)
    >>> print(unpackrgb(data, '<B', (5, 6, 5), False))
    [ 1  1  1 31 63 31]
    >>> print(unpackrgb(data, '<B', (5, 6, 5)))
    [  8   4   8 255 255 255]
    >>> print(unpackrgb(data, '<B', (5, 5, 5)))
    [ 16   8   8 255 255 255]

    """
    dtype = numpy.dtype(dtype)
    bits = int(numpy.sum(bitspersample))
    if not (bits <= 32 and all(
            i <= dtype.itemsize * 8 for i in bitspersample)):
        raise ValueError(u"sample size not supported %s" % unicode(bitspersample))
    dt = i for i in u'BHI' if numpy.dtype(i).itemsize * 8 >= bits.next()
    data = numpy.fromstring(data, dtype.byteorder + dt)
    result = numpy.empty((data.size, len(bitspersample)), dtype.char)
    for i, bps in enumerate(bitspersample):
        t = data >> int(numpy.sum(bitspersample[i + 1:]))
        t &= int(u'0b' + u'1' * bps, 2)
        if rescale:
            o = ((dtype.itemsize * 8) // bps + 1) * bps
            if o > data.dtype.itemsize * 8:
                t = t.astype(u'I')
            t *= (2**o - 1) // (2**bps - 1)
            t //= 2**(o - (dtype.itemsize * 8))
        result[:, i] = t
    return result.reshape(-1)


def reorient(image, orientation):
    u"""Return reoriented view of image array.

    Parameters
    ----------
    image : numpy array
        Non-squeezed output of asarray() functions.
        Axes -3 and -2 must be image length and width respectively.
    orientation : int or str
        One of TIFF_ORIENTATIONS keys or values.

    """
    o = TIFF_ORIENTATIONS.get(orientation, orientation)
    if o == u'top_left':
        return image
    elif o == u'top_right':
        return image[..., ::-1, :]
    elif o == u'bottom_left':
        return image[..., ::-1, :, :]
    elif o == u'bottom_right':
        return image[..., ::-1, ::-1, :]
    elif o == u'left_top':
        return numpy.swapaxes(image, -3, -2)
    elif o == u'right_top':
        return numpy.swapaxes(image, -3, -2)[..., ::-1, :]
    elif o == u'left_bottom':
        return numpy.swapaxes(image, -3, -2)[..., ::-1, :, :]
    elif o == u'right_bottom':
        return numpy.swapaxes(image, -3, -2)[..., ::-1, ::-1, :]


def squeeze_axes(shape, axes, skip=u'XY'):
    u"""Return shape and axes with single-dimensional entries removed.

    Remove unused dimensions unless their axes are listed in 'skip'.

    >>> squeeze_axes((5, 1, 2, 1, 1), 'TZYXC')
    ((5, 2, 1), 'TYX')

    """
    if len(shape) != len(axes):
        raise ValueError(u"dimensions of axes and shape don't match")
    shape, axes = izip(*(i for i in izip(shape, axes)
                        if i[0] > 1 or i[1] in skip))
    return shape, u''.join(axes)


def transpose_axes(data, axes, asaxes=u'CTZYX'):
    u"""Return data with its axes permuted to match specified axes.

    A view is returned if possible.

    >>> transpose_axes(numpy.zeros((2, 3, 4, 5)), 'TYXC', asaxes='CTZYX').shape
    (5, 2, 1, 3, 4)

    """
    for ax in axes:
        if ax not in asaxes:
            raise ValueError(u"unknown axis %s" % ax)
    # add missing axes to data
    shape = data.shape
    for ax in reversed(asaxes):
        if ax not in axes:
            axes = ax + axes
            shape = (1,) + shape
    data = data.reshape(shape)
    # transpose axes
    data = data.transpose([axes.index(ax) for ax in asaxes])
    return data


def stack_pages(pages, memmap=False, *args, **kwargs):
    u"""Read data from sequence of TiffPage and stack them vertically.

    If memmap is True, return an array stored in a binary file on disk.
    Additional parameters are passsed to the page asarray function.

    """
    if len(pages) == 0:
        raise ValueError(u"no pages")

    if len(pages) == 1:
        return pages[0].asarray(memmap=memmap, *args, **kwargs)

    result = pages[0].asarray(*args, **kwargs)
    shape = (len(pages),) + result.shape
    if memmap:
        with tempfile.NamedTemporaryFile() as fh:
            result = numpy.memmap(fh, dtype=result.dtype, shape=shape)
    else:
        result = numpy.empty(shape, dtype=result.dtype)

    for i, page in enumerate(pages):
        result[i] = page.asarray(*args, **kwargs)

    return result


def stripnull(string):
    u"""Return string truncated at first null character.

    Clean NULL terminated C strings.

    >>> stripnull(b'string\\x00')
    b'string'

    """
    i = string.find('\x00')
    return string if (i < 0) else string[:i]


def stripascii(string):
    u"""Return string truncated at last byte that is 7bit ASCII.

    Clean NULL separated and terminated TIFF strings.

    >>> stripascii(b'string\\x00string\\n\\x01\\x00')
    b'string\\x00string\\n'
    >>> stripascii(b'\\x00')
    b''

    """
    # TODO: pythonize this
    ord_ = ord if sys.version_info[0] < 3 else lambda x: x
    i = len(string)
    while i:
        i -= 1
        if 8 < ord_(string[i]) < 127:
            break
    else:
        i = -1
    return string[:i + 1]


def format_size(size):
    u"""Return file size as string from byte size."""
    for unit in (u'B', u'KB', u'MB', u'GB', u'TB'):
        if size < 2048:
            return u"%.f %s" % (size, unit)
        size /= 1024.0


def sequence(value):
    u"""Return tuple containing value if value is not a sequence.

    >>> sequence(1)
    (1,)
    >>> sequence([1])
    [1]

    """
    try:
        len(value)
        return value
    except TypeError:
        return value,


def product(iterable):
    u"""Return product of sequence of numbers.

    Equivalent of functools.reduce(operator.mul, iterable, 1).

    >>> product([2**8, 2**30])
    274877906944
    >>> product([])
    1

    """
    prod = 1
    for i in iterable:
        prod *= i
    return prod


def natural_sorted(iterable):
    u"""Return human sorted list of strings.

    E.g. for sorting file names.

    >>> natural_sorted(['f1', 'f2', 'f10'])
    ['f1', 'f2', 'f10']

    """
    def sortkey(x):
        return [(int(c) if c.isdigit() else c) for c in re.split(numbers, x)]
    numbers = re.compile(ur'(\d+)')
    return sorted(iterable, key=sortkey)


def excel_datetime(timestamp, epoch=datetime.datetime.fromordinal(693594)):
    u"""Return datetime object from timestamp in Excel serial format.

    Convert LSM time stamps.

    >>> excel_datetime(40237.029999999795)
    datetime.datetime(2010, 2, 28, 0, 43, 11, 999982)

    """
    return epoch + datetime.timedelta(timestamp)


def julian_datetime(julianday, milisecond=0):
    u"""Return datetime from days since 1/1/4713 BC and ms since midnight.

    Convert Julian dates according to MetaMorph.

    >>> julian_datetime(2451576, 54362783)
    datetime.datetime(2000, 2, 2, 15, 6, 2, 783)

    """
    if julianday <= 1721423:
        # no datetime before year 1
        return None

    a = julianday + 1
    if a > 2299160:
        alpha = math.trunc((a - 1867216.25) / 36524.25)
        a += 1 + alpha - alpha // 4
    b = a + (1524 if a > 1721423 else 1158)
    c = math.trunc((b - 122.1) / 365.25)
    d = math.trunc(365.25 * c)
    e = math.trunc((b - d) / 30.6001)

    day = b - d - math.trunc(30.6001 * e)
    month = e - (1 if e < 13.5 else 13)
    year = c - (4716 if month > 2.5 else 4715)

    hour, milisecond = divmod(milisecond, 1000 * 60 * 60)
    minute, milisecond = divmod(milisecond, 1000 * 60)
    second, milisecond = divmod(milisecond, 1000)

    return datetime.datetime(year, month, day,
                             hour, minute, second, milisecond)


def test_tifffile(directory=u'testimages', verbose=True):
    u"""Read all images in directory.

    Print error message on failure.

    >>> test_tifffile(verbose=False)

    """
    successful = 0
    failed = 0
    start = time.time()
    for f in glob.glob(os.path.join(directory, u'*.*')):
        if verbose:
            print u"\n%s>\n" % f.lower(),; sys.stdout.write(u'')
        t0 = time.time()
        try:
            tif = TiffFile(f, multifile=True)
        except Exception, e:
            if not verbose:
                print f,
            print u"ERROR:", e
            failed += 1
            continue
        try:
            img = tif.asarray()
        except ValueError:
            try:
                img = tif[0].asarray()
            except Exception, e:
                if not verbose:
                    print f,
                print u"ERROR:", e
                failed += 1
                continue
        finally:
            tif.close()
        successful += 1
        if verbose:
            print u"%s, %s %s, %s, %.0f ms" % (
                unicode(tif), unicode(img.shape), img.dtype, tif[0].compression,
                (time.time() - t0) * 1e3)
    if verbose:
        print u"\nSuccessfully read %i of %i files in %.3f s\n" % (
            successful, successful + failed, time.time() - start)


class TIFF_SUBFILE_TYPES(object):

    def __getitem__(self, key):
        result = []
        if key & 1:
            result.append(u'reduced_image')
        if key & 2:
            result.append(u'page')
        if key & 4:
            result.append(u'mask')
        return tuple(result)


TIFF_PHOTOMETRICS = {
    0: u'miniswhite',
    1: u'minisblack',
    2: u'rgb',
    3: u'palette',
    4: u'mask',
    5: u'separated',  # CMYK
    6: u'ycbcr',
    8: u'cielab',
    9: u'icclab',
    10: u'itulab',
    32803: u'cfa',  # Color Filter Array
    32844: u'logl',
    32845: u'logluv',
    34892: u'linear_raw'
}

TIFF_COMPESSIONS = {
    1: None,
    2: u'ccittrle',
    3: u'ccittfax3',
    4: u'ccittfax4',
    5: u'lzw',
    6: u'ojpeg',
    7: u'jpeg',
    8: u'adobe_deflate',
    9: u't85',
    10: u't43',
    32766: u'next',
    32771: u'ccittrlew',
    32773: u'packbits',
    32809: u'thunderscan',
    32895: u'it8ctpad',
    32896: u'it8lw',
    32897: u'it8mp',
    32898: u'it8bl',
    32908: u'pixarfilm',
    32909: u'pixarlog',
    32946: u'deflate',
    32947: u'dcs',
    34661: u'jbig',
    34676: u'sgilog',
    34677: u'sgilog24',
    34712: u'jp2000',
    34713: u'nef',
}

TIFF_DECOMPESSORS = {
    None: lambda x: x,
    u'adobe_deflate': zlib.decompress,
    u'deflate': zlib.decompress,
    u'packbits': decodepackbits,
    u'lzw': decodelzw,
    # 'jpeg': decodejpg
}

TIFF_DATA_TYPES = {
    1: u'1B',   # BYTE 8-bit unsigned integer.
    2: u'1s',   # ASCII 8-bit byte that contains a 7-bit ASCII code;
               #   the last byte must be NULL (binary zero).
    3: u'1H',   # SHORT 16-bit (2-byte) unsigned integer
    4: u'1I',   # LONG 32-bit (4-byte) unsigned integer.
    5: u'2I',   # RATIONAL Two LONGs: the first represents the numerator of
               #   a fraction; the second, the denominator.
    6: u'1b',   # SBYTE An 8-bit signed (twos-complement) integer.
    7: u'1s',   # UNDEFINED An 8-bit byte that may contain anything,
               #   depending on the definition of the field.
    8: u'1h',   # SSHORT A 16-bit (2-byte) signed (twos-complement) integer.
    9: u'1i',   # SLONG A 32-bit (4-byte) signed (twos-complement) integer.
    10: u'2i',  # SRATIONAL Two SLONGs: the first represents the numerator
               #   of a fraction, the second the denominator.
    11: u'1f',  # FLOAT Single precision (4-byte) IEEE format.
    12: u'1d',  # DOUBLE Double precision (8-byte) IEEE format.
    13: u'1I',  # IFD unsigned 4 byte IFD offset.
    # 14: '',   # UNICODE
    # 15: '',   # COMPLEX
    16: u'1Q',  # LONG8 unsigned 8 byte integer (BigTiff)
    17: u'1q',  # SLONG8 signed 8 byte integer (BigTiff)
    18: u'1Q',  # IFD8 unsigned 8 byte IFD offset (BigTiff)
}

TIFF_SAMPLE_FORMATS = {
    1: u'uint',
    2: u'int',
    3: u'float',
    # 4: 'void',
    # 5: 'complex_int',
    6: u'complex',
}

TIFF_SAMPLE_DTYPES = {
    (u'uint', 1): u'?',  # bitmap
    (u'uint', 2): u'B',
    (u'uint', 3): u'B',
    (u'uint', 4): u'B',
    (u'uint', 5): u'B',
    (u'uint', 6): u'B',
    (u'uint', 7): u'B',
    (u'uint', 8): u'B',
    (u'uint', 9): u'H',
    (u'uint', 10): u'H',
    (u'uint', 11): u'H',
    (u'uint', 12): u'H',
    (u'uint', 13): u'H',
    (u'uint', 14): u'H',
    (u'uint', 15): u'H',
    (u'uint', 16): u'H',
    (u'uint', 17): u'I',
    (u'uint', 18): u'I',
    (u'uint', 19): u'I',
    (u'uint', 20): u'I',
    (u'uint', 21): u'I',
    (u'uint', 22): u'I',
    (u'uint', 23): u'I',
    (u'uint', 24): u'I',
    (u'uint', 25): u'I',
    (u'uint', 26): u'I',
    (u'uint', 27): u'I',
    (u'uint', 28): u'I',
    (u'uint', 29): u'I',
    (u'uint', 30): u'I',
    (u'uint', 31): u'I',
    (u'uint', 32): u'I',
    (u'uint', 64): u'Q',
    (u'int', 8): u'b',
    (u'int', 16): u'h',
    (u'int', 32): u'i',
    (u'int', 64): u'q',
    (u'float', 16): u'e',
    (u'float', 32): u'f',
    (u'float', 64): u'd',
    (u'complex', 64): u'F',
    (u'complex', 128): u'D',
    (u'uint', (5, 6, 5)): u'B',
}

TIFF_ORIENTATIONS = {
    1: u'top_left',
    2: u'top_right',
    3: u'bottom_right',
    4: u'bottom_left',
    5: u'left_top',
    6: u'right_top',
    7: u'right_bottom',
    8: u'left_bottom',
}

# TODO: is there a standard for character axes labels?
AXES_LABELS = {
    u'X': u'width',
    u'Y': u'height',
    u'Z': u'depth',
    u'S': u'sample',  # rgb(a)
    u'I': u'series',  # general sequence, plane, page, IFD
    u'T': u'time',
    u'C': u'channel',  # color, emission wavelength
    u'A': u'angle',
    u'P': u'phase',  # formerly F    # P is Position in LSM!
    u'R': u'tile',  # region, point, mosaic
    u'H': u'lifetime',  # histogram
    u'E': u'lambda',  # excitation wavelength
    u'L': u'exposure',  # lux
    u'V': u'event',
    u'Q': u'other',
    # 'M': 'mosaic',  # LSM 6
}

AXES_LABELS.update(dict((v, k) for k, v in AXES_LABELS.items()))

# Map OME pixel types to numpy dtype
OME_PIXEL_TYPES = {
    u'int8': u'i1',
    u'int16': u'i2',
    u'int32': u'i4',
    u'uint8': u'u1',
    u'uint16': u'u2',
    u'uint32': u'u4',
    u'float': u'f4',
    # 'bit': 'bit',
    u'double': u'f8',
    u'complex': u'c8',
    u'double-complex': u'c16',
}

# NIH Image PicHeader v1.63
NIH_IMAGE_HEADER = [
    (u'fileid', u'a8'),
    (u'nlines', u'i2'),
    (u'pixelsperline', u'i2'),
    (u'version', u'i2'),
    (u'oldlutmode', u'i2'),
    (u'oldncolors', u'i2'),
    (u'colors', u'u1', (3, 32)),
    (u'oldcolorstart', u'i2'),
    (u'colorwidth', u'i2'),
    (u'extracolors', u'u2', (6, 3)),
    (u'nextracolors', u'i2'),
    (u'foregroundindex', u'i2'),
    (u'backgroundindex', u'i2'),
    (u'xscale', u'f8'),
    (u'_x0', u'i2'),
    (u'_x1', u'i2'),
    (u'units_t', u'i2'),  # NIH_UNITS_TYPE
    (u'p1', [(u'x', u'i2'), (u'y', u'i2')]),
    (u'p2', [(u'x', u'i2'), (u'y', u'i2')]),
    (u'curvefit_t', u'i2'),  # NIH_CURVEFIT_TYPE
    (u'ncoefficients', u'i2'),
    (u'coeff', u'f8', 6),
    (u'_um_len', u'u1'),
    (u'um', u'a15'),
    (u'_x2', u'u1'),
    (u'binarypic', u'b1'),
    (u'slicestart', u'i2'),
    (u'sliceend', u'i2'),
    (u'scalemagnification', u'f4'),
    (u'nslices', u'i2'),
    (u'slicespacing', u'f4'),
    (u'currentslice', u'i2'),
    (u'frameinterval', u'f4'),
    (u'pixelaspectratio', u'f4'),
    (u'colorstart', u'i2'),
    (u'colorend', u'i2'),
    (u'ncolors', u'i2'),
    (u'fill1', u'3u2'),
    (u'fill2', u'3u2'),
    (u'colortable_t', u'u1'),  # NIH_COLORTABLE_TYPE
    (u'lutmode_t', u'u1'),  # NIH_LUTMODE_TYPE
    (u'invertedtable', u'b1'),
    (u'zeroclip', u'b1'),
    (u'_xunit_len', u'u1'),
    (u'xunit', u'a11'),
    (u'stacktype_t', u'i2'),  # NIH_STACKTYPE_TYPE
]

NIH_COLORTABLE_TYPE = (
    u'CustomTable', u'AppleDefault', u'Pseudo20', u'Pseudo32', u'Rainbow',
    u'Fire1', u'Fire2', u'Ice', u'Grays', u'Spectrum')

NIH_LUTMODE_TYPE = (
    u'PseudoColor', u'OldAppleDefault', u'OldSpectrum', u'GrayScale',
    u'ColorLut', u'CustomGrayscale')

NIH_CURVEFIT_TYPE = (
    u'StraightLine', u'Poly2', u'Poly3', u'Poly4', u'Poly5', u'ExpoFit',
    u'PowerFit', u'LogFit', u'RodbardFit', u'SpareFit1', u'Uncalibrated',
    u'UncalibratedOD')

NIH_UNITS_TYPE = (
    u'Nanometers', u'Micrometers', u'Millimeters', u'Centimeters', u'Meters',
    u'Kilometers', u'Inches', u'Feet', u'Miles', u'Pixels', u'OtherUnits')

NIH_STACKTYPE_TYPE = (
    u'VolumeStack', u'RGBStack', u'MovieStack', u'HSVStack')

# Map Universal Imaging Corporation MetaMorph internal tag ids to name and type
UIC_TAGS = {
    0: (u'auto_scale', int),
    1: (u'min_scale', int),
    2: (u'max_scale', int),
    3: (u'spatial_calibration', int),
    4: (u'x_calibration', Fraction),
    5: (u'y_calibration', Fraction),
    6: (u'calibration_units', unicode),
    7: (u'name', unicode),
    8: (u'thresh_state', int),
    9: (u'thresh_state_red', int),
    10: (u'tagid_10', None),  # undefined
    11: (u'thresh_state_green', int),
    12: (u'thresh_state_blue', int),
    13: (u'thresh_state_lo', int),
    14: (u'thresh_state_hi', int),
    15: (u'zoom', int),
    16: (u'create_time', julian_datetime),
    17: (u'last_saved_time', julian_datetime),
    18: (u'current_buffer', int),
    19: (u'gray_fit', None),
    20: (u'gray_point_count', None),
    21: (u'gray_x', Fraction),
    22: (u'gray_y', Fraction),
    23: (u'gray_min', Fraction),
    24: (u'gray_max', Fraction),
    25: (u'gray_unit_name', unicode),
    26: (u'standard_lut', int),
    27: (u'wavelength', int),
    28: (u'stage_position', u'(%i,2,2)u4'),  # N xy positions as fractions
    29: (u'camera_chip_offset', u'(%i,2,2)u4'),  # N xy offsets as fractions
    30: (u'overlay_mask', None),
    31: (u'overlay_compress', None),
    32: (u'overlay', None),
    33: (u'special_overlay_mask', None),
    34: (u'special_overlay_compress', None),
    35: (u'special_overlay', None),
    36: (u'image_property', read_uic_image_property),
    37: (u'stage_label', u'%ip'),  # N str
    38: (u'autoscale_lo_info', Fraction),
    39: (u'autoscale_hi_info', Fraction),
    40: (u'absolute_z', u'(%i,2)u4'),  # N fractions
    41: (u'absolute_z_valid', u'(%i,)u4'),  # N long
    42: (u'gamma', int),
    43: (u'gamma_red', int),
    44: (u'gamma_green', int),
    45: (u'gamma_blue', int),
    46: (u'camera_bin', int),
    47: (u'new_lut', int),
    48: (u'image_property_ex', None),
    49: (u'plane_property', int),
    50: (u'user_lut_table', u'(256,3)u1'),
    51: (u'red_autoscale_info', int),
    52: (u'red_autoscale_lo_info', Fraction),
    53: (u'red_autoscale_hi_info', Fraction),
    54: (u'red_minscale_info', int),
    55: (u'red_maxscale_info', int),
    56: (u'green_autoscale_info', int),
    57: (u'green_autoscale_lo_info', Fraction),
    58: (u'green_autoscale_hi_info', Fraction),
    59: (u'green_minscale_info', int),
    60: (u'green_maxscale_info', int),
    61: (u'blue_autoscale_info', int),
    62: (u'blue_autoscale_lo_info', Fraction),
    63: (u'blue_autoscale_hi_info', Fraction),
    64: (u'blue_min_scale_info', int),
    65: (u'blue_max_scale_info', int),
    # 66: ('overlay_plane_color', read_uic_overlay_plane_color),
}


# Olympus FluoView
MM_DIMENSION = [
    (u'name', u'a16'),
    (u'size', u'i4'),
    (u'origin', u'f8'),
    (u'resolution', u'f8'),
    (u'unit', u'a64'),
]

MM_HEADER = [
    (u'header_flag', u'i2'),
    (u'image_type', u'u1'),
    (u'image_name', u'a257'),
    (u'offset_data', u'u4'),
    (u'palette_size', u'i4'),
    (u'offset_palette0', u'u4'),
    (u'offset_palette1', u'u4'),
    (u'comment_size', u'i4'),
    (u'offset_comment', u'u4'),
    (u'dimensions', MM_DIMENSION, 10),
    (u'offset_position', u'u4'),
    (u'map_type', u'i2'),
    (u'map_min', u'f8'),
    (u'map_max', u'f8'),
    (u'min_value', u'f8'),
    (u'max_value', u'f8'),
    (u'offset_map', u'u4'),
    (u'gamma', u'f8'),
    (u'offset', u'f8'),
    (u'gray_channel', MM_DIMENSION),
    (u'offset_thumbnail', u'u4'),
    (u'voice_field', u'i4'),
    (u'offset_voice_field', u'u4'),
]

# Carl Zeiss LSM
CZ_LSM_INFO = [
    (u'magic_number', u'u4'),
    (u'structure_size', u'i4'),
    (u'dimension_x', u'i4'),
    (u'dimension_y', u'i4'),
    (u'dimension_z', u'i4'),
    (u'dimension_channels', u'i4'),
    (u'dimension_time', u'i4'),
    (u'data_type', u'i4'),  # CZ_DATA_TYPES
    (u'thumbnail_x', u'i4'),
    (u'thumbnail_y', u'i4'),
    (u'voxel_size_x', u'f8'),
    (u'voxel_size_y', u'f8'),
    (u'voxel_size_z', u'f8'),
    (u'origin_x', u'f8'),
    (u'origin_y', u'f8'),
    (u'origin_z', u'f8'),
    (u'scan_type', u'u2'),
    (u'spectral_scan', u'u2'),
    (u'type_of_data', u'u4'),  # CZ_TYPE_OF_DATA
    (u'offset_vector_overlay', u'u4'),
    (u'offset_input_lut', u'u4'),
    (u'offset_output_lut', u'u4'),
    (u'offset_channel_colors', u'u4'),
    (u'time_interval', u'f8'),
    (u'offset_channel_data_types', u'u4'),
    (u'offset_scan_info', u'u4'),  # CZ_LSM_SCAN_INFO
    (u'offset_ks_data', u'u4'),
    (u'offset_time_stamps', u'u4'),
    (u'offset_event_list', u'u4'),
    (u'offset_roi', u'u4'),
    (u'offset_bleach_roi', u'u4'),
    (u'offset_next_recording', u'u4'),
    # LSM 2.0 ends here
    (u'display_aspect_x', u'f8'),
    (u'display_aspect_y', u'f8'),
    (u'display_aspect_z', u'f8'),
    (u'display_aspect_time', u'f8'),
    (u'offset_mean_of_roi_overlay', u'u4'),
    (u'offset_topo_isoline_overlay', u'u4'),
    (u'offset_topo_profile_overlay', u'u4'),
    (u'offset_linescan_overlay', u'u4'),
    (u'offset_toolbar_flags', u'u4'),
    (u'offset_channel_wavelength', u'u4'),
    (u'offset_channel_factors', u'u4'),
    (u'objective_sphere_correction', u'f8'),
    (u'offset_unmix_parameters', u'u4'),
    # LSM 3.2, 4.0 end here
    (u'offset_acquisition_parameters', u'u4'),
    (u'offset_characteristics', u'u4'),
    (u'offset_palette', u'u4'),
    (u'time_difference_x', u'f8'),
    (u'time_difference_y', u'f8'),
    (u'time_difference_z', u'f8'),
    (u'internal_use_1', u'u4'),
    (u'dimension_p', u'i4'),
    (u'dimension_m', u'i4'),
    (u'dimensions_reserved', u'16i4'),
    (u'offset_tile_positions', u'u4'),
    (u'reserved_1', u'9u4'),
    (u'offset_positions', u'u4'),
    (u'reserved_2', u'21u4'),  # must be 0
]

# Import functions for LSM_INFO sub-records
CZ_LSM_INFO_READERS = {
    u'scan_info': read_cz_lsm_scan_info,
    u'time_stamps': read_cz_lsm_time_stamps,
    u'event_list': read_cz_lsm_event_list,
    u'channel_colors': read_cz_lsm_floatpairs,
    u'positions': read_cz_lsm_floatpairs,
    u'tile_positions': read_cz_lsm_floatpairs,
}

# Map cz_lsm_info.scan_type to dimension order
CZ_SCAN_TYPES = {
    0: u'XYZCT',  # x-y-z scan
    1: u'XYZCT',  # z scan (x-z plane)
    2: u'XYZCT',  # line scan
    3: u'XYTCZ',  # time series x-y
    4: u'XYZTC',  # time series x-z
    5: u'XYTCZ',  # time series 'Mean of ROIs'
    6: u'XYZTC',  # time series x-y-z
    7: u'XYCTZ',  # spline scan
    8: u'XYCZT',  # spline scan x-z
    9: u'XYTCZ',  # time series spline plane x-z
    10: u'XYZCT',  # point mode
}

# Map dimension codes to cz_lsm_info attribute
CZ_DIMENSIONS = {
    u'X': u'dimension_x',
    u'Y': u'dimension_y',
    u'Z': u'dimension_z',
    u'C': u'dimension_channels',
    u'T': u'dimension_time',
}

# Description of cz_lsm_info.data_type
CZ_DATA_TYPES = {
    0: u'varying data types',
    1: u'8 bit unsigned integer',
    2: u'12 bit unsigned integer',
    5: u'32 bit float',
}

# Description of cz_lsm_info.type_of_data
CZ_TYPE_OF_DATA = {
    0: u'Original scan data',
    1: u'Calculated data',
    2: u'3D reconstruction',
    3: u'Topography height map',
}

CZ_LSM_SCAN_INFO_ARRAYS = {
    0x20000000: u"tracks",
    0x30000000: u"lasers",
    0x60000000: u"detection_channels",
    0x80000000: u"illumination_channels",
    0xa0000000: u"beam_splitters",
    0xc0000000: u"data_channels",
    0x11000000: u"timers",
    0x13000000: u"markers",
}

CZ_LSM_SCAN_INFO_STRUCTS = {
    # 0x10000000: "recording",
    0x40000000: u"track",
    0x50000000: u"laser",
    0x70000000: u"detection_channel",
    0x90000000: u"illumination_channel",
    0xb0000000: u"beam_splitter",
    0xd0000000: u"data_channel",
    0x12000000: u"timer",
    0x14000000: u"marker",
}

CZ_LSM_SCAN_INFO_ATTRIBUTES = {
    # recording
    0x10000001: u"name",
    0x10000002: u"description",
    0x10000003: u"notes",
    0x10000004: u"objective",
    0x10000005: u"processing_summary",
    0x10000006: u"special_scan_mode",
    0x10000007: u"scan_type",
    0x10000008: u"scan_mode",
    0x10000009: u"number_of_stacks",
    0x1000000a: u"lines_per_plane",
    0x1000000b: u"samples_per_line",
    0x1000000c: u"planes_per_volume",
    0x1000000d: u"images_width",
    0x1000000e: u"images_height",
    0x1000000f: u"images_number_planes",
    0x10000010: u"images_number_stacks",
    0x10000011: u"images_number_channels",
    0x10000012: u"linscan_xy_size",
    0x10000013: u"scan_direction",
    0x10000014: u"time_series",
    0x10000015: u"original_scan_data",
    0x10000016: u"zoom_x",
    0x10000017: u"zoom_y",
    0x10000018: u"zoom_z",
    0x10000019: u"sample_0x",
    0x1000001a: u"sample_0y",
    0x1000001b: u"sample_0z",
    0x1000001c: u"sample_spacing",
    0x1000001d: u"line_spacing",
    0x1000001e: u"plane_spacing",
    0x1000001f: u"plane_width",
    0x10000020: u"plane_height",
    0x10000021: u"volume_depth",
    0x10000023: u"nutation",
    0x10000034: u"rotation",
    0x10000035: u"precession",
    0x10000036: u"sample_0time",
    0x10000037: u"start_scan_trigger_in",
    0x10000038: u"start_scan_trigger_out",
    0x10000039: u"start_scan_event",
    0x10000040: u"start_scan_time",
    0x10000041: u"stop_scan_trigger_in",
    0x10000042: u"stop_scan_trigger_out",
    0x10000043: u"stop_scan_event",
    0x10000044: u"stop_scan_time",
    0x10000045: u"use_rois",
    0x10000046: u"use_reduced_memory_rois",
    0x10000047: u"user",
    0x10000048: u"use_bc_correction",
    0x10000049: u"position_bc_correction1",
    0x10000050: u"position_bc_correction2",
    0x10000051: u"interpolation_y",
    0x10000052: u"camera_binning",
    0x10000053: u"camera_supersampling",
    0x10000054: u"camera_frame_width",
    0x10000055: u"camera_frame_height",
    0x10000056: u"camera_offset_x",
    0x10000057: u"camera_offset_y",
    0x10000059: u"rt_binning",
    0x1000005a: u"rt_frame_width",
    0x1000005b: u"rt_frame_height",
    0x1000005c: u"rt_region_width",
    0x1000005d: u"rt_region_height",
    0x1000005e: u"rt_offset_x",
    0x1000005f: u"rt_offset_y",
    0x10000060: u"rt_zoom",
    0x10000061: u"rt_line_period",
    0x10000062: u"prescan",
    0x10000063: u"scan_direction_z",
    # track
    0x40000001: u"multiplex_type",  # 0 after line; 1 after frame
    0x40000002: u"multiplex_order",
    0x40000003: u"sampling_mode",  # 0 sample; 1 line average; 2 frame average
    0x40000004: u"sampling_method",  # 1 mean; 2 sum
    0x40000005: u"sampling_number",
    0x40000006: u"acquire",
    0x40000007: u"sample_observation_time",
    0x4000000b: u"time_between_stacks",
    0x4000000c: u"name",
    0x4000000d: u"collimator1_name",
    0x4000000e: u"collimator1_position",
    0x4000000f: u"collimator2_name",
    0x40000010: u"collimator2_position",
    0x40000011: u"is_bleach_track",
    0x40000012: u"is_bleach_after_scan_number",
    0x40000013: u"bleach_scan_number",
    0x40000014: u"trigger_in",
    0x40000015: u"trigger_out",
    0x40000016: u"is_ratio_track",
    0x40000017: u"bleach_count",
    0x40000018: u"spi_center_wavelength",
    0x40000019: u"pixel_time",
    0x40000021: u"condensor_frontlens",
    0x40000023: u"field_stop_value",
    0x40000024: u"id_condensor_aperture",
    0x40000025: u"condensor_aperture",
    0x40000026: u"id_condensor_revolver",
    0x40000027: u"condensor_filter",
    0x40000028: u"id_transmission_filter1",
    0x40000029: u"id_transmission1",
    0x40000030: u"id_transmission_filter2",
    0x40000031: u"id_transmission2",
    0x40000032: u"repeat_bleach",
    0x40000033: u"enable_spot_bleach_pos",
    0x40000034: u"spot_bleach_posx",
    0x40000035: u"spot_bleach_posy",
    0x40000036: u"spot_bleach_posz",
    0x40000037: u"id_tubelens",
    0x40000038: u"id_tubelens_position",
    0x40000039: u"transmitted_light",
    0x4000003a: u"reflected_light",
    0x4000003b: u"simultan_grab_and_bleach",
    0x4000003c: u"bleach_pixel_time",
    # laser
    0x50000001: u"name",
    0x50000002: u"acquire",
    0x50000003: u"power",
    # detection_channel
    0x70000001: u"integration_mode",
    0x70000002: u"special_mode",
    0x70000003: u"detector_gain_first",
    0x70000004: u"detector_gain_last",
    0x70000005: u"amplifier_gain_first",
    0x70000006: u"amplifier_gain_last",
    0x70000007: u"amplifier_offs_first",
    0x70000008: u"amplifier_offs_last",
    0x70000009: u"pinhole_diameter",
    0x7000000a: u"counting_trigger",
    0x7000000b: u"acquire",
    0x7000000c: u"point_detector_name",
    0x7000000d: u"amplifier_name",
    0x7000000e: u"pinhole_name",
    0x7000000f: u"filter_set_name",
    0x70000010: u"filter_name",
    0x70000013: u"integrator_name",
    0x70000014: u"channel_name",
    0x70000015: u"detector_gain_bc1",
    0x70000016: u"detector_gain_bc2",
    0x70000017: u"amplifier_gain_bc1",
    0x70000018: u"amplifier_gain_bc2",
    0x70000019: u"amplifier_offset_bc1",
    0x70000020: u"amplifier_offset_bc2",
    0x70000021: u"spectral_scan_channels",
    0x70000022: u"spi_wavelength_start",
    0x70000023: u"spi_wavelength_stop",
    0x70000026: u"dye_name",
    0x70000027: u"dye_folder",
    # illumination_channel
    0x90000001: u"name",
    0x90000002: u"power",
    0x90000003: u"wavelength",
    0x90000004: u"aquire",
    0x90000005: u"detchannel_name",
    0x90000006: u"power_bc1",
    0x90000007: u"power_bc2",
    # beam_splitter
    0xb0000001: u"filter_set",
    0xb0000002: u"filter",
    0xb0000003: u"name",
    # data_channel
    0xd0000001: u"name",
    0xd0000003: u"acquire",
    0xd0000004: u"color",
    0xd0000005: u"sample_type",
    0xd0000006: u"bits_per_sample",
    0xd0000007: u"ratio_type",
    0xd0000008: u"ratio_track1",
    0xd0000009: u"ratio_track2",
    0xd000000a: u"ratio_channel1",
    0xd000000b: u"ratio_channel2",
    0xd000000c: u"ratio_const1",
    0xd000000d: u"ratio_const2",
    0xd000000e: u"ratio_const3",
    0xd000000f: u"ratio_const4",
    0xd0000010: u"ratio_const5",
    0xd0000011: u"ratio_const6",
    0xd0000012: u"ratio_first_images1",
    0xd0000013: u"ratio_first_images2",
    0xd0000014: u"dye_name",
    0xd0000015: u"dye_folder",
    0xd0000016: u"spectrum",
    0xd0000017: u"acquire",
    # timer
    0x12000001: u"name",
    0x12000002: u"description",
    0x12000003: u"interval",
    0x12000004: u"trigger_in",
    0x12000005: u"trigger_out",
    0x12000006: u"activation_time",
    0x12000007: u"activation_number",
    # marker
    0x14000001: u"name",
    0x14000002: u"description",
    0x14000003: u"trigger_in",
    0x14000004: u"trigger_out",
}

# Map TIFF tag code to attribute name, default value, type, count, validator
TIFF_TAGS = {
    254: (u'new_subfile_type', 0, 4, 1, TIFF_SUBFILE_TYPES()),
    255: (u'subfile_type', None, 3, 1,
          {0: u'undefined', 1: u'image', 2: u'reduced_image', 3: u'page'}),
    256: (u'image_width', None, 4, 1, None),
    257: (u'image_length', None, 4, 1, None),
    258: (u'bits_per_sample', 1, 3, 1, None),
    259: (u'compression', 1, 3, 1, TIFF_COMPESSIONS),
    262: (u'photometric', None, 3, 1, TIFF_PHOTOMETRICS),
    266: (u'fill_order', 1, 3, 1, {1: u'msb2lsb', 2: u'lsb2msb'}),
    269: (u'document_name', None, 2, None, None),
    270: (u'image_description', None, 2, None, None),
    271: (u'make', None, 2, None, None),
    272: (u'model', None, 2, None, None),
    273: (u'strip_offsets', None, 4, None, None),
    274: (u'orientation', 1, 3, 1, TIFF_ORIENTATIONS),
    277: (u'samples_per_pixel', 1, 3, 1, None),
    278: (u'rows_per_strip', 2**32 - 1, 4, 1, None),
    279: (u'strip_byte_counts', None, 4, None, None),
    280: (u'min_sample_value', None, 3, None, None),
    281: (u'max_sample_value', None, 3, None, None),  # 2**bits_per_sample
    282: (u'x_resolution', None, 5, 1, None),
    283: (u'y_resolution', None, 5, 1, None),
    284: (u'planar_configuration', 1, 3, 1, {1: u'contig', 2: u'separate'}),
    285: (u'page_name', None, 2, None, None),
    286: (u'x_position', None, 5, 1, None),
    287: (u'y_position', None, 5, 1, None),
    296: (u'resolution_unit', 2, 4, 1, {1: u'none', 2: u'inch', 3: u'centimeter'}),
    297: (u'page_number', None, 3, 2, None),
    305: (u'software', None, 2, None, None),
    306: (u'datetime', None, 2, None, None),
    315: (u'artist', None, 2, None, None),
    316: (u'host_computer', None, 2, None, None),
    317: (u'predictor', 1, 3, 1, {1: None, 2: u'horizontal'}),
    318: (u'white_point', None, 5, 2, None),
    319: (u'primary_chromaticities', None, 5, 6, None),
    320: (u'color_map', None, 3, None, None),
    322: (u'tile_width', None, 4, 1, None),
    323: (u'tile_length', None, 4, 1, None),
    324: (u'tile_offsets', None, 4, None, None),
    325: (u'tile_byte_counts', None, 4, None, None),
    338: (u'extra_samples', None, 3, None,
          {0: u'unspecified', 1: u'assocalpha', 2: u'unassalpha'}),
    339: (u'sample_format', 1, 3, 1, TIFF_SAMPLE_FORMATS),
    340: (u'smin_sample_value', None, None, None, None),
    341: (u'smax_sample_value', None, None, None, None),
    347: (u'jpeg_tables', None, 7, None, None),
    530: (u'ycbcr_subsampling', 1, 3, 2, None),
    531: (u'ycbcr_positioning', 1, 3, 1, None),
    32996: (u'sgi_datatype', None, None, 1, None),  # use sample_format
    32997: (u'image_depth', None, 4, 1, None),
    32998: (u'tile_depth', None, 4, 1, None),
    33432: (u'copyright', None, 1, None, None),
    33445: (u'md_file_tag', None, 4, 1, None),
    33446: (u'md_scale_pixel', None, 5, 1, None),
    33447: (u'md_color_table', None, 3, None, None),
    33448: (u'md_lab_name', None, 2, None, None),
    33449: (u'md_sample_info', None, 2, None, None),
    33450: (u'md_prep_date', None, 2, None, None),
    33451: (u'md_prep_time', None, 2, None, None),
    33452: (u'md_file_units', None, 2, None, None),
    33550: (u'model_pixel_scale', None, 12, 3, None),
    33922: (u'model_tie_point', None, 12, None, None),
    34665: (u'exif_ifd', None, None, 1, None),
    34735: (u'geo_key_directory', None, 3, None, None),
    34736: (u'geo_double_params', None, 12, None, None),
    34737: (u'geo_ascii_params', None, 2, None, None),
    34853: (u'gps_ifd', None, None, 1, None),
    37510: (u'user_comment', None, None, None, None),
    42112: (u'gdal_metadata', None, 2, None, None),
    42113: (u'gdal_nodata', None, 2, None, None),
    50289: (u'mc_xy_position', None, 12, 2, None),
    50290: (u'mc_z_position', None, 12, 1, None),
    50291: (u'mc_xy_calibration', None, 12, 3, None),
    50292: (u'mc_lens_lem_na_n', None, 12, 3, None),
    50293: (u'mc_channel_name', None, 1, None, None),
    50294: (u'mc_ex_wavelength', None, 12, 1, None),
    50295: (u'mc_time_stamp', None, 12, 1, None),
    50838: (u'imagej_byte_counts', None, None, None, None),
    65200: (u'flex_xml', None, 2, None, None),
    # code: (attribute name, default value, type, count, validator)
}

# Map custom TIFF tag codes to attribute names and import functions
CUSTOM_TAGS = {
    700: (u'xmp', read_bytes),
    34377: (u'photoshop', read_numpy),
    33723: (u'iptc', read_bytes),
    34675: (u'icc_profile', read_bytes),
    33628: (u'uic1tag', read_uic1tag),  # Universal Imaging Corporation STK
    33629: (u'uic2tag', read_uic2tag),
    33630: (u'uic3tag', read_uic3tag),
    33631: (u'uic4tag', read_uic4tag),
    34361: (u'mm_header', read_mm_header),  # Olympus FluoView
    34362: (u'mm_stamp', read_mm_stamp),
    34386: (u'mm_user_block', read_bytes),
    34412: (u'cz_lsm_info', read_cz_lsm_info),  # Carl Zeiss LSM
    43314: (u'nih_image_header', read_nih_image_header),
    # 40001: ('mc_ipwinscal', read_bytes),
    40100: (u'mc_id_old', read_bytes),
    50288: (u'mc_id', read_bytes),
    50296: (u'mc_frame_properties', read_bytes),
    50839: (u'imagej_metadata', read_bytes),
    51123: (u'micromanager_metadata', read_json),
}

# Max line length of printed output
PRINT_LINE_LEN = 79


def imshow(data, title=None, vmin=0, vmax=None, cmap=None,
           bitspersample=None, photometric=u'rgb', interpolation=u'nearest',
           dpi=96, figure=None, subplot=111, maxdim=8192, **kwargs):
    u"""Plot n-dimensional images using matplotlib.pyplot.

    Return figure, subplot and plot axis.
    Requires pyplot already imported ``from matplotlib import pyplot``.

    Parameters
    ----------
    bitspersample : int or None
        Number of bits per channel in integer RGB images.
    photometric : {'miniswhite', 'minisblack', 'rgb', or 'palette'}
        The color space of the image data.
    title : str
        Window and subplot title.
    figure : matplotlib.figure.Figure (optional).
        Matplotlib to use for plotting.
    subplot : int
        A matplotlib.pyplot.subplot axis.
    maxdim : int
        maximum image size in any dimension.
    kwargs : optional
        Arguments for matplotlib.pyplot.imshow.

    """
    # if photometric not in ('miniswhite', 'minisblack', 'rgb', 'palette'):
    #    raise ValueError("Can't handle %s photometrics" % photometric)
    # TODO: handle photometric == 'separated' (CMYK)
    isrgb = photometric in (u'rgb', u'palette')
    data = numpy.atleast_2d(data.squeeze())
    data = data[(slice(0, maxdim), ) * len(data.shape)]

    dims = data.ndim
    if dims < 2:
        raise ValueError(u"not an image")
    elif dims == 2:
        dims = 0
        isrgb = False
    else:
        if isrgb and data.shape[-3] in (3, 4):
            data = numpy.swapaxes(data, -3, -2)
            data = numpy.swapaxes(data, -2, -1)
        elif not isrgb and (data.shape[-1] < data.shape[-2] // 16 and
                            data.shape[-1] < data.shape[-3] // 16 and
                            data.shape[-1] < 5):
            data = numpy.swapaxes(data, -3, -1)
            data = numpy.swapaxes(data, -2, -1)
        isrgb = isrgb and data.shape[-1] in (3, 4)
        dims -= 3 if isrgb else 2

    if photometric == u'palette' and isrgb:
        datamax = data.max()
        if datamax > 255:
            data >>= 8  # possible precision loss
        data = data.astype(u'B')
    elif data.dtype.kind in u'ui':
        if not (isrgb and data.dtype.itemsize <= 1) or bitspersample is None:
            try:
                bitspersample = int(math.ceil(math.log(data.max(), 2)))
            except Exception:
                bitspersample = data.dtype.itemsize * 8
        elif not isinstance(bitspersample, int):
            # bitspersample can be tuple, e.g. (5, 6, 5)
            bitspersample = data.dtype.itemsize * 8
        datamax = 2**bitspersample
        if isrgb:
            if bitspersample < 8:
                data <<= 8 - bitspersample
            elif bitspersample > 8:
                data >>= bitspersample - 8  # precision loss
            data = data.astype(u'B')
    elif data.dtype.kind == u'f':
        datamax = data.max()
        if isrgb and datamax > 1.0:
            if data.dtype.char == u'd':
                data = data.astype(u'f')
            data /= datamax
    elif data.dtype.kind == u'b':
        datamax = 1
    elif data.dtype.kind == u'c':
        raise NotImplementedError(u"complex type")  # TODO: handle complex types

    if not isrgb:
        if vmax is None:
            vmax = datamax
        if vmin is None:
            if data.dtype.kind == u'i':
                dtmin = numpy.iinfo(data.dtype).min
                vmin = numpy.min(data)
                if vmin == dtmin:
                    vmin = numpy.min(data > dtmin)
            if data.dtype.kind == u'f':
                dtmin = numpy.finfo(data.dtype).min
                vmin = numpy.min(data)
                if vmin == dtmin:
                    vmin = numpy.min(data > dtmin)
            else:
                vmin = 0

    pyplot = sys.modules[u'matplotlib.pyplot']

    if figure is None:
        pyplot.rc(u'font', family=u'sans-serif', weight=u'normal', size=8)
        figure = pyplot.figure(dpi=dpi, figsize=(10.3, 6.3), frameon=True,
                               facecolor=u'1.0', edgecolor=u'w')
        try:
            figure.canvas.manager.window.title(title)
        except Exception:
            pass
        pyplot.subplots_adjust(bottom=0.03 * (dims + 2), top=0.9,
                               left=0.1, right=0.95, hspace=0.05, wspace=0.0)
    subplot = pyplot.subplot(subplot)

    if title:
        try:
            title = unicode(title, u'Windows-1252')
        except TypeError:
            pass
        pyplot.title(title, size=11)

    if cmap is None:
        if data.dtype.kind in u'ubf' or vmin == 0:
            cmap = u'cubehelix'
        else:
            cmap = u'coolwarm'
        if photometric == u'miniswhite':
            cmap += u'_r'

    image = pyplot.imshow(data[(0, ) * dims].squeeze(), vmin=vmin, vmax=vmax,
                          cmap=cmap, interpolation=interpolation, **kwargs)

    if not isrgb:
        pyplot.colorbar()  # panchor=(0.55, 0.5), fraction=0.05

    def format_coord(x, y):
        # callback function to format coordinate display in toolbar
        x = int(x + 0.5)
        y = int(y + 0.5)
        try:
            if dims:
                return u"%s @ %s [%4i, %4i]" % (cur_ax_dat[1][y, x],
                                               current, x, y)
            else:
                return u"%s @ [%4i, %4i]" % (data[y, x], x, y)
        except IndexError:
            return u""

    pyplot.gca().format_coord = format_coord

    if dims:
        current = list((0, ) * dims)
        cur_ax_dat = [0, data[tuple(current)].squeeze()]
        sliders = [pyplot.Slider(
            pyplot.axes([0.125, 0.03 * (axis + 1), 0.725, 0.025]),
            u'Dimension %i' % axis, 0, data.shape[axis] - 1, 0, facecolor=u'0.5',
            valfmt=u'%%.0f [%i]' % data.shape[axis]) for axis in xrange(dims)]
        for slider in sliders:
            slider.drawon = False

        def set_image(current, sliders=sliders, data=data):
            # change image and redraw canvas
            cur_ax_dat[1] = data[tuple(current)].squeeze()
            image.set_data(cur_ax_dat[1])
            for ctrl, index in izip(sliders, current):
                ctrl.eventson = False
                ctrl.set_val(index)
                ctrl.eventson = True
            figure.canvas.draw()

        def on_changed(index, axis, data=data, current=current):
            # callback function for slider change event
            index = int(round(index))
            cur_ax_dat[0] = axis
            if index == current[axis]:
                return
            if index >= data.shape[axis]:
                index = 0
            elif index < 0:
                index = data.shape[axis] - 1
            current[axis] = index
            set_image(current)

        def on_keypressed(event, data=data, current=current):
            # callback function for key press event
            key = event.key
            axis = cur_ax_dat[0]
            if unicode(key) in u'0123456789':
                on_changed(key, axis)
            elif key == u'right':
                on_changed(current[axis] + 1, axis)
            elif key == u'left':
                on_changed(current[axis] - 1, axis)
            elif key == u'up':
                cur_ax_dat[0] = 0 if axis == len(data.shape) - 1 else axis + 1
            elif key == u'down':
                cur_ax_dat[0] = len(data.shape) - 1 if axis == 0 else axis - 1
            elif key == u'end':
                on_changed(data.shape[axis] - 1, axis)
            elif key == u'home':
                on_changed(0, axis)

        figure.canvas.mpl_connect(u'key_press_event', on_keypressed)
        for axis, ctrl in enumerate(sliders):
            ctrl.on_changed(lambda k, a=axis: on_changed(k, a))

    return figure, subplot, image


def _app_show():
    u"""Block the GUI. For use as skimage plugin."""
    pyplot = sys.modules[u'matplotlib.pyplot']
    pyplot.show()


def main(argv=None):
    u"""Command line usage main function."""
    if float(sys.version[0:3]) < 2.6:
        print u"This script requires Python version 2.6 or better."
        print u"This is Python version %s" % sys.version
        return 0
    if argv is None:
        argv = sys.argv

    import optparse

    parser = optparse.OptionParser(
        usage=u"usage: %prog [options] path",
        description=u"Display image data in TIFF files.",
        version=u"%%prog %s" % __version__)
    opt = parser.add_option
    opt(u'-p', u'--page', dest=u'page', type=u'int', default=-1,
        help=u"display single page")
    opt(u'-s', u'--series', dest=u'series', type=u'int', default=-1,
        help=u"display series of pages of same shape")
    opt(u'--nomultifile', dest=u'nomultifile', action=u'store_true',
        default=False, help=u"don't read OME series from multiple files")
    opt(u'--noplot', dest=u'noplot', action=u'store_true', default=False,
        help=u"don't display images")
    opt(u'--interpol', dest=u'interpol', metavar=u'INTERPOL', default=u'bilinear',
        help=u"image interpolation method")
    opt(u'--dpi', dest=u'dpi', type=u'int', default=96,
        help=u"set plot resolution")
    opt(u'--debug', dest=u'debug', action=u'store_true', default=False,
        help=u"raise exception on failures")
    opt(u'--test', dest=u'test', action=u'store_true', default=False,
        help=u"try read all images in path")
    opt(u'--doctest', dest=u'doctest', action=u'store_true', default=False,
        help=u"runs the docstring examples")
    opt(u'-v', u'--verbose', dest=u'verbose', action=u'store_true', default=True)
    opt(u'-q', u'--quiet', dest=u'verbose', action=u'store_false')

    settings, path = parser.parse_args()
    path = u' '.join(path)

    if settings.doctest:
        import doctest
        doctest.testmod()
        return 0
    if not path:
        parser.error(u"No file specified")
    if settings.test:
        test_tifffile(path, settings.verbose)
        return 0

    if any(i in path for i in u'?*'):
        path = glob.glob(path)
        if not path:
            print u'no files match the pattern'
            return 0
        # TODO: handle image sequences
        # if len(path) == 1:
        path = path[0]

    print u"Reading file structure...",
    start = time.time()
    try:
        tif = TiffFile(path, multifile=not settings.nomultifile)
    except Exception, e:
        if settings.debug:
            raise
        else:
            print u"\n", e
            sys.exit(0)
    print u"%.3f ms" % ((time.time() - start) * 1e3)

    if tif.is_ome:
        settings.norgb = True

    images = [(None, tif[0 if settings.page < 0 else settings.page])]
    if not settings.noplot:
        print u"Reading image data... ",

        def notnone(x):
            return i for i in x if i is not None.next()
        start = time.time()
        try:
            if settings.page >= 0:
                images = [(tif.asarray(key=settings.page),
                           tif[settings.page])]
            elif settings.series >= 0:
                images = [(tif.asarray(series=settings.series),
                           notnone(tif.series[settings.series].pages))]
            else:
                images = []
                for i, s in enumerate(tif.series):
                    try:
                        images.append(
                            (tif.asarray(series=i), notnone(s.pages)))
                    except ValueError, e:
                        images.append((None, notnone(s.pages)))
                        if settings.debug:
                            raise
                        else:
                            print u"\n* series %i failed: %s... " % (i, e),; sys.stdout.write(u'')
            print u"%.3f ms" % ((time.time() - start) * 1e3)
        except Exception, e:
            if settings.debug:
                raise
            else:
                print e

    tif.close()

    print u"\nTIFF file:", tif
    print
    for i, s in enumerate(tif.series):
        print u"Series %i" % i
        print s
        print
    for i, page in images:
        print page
        print page.tags
        if page.is_palette:
            print u"\nColor Map:", page.color_map.shape, page.color_map.dtype
        for attr in (u'cz_lsm_info', u'cz_lsm_scan_info', u'uic_tags',
                     u'mm_header', u'imagej_tags', u'micromanager_metadata',
                     u'nih_image_header'):
            if hasattr(page, attr):
                print u"\n".join([unicode(u""), unicode(attr.upper()), unicode(Record(getattr(page, attr)))])
        print
        if page.is_micromanager:
            print u'MICROMANAGER_FILE_METADATA'
            print Record(tif.micromanager_metadata)

    if images and not settings.noplot:
        try:
            import matplotlib
            matplotlib.use(u'TkAgg')
            from matplotlib import pyplot
        except ImportError, e:
            warnings.warn(u"failed to import matplotlib.\n%s" % e)
        else:
            for img, page in images:
                if img is None:
                    continue
                vmin, vmax = None, None
                if u'gdal_nodata' in page.tags:
                    try:
                        vmin = numpy.min(img[img > float(page.gdal_nodata)])
                    except ValueError:
                        pass
                if page.is_stk:
                    try:
                        vmin = page.uic_tags[u'min_scale']
                        vmax = page.uic_tags[u'max_scale']
                    except KeyError:
                        pass
                    else:
                        if vmax <= vmin:
                            vmin, vmax = None, None
                title = u"%s\n %s" % (unicode(tif), unicode(page))
                imshow(img, title=title, vmin=vmin, vmax=vmax,
                       bitspersample=page.bits_per_sample,
                       photometric=page.photometric,
                       interpolation=settings.interpol,
                       dpi=settings.dpi)
            pyplot.show()


TIFFfile = TiffFile  # backwards compatibility

if sys.version_info[0] > 2:
    basestring = unicode, str
    unicode = unicode

if __name__ == u"__main__":
    sys.exit(main())
