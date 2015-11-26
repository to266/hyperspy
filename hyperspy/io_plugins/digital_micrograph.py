# -*- coding: utf-8 -*-
# Copyright 2010 Stefano Mazzucco
# Copyright 2011-2015 The HyperSpy developers
#
# This file is part of  HyperSpy. It is a fork of the original PIL dm3 plugin
# written by Stefano Mazzucco.
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

# Plugin to read the Gatan Digital Micrograph(TM) file format


from __future__ import with_statement
from __future__ import division
import os

import numpy as np
import traits.api as t

from hyperspy.misc.io.utils_readfile import *
from hyperspy.exceptions import *
import hyperspy.misc.io.tools
from hyperspy.misc.utils import DictionaryTreeBrowser
from itertools import izip
from io import open


# Plugin characteristics
# ----------------------
format_name = u'Digital Micrograph dm3'
description = u'Read data from Gatan Digital Micrograph (TM) files'
full_support = False
# Recognised file extension
file_extensions = (u'dm3', u'DM3', u'dm4', u'DM4')
default_extension = 0

# Writing features
writes = False
# ----------------------


class DigitalMicrographReader(object):

    u""" Class to read Gatan Digital Micrograph (TM) files.

    Currently it supports versions 3 and 4.

    Attributes
    ----------
    dm_version, endian, tags_dict

    Methods
    -------
    parse_file, parse_header, get_image_dictionaries

    """

    _complex_type = (15, 18, 20)
    simple_type = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

    def __init__(self, f, verbose=False):
        self.verbose = verbose
        self.dm_version = None
        self.endian = None
        self.tags_dict = None
        self.f = f

    def parse_file(self):
        self.f.seek(0)
        self.parse_header()
        self.tags_dict = {u"root": {}}
        number_of_root_tags = self.parse_tag_group()[2]
        if self.verbose is True:
            print u'Total tags in root group:', number_of_root_tags
        self.parse_tags(
            number_of_root_tags,
            group_name=u"root",
            group_dict=self.tags_dict)

    def parse_header(self):
        self.dm_version = read_long(self.f, u"big")
        if self.dm_version not in (3, 4):
            print u'File address:', dm_version[1]
            raise NotImplementedError(
                u"Currently we only support reading DM versions 3 and 4 but "
                u"this file "
                u"seems to be version %s " % self.dm_version)
        self.skipif4()
        filesizeB = read_long(self.f, u"big")
        is_little_endian = read_long(self.f, u"big")

        if self.verbose is True:
            # filesizeMB = filesizeB[3] / 2.**20
            print u'DM version: %i' % self.dm_version
            print u'size %i B' % filesizeB
            print u'Is file Little endian? %s' % bool(is_little_endian)
        if bool(is_little_endian):
            self.endian = u'little'
        else:
            self.endian = u'big'

    def parse_tags(self, ntags, group_name=u'root', group_dict={}):
        u"""Parse the DM file into a dictionary.

        """
        unnammed_data_tags = 0
        unnammed_group_tags = 0
        for tag in xrange(ntags):
            if self.verbose is True:
                print u'Reading tag name at address:', self.f.tell()
            tag_header = self.parse_tag_header()
            tag_name = tag_header[u'tag_name']

            skip = True if (group_name == u"ImageData" and
                            tag_name == u"Data") else False
            if self.verbose is True:
                print u'Tag name:', tag_name[:20]
                print u'Tag ID:', tag_header[u'tag_id']

            if tag_header[u'tag_id'] == 21:  # it's a TagType (DATA)
                if not tag_name:
                    tag_name = u'Data%i' % unnammed_data_tags
                    unnammed_data_tags += 1

                if self.verbose is True:
                    print u'Reading data tag at address:', self.f.tell()

                # Start reading the data
                # Raises IOError if it is wrong
                self.check_data_tag_delimiter()
                self.skipif4()
                infoarray_size = read_long(self.f, u'big')
                if self.verbose:
                    print u"Infoarray size ", infoarray_size
                self.skipif4()
                if infoarray_size == 1:  # Simple type
                    if self.verbose:
                        print u"Reading simple data"
                    etype = read_long(self.f, u"big")
                    data = self.read_simple_data(etype)
                elif infoarray_size == 2:  # String
                    if self.verbose:
                        print u"Reading string"
                    enctype = read_long(self.f, u"big")
                    if enctype != 18:
                        raise IOError(u"Expected 18 (string), got %i" % enctype)
                    string_length = self.parse_string_definition()
                    data = self.read_string(string_length, skip=skip)
                elif infoarray_size == 3:  # Array of simple type
                    if self.verbose:
                        print u"Reading simple array"
                    # Read array header
                    enctype = read_long(self.f, u"big")
                    if enctype != 20:  # Should be 20 if it is an array
                        raise IOError(u"Expected 20 (string), got %i" % enctype)
                    size, enc_eltype = self.parse_array_definition()
                    data = self.read_array(size, enc_eltype, skip=skip)
                elif infoarray_size > 3:
                    enctype = read_long(self.f, u"big")
                    if enctype == 15:  # It is a struct
                        if self.verbose:
                            print u"Reading struct"
                        definition = self.parse_struct_definition()
                        if self.verbose:
                            print u"Struct definition ", definition
                        data = self.read_struct(definition, skip=skip)
                    elif enctype == 20:  # It is an array of complex type
                        # Read complex array info
                        # The structure is
                        # 20 <4>, ?  <4>, enc_dtype <4>, definition <?>,
                        # size <4>
                        self.skipif4()
                        enc_eltype = read_long(self.f, u"big")
                        if enc_eltype == 15:  # Array of structs
                            if self.verbose:
                                print u"Reading array of structs"
                            definition = self.parse_struct_definition()
                            self.skipif4()  # Padding?
                            size = read_long(self.f, u"big")
                            if self.verbose:
                                print u"Struct definition: ", definition
                                print u"Array size: ", size
                            data = self.read_array(
                                size=size,
                                enc_eltype=enc_eltype,
                                extra={u"definition": definition},
                                skip=skip)
                        elif enc_eltype == 18:  # Array of strings
                            if self.verbose:
                                print u"Reading array of strings"
                            string_length = \
                                self.parse_string_definition()
                            size = read_long(self.f, u"big")
                            data = self.read_array(
                                size=size,
                                enc_eltype=enc_eltype,
                                extra={u"length": string_length},
                                skip=skip)
                        elif enc_eltype == 20:  # Array of arrays
                            if self.verbose:
                                print u"Reading array of arrays"
                            el_length, enc_eltype = \
                                self.parse_array_definition()
                            size = read_long(self.f, u"big")
                            data = self.read_array(
                                size=size,
                                enc_eltype=enc_eltype,
                                extra={u"size": el_length},
                                skip=skip)

                else:  # Infoarray_size < 1
                    raise IOError(u"Invalided infoarray size ", infoarray_size)

                if self.verbose:
                    print u"Data: %s" % unicode(data)[:70]
                group_dict[tag_name] = data

            elif tag_header[u'tag_id'] == 20:  # it's a TagGroup (GROUP)
                if not tag_name:
                    tag_name = u'TagGroup%i' % unnammed_group_tags
                    unnammed_group_tags += 1
                if self.verbose is True:
                    print u'Reading Tag group at address:', self.f.tell()
                ntags = self.parse_tag_group(skip4=3)[2]
                group_dict[tag_name] = {}
                self.parse_tags(
                    ntags=ntags,
                    group_name=tag_name,
                    group_dict=group_dict[tag_name])
            else:
                print u'File address:', self.f.tell()
                raise DM3TagIDError(tag_header[u'tag_id'])

    def get_data_reader(self, enc_dtype):
        # _data_type dictionary.
        # The first element of the InfoArray in the TagType
        # will always be one of _data_type keys.
        # the tuple reads: ('read bytes function', 'number of bytes', 'type')

        dtype_dict = {
            2: (read_short, 2, u'h'),
            3: (read_long, 4, u'l'),
            4: (read_ushort, 2, u'H'),  # dm3 uses ushorts for unicode chars
            5: (read_ulong, 4, u'L'),
            6: (read_float, 4, u'f'),
            7: (read_double, 8, u'd'),
            8: (read_boolean, 1, u'B'),
            # dm3 uses chars for 1-Byte signed integers
            9: (read_char, 1, u'b'),
            10: (read_byte, 1, u'b'),   # 0x0a
            11: (read_double, 8, u'l'),  # Unknown, new in DM4
            12: (read_double, 8, u'l'),  # Unknown, new in DM4
            15: (self.read_struct, None, u'struct',),  # 0x0f
            18: (self.read_string, None, u'c'),  # 0x12
            20: (self.read_array, None, u'array'),  # 0x14
        }
        return dtype_dict[enc_dtype]

    def skipif4(self, n=1):
        if self.dm_version == 4:
            self.f.seek(4 * n, 1)

    def parse_array_definition(self):
        u"""Reads and returns the element type and length of the array.

        The position in the file must be just after the
        array encoded dtype.

        """
        self.skipif4()
        enc_eltype = read_long(self.f, u"big")
        self.skipif4()
        length = read_long(self.f, u"big")
        return length, enc_eltype

    def parse_string_definition(self):
        u"""Reads and returns the length of the string.

        The position in the file must be just after the
        string encoded dtype.
        """
        self.skipif4()
        return read_long(self.f, u"big")

    def parse_struct_definition(self):
        u"""Reads and returns the struct definition tuple.

        The position in the file must be just after the
        struct encoded dtype.

        """
        self.f.seek(4, 1)  # Skip the name length
        self.skipif4(2)
        nfields = read_long(self.f, u"big")
        definition = ()
        for ifield in xrange(nfields):
            self.f.seek(4, 1)
            self.skipif4(2)
            definition += (read_long(self.f, u"big"),)

        return definition

    def read_simple_data(self, etype):
        u"""Parse the data of the given DM3 file f
        with the given endianness (byte order).
        The infoArray iarray specifies how to read the data.
        Returns the tuple (file address, data).
        The tag data is stored in the platform's byte order:
        'little' endian for Intel, PC; 'big' endian for Mac, Motorola.
        If skip != 0 the data is actually skipped.
        """
        data = self.get_data_reader(etype)[0](self.f, self.endian)
        if isinstance(data, unicode):
            data = hyperspy.misc.utils.ensure_unicode(data)
        return data

    def read_string(self, length, skip=False):
        u"""Read a string defined by the infoArray iarray from
         file f with a given endianness (byte order).
        endian can be either 'big' or 'little'.

        If it's a tag name, each char is 1-Byte;
        if it's a tag data, each char is 2-Bytes Unicode,
        """
        if skip is True:
            offset = self.f.tell()
            self.f.seek(length, 1)
            return {u'size': length,
                    u'size_bytes': size_bytes,
                    u'offset': offset,
                    u'endian': self.endian, }
        data = ''
        if self.endian == u'little':
            s = L_char
        elif self.endian == u'big':
            s = B_char
        for char in xrange(length):
            data += s.unpack(self.f.read(1))[0]
        try:
            data = data.decode(u'utf8')
        except:
            # Sometimes the dm3 file strings are encoded in latin-1
            # instead of utf8
            data = data.decode(u'latin-1', errors=u'ignore')
        return data

    def read_struct(self, definition, skip=False):
        u"""Read a struct, defined by iarray, from file f
        with a given endianness (byte order).
        Returns a list of 2-tuples in the form
        (fieldAddress, fieldValue).
        endian can be either 'big' or 'little'.

        """
        field_value = []
        size_bytes = 0
        offset = self.f.tell()
        for dtype in definition:
            if dtype in self.simple_type:
                if skip is False:
                    data = self.get_data_reader(dtype)[0](self.f, self.endian)
                    field_value.append(data)
                else:
                    sbytes = self.get_data_reader(dtype)[1]
                    self.f.seek(sbytes, 1)
                    size_bytes += sbytes
            else:
                raise DM3DataTypeError(dtype)
        if skip is False:
            return tuple(field_value)
        else:
            return {u'size': len(definition),
                    u'size_bytes': size_bytes,
                    u'offset': offset,
                    u'endian': self.endian, }

    def read_array(self, size, enc_eltype, extra=None, skip=False):
        u"""Read an array, defined by iarray, from file f
        with a given endianness (byte order).
        endian can be either 'big' or 'little'.

        """
        eltype = self.get_data_reader(enc_eltype)[0]  # same for all elements
        if skip is True:
            if enc_eltype not in self._complex_type:
                size_bytes = self.get_data_reader(enc_eltype)[1] * size
                data = {u"size": size,
                        u"endian": self.endian,
                        u"size_bytes": size_bytes,
                        u"offset": self.f.tell()}
                self.f.seek(size_bytes, 1)  # Skipping data
            else:
                data = eltype(skip=skip, **extra)
                self.f.seek(data[u'size_bytes'] * (size - 1), 1)
                data[u'size'] = size
                data[u'size_bytes'] *= size
        else:
            if enc_eltype in self.simple_type:  # simple type
                data = [eltype(self.f, self.endian)
                        for element in xrange(size)]
                if enc_eltype == 4 and data:  # it's actually a string
                    data = u"".join([unichr(i) for i in data])
            elif enc_eltype in self._complex_type:
                data = [eltype(**extra)
                        for element in xrange(size)]
        return data

    def parse_tag_group(self, skip4=1):
        u"""Parse the root TagGroup of the given DM3 file f.
        Returns the tuple (is_sorted, is_open, n_tags).
        endian can be either 'big' or 'little'.
        """
        is_sorted = read_byte(self.f, u"big")
        is_open = read_byte(self.f, u"big")
        self.skipif4(n=skip4)
        n_tags = read_long(self.f, u"big")
        return bool(is_sorted), bool(is_open), n_tags

    def find_next_tag(self):
        while read_byte(self.f, u"big") not in (20, 21):
            continue
        location = self.f.tell() - 1
        self.f.seek(location)
        tag_id = read_byte(self.f, u"big")
        self.f.seek(location)
        tag_header = self.parse_tag_header()
        if tag_id == 20:
            print u"Tag header length", tag_header[u'tag_name_length']
            if not 20 > tag_header[u'tag_name_length'] > 0:
                print u"Skipping id 20"
                self.f.seek(location + 1)
                self.find_next_tag()
            else:
                self.f.seek(location)
                return
        else:
            try:
                self.check_data_tag_delimiter()
                self.f.seek(location)
                return
            except DM3TagTypeError:
                self.f.seek(location + 1)
                print u"Skipping id 21"
                self.find_next_tag()

    def find_next_data_tag(self):
        while read_byte(self.f, u"big") != 21:
            continue
        position = self.f.tell() - 1
        self.f.seek(position)
        self.parse_tag_header()
        try:
            self.check_data_tag_delimiter()
            self.f.seek(position)
        except DM3TagTypeError:
            self.f.seek(position + 1)
            self.find_next_data_tag()

    def parse_tag_header(self):
        tag_id = read_byte(self.f, u"big")
        tag_name_length = read_short(self.f, u"big")
        tag_name = self.read_string(tag_name_length)
        return {u'tag_id': tag_id,
                u'tag_name_length': tag_name_length,
                u'tag_name': tag_name, }

    def check_data_tag_delimiter(self):
        self.skipif4(2)
        delimiter = self.read_string(4)
        if delimiter != u'%%%%':
            raise DM3TagTypeError(delimiter)

    def get_image_dictionaries(self):
        u"""Returns the image dictionaries of all images in the file except
        the thumbnails.

        Returns
        -------
        dict, None

        """
        if u'ImageList' not in self.tags_dict:
            return None
        if u"Thumbnails" in self.tags_dict:
            thumbnail_idx = [tag[u'ImageIndex'] for key, tag in
                             self.tags_dict[u'Thumbnails'].items()]
        else:
            thumbnail_idx = []
        images = [image for key, image in
                  self.tags_dict[u'ImageList'].items()
                  if not int(key.replace(u"TagGroup", u"")) in
                  thumbnail_idx]
        return images


class ImageObject(object):

    def __init__(self, imdict, file, order=u"C", record_by=None):
        self.imdict = DictionaryTreeBrowser(imdict)
        self.file = file
        self._order = order if order else u"C"
        self._record_by = record_by

    @property
    def shape(self):
        dimensions = self.imdict.ImageData.Dimensions
        shape = tuple([dimension[1] for dimension in dimensions])
        return shape[::-1]  # DM uses image indexing X, Y, Z...

    # For some image stacks created using plugins in Digital Micrograph
    # the metadata under Calibrations.Dimension would not reflect the
    # actual dimensions in the dataset, leading to these images not
    # loading properly. To allow HyperSpy to load these files, any missing
    # dimensions in the metadata is appended with "dummy" values.
    # This is done for the offsets, scales and units properties, using
    # the len_diff variable
    @property
    def offsets(self):
        dimensions = self.imdict.ImageData.Calibrations.Dimension
        len_diff = len(self.shape) - len(dimensions)
        origins = np.array([dimension[1].Origin for dimension in dimensions])
        origins = np.append(origins, (0.0,) * len_diff)
        return -1 * origins[::-1] * self.scales

    @property
    def scales(self):
        dimensions = self.imdict.ImageData.Calibrations.Dimension
        len_diff = len(self.shape) - len(dimensions)
        scales = np.array([dimension[1].Scale for dimension in dimensions])
        scales = np.append(scales, (1.0,) * len_diff)
        return scales[::-1]

    @property
    def units(self):
        dimensions = self.imdict.ImageData.Calibrations.Dimension
        len_diff = len(self.shape) - len(dimensions)
        return (tuple([dimension[1].Units
                       if dimension[1].Units else u""
                       for dimension in dimensions]) + (u'',) * len_diff)[::-1]

    @property
    def names(self):
        names = [t.Undefined] * len(self.shape)
        indices = xrange(len(self.shape))
        if self.signal_type == u"EELS":
            if u"eV" in self.units:
                names[indices.pop(self.units.index(u"eV"))] = u"Energy loss"
        elif self.signal_type in (u"EDS", u"EDX"):
            if u"keV" in self.units:
                names[indices.pop(self.units.index(u"keV"))] = u"Energy"
        for index, name in izip(indices[::-1], (u"x", u"y", u"z")):
            names[index] = name
        return names

    @property
    def title(self):
        if u"Name" in self.imdict:
            return self.imdict.Name
        else:
            return u''

    @property
    def record_by(self):
        if self._record_by is not None:
            return self._record_by
        if len(self.scales) == 1:
            return u"spectrum"
        elif ((u'ImageTags.Meta_Data.Format' in self.imdict and
               self.imdict.ImageTags.Meta_Data.Format in (u"Spectrum image",
                                                          u"Spectrum")) or (
                u"ImageTags.spim" in self.imdict)) and len(self.scales) == 2:
            return u"spectrum"
        else:
            return u"image"

    @property
    def to_spectrum(self):
        if ((u'ImageTags.Meta_Data.Format' in self.imdict and
                self.imdict.ImageTags.Meta_Data.Format == u"Spectrum image") or
                (u"ImageTags.spim" in self.imdict)) and len(self.scales) > 2:
            return True
        else:
            return False

    @property
    def order(self):
        return self._order

    @property
    def intensity_calibration(self):
        ic = self.imdict.ImageData.Calibrations.Brightness.as_dictionary()
        if not ic[u'Units']:
            ic[u'Units'] = u""
        return ic

    @property
    def dtype(self):
        # Image data types (Image Object chapter on DM help)#
        # key = DM data type code
        # value = numpy data type
        if self.imdict.ImageData.DataType == 4:
            raise NotImplementedError(
                u"Reading data of this type is not implemented.")

        imdtype_dict = {
            0: u'not_implemented',  # null
            1: u'int16',
            2: u'float32',
            3: u'complex64',
            5: u'float32',  # not numpy: 8-Byte packed complex (FFT data)
            6: u'uint8',
            7: u'int32',
            8: np.dtype({u'names': [u'B', u'G', u'R', u'A'],
                         u'formats': [u'u1', u'u1', u'u1', u'u1']}),
            9: u'int8',
            10: u'uint16',
            11: u'uint32',
            12: u'float64',
            13: u'complex128',
            14: u'bool',
            23: np.dtype({u'names': [u'B', u'G', u'R', u'A'],
                          u'formats': [u'u1', u'u1', u'u1', u'u1']}),
            27: u'complex64',  # not numpy: 8-Byte packed complex (FFT data)
            28: u'complex128',  # not numpy: 16-Byte packed complex (FFT data)
        }
        return imdtype_dict[self.imdict.ImageData.DataType]

    @property
    def signal_type(self):
        if u'ImageTags.Meta_Data.Signal' in self.imdict:
            if self.imdict.ImageTags.Meta_Data.Signal == u"X-ray":
                return u"EDS_TEM"
            return self.imdict.ImageTags.Meta_Data.Signal
        elif u'ImageTags.spim.eels' in self.imdict:  # Orsay's tag group
            return u"EELS"
        else:
            return u""

    def _get_data_array(self):
        self.file.seek(self.imdict.ImageData.Data.offset)
        count = self.imdict.ImageData.Data.size
        if self.imdict.ImageData.DataType in (27, 28):  # Packed complex
            count = int(count / 2)
        return np.fromfile(self.file,
                           dtype=self.dtype,
                           count=count)

    @property
    def size(self):
        if self.imdict.ImageData.DataType in (27, 28):  # Packed complex
            if self.imdict.ImageData.Data.size % 2:
                raise IOError(
                    u"ImageData.Data.size should be an even integer for "
                    u"this datatype.")
            else:
                return int(self.imdict.ImageData.Data.size / 2)
        else:
            return self.imdict.ImageData.Data.size

    def get_data(self):
        if isinstance(self.imdict.ImageData.Data, np.ndarray):
            return self.imdict.ImageData.Data
        data = self._get_data_array()
        if self.imdict.ImageData.DataType in (27, 28):  # New packed complex
            return self.unpack_new_packed_complex(data)
        elif self.imdict.ImageData.DataType == 5:  # Old packed compled
            return self.unpack_packed_complex(data)
        elif self.imdict.ImageData.DataType in (8, 23):  # ABGR
            # Reorder the fields
            data = np.hstack((data[[u"B", u"G", u"R"]].view((u"u1", 3))[..., ::-1],
                              data[u"A"].reshape(-1, 1))).view(
                {u"names": (u"R", u"G", u"B", u"A"),
                 u"formats": (u"u1",) * 4}).copy()
        return data.reshape(self.shape, order=self.order)

    def unpack_new_packed_complex(self, data):
        packed_shape = (self.shape[0], int(self.shape[1] / 2 + 1))
        data = data.reshape(packed_shape, order=self.order)
        return np.hstack((data[:, ::-1], np.conjugate(data[:, 1:-1])))

    def unpack_packed_complex(self, tmpdata):
        shape = self.shape
        if shape[0] != shape[1] or len(shape) > 2:
            msg = u"Packed complex format works only for a 2Nx2N image"
            msg += u" -> width == height"
            print msg
            raise IOError(
                u'Unable to read this DM file in packed complex format. '
                u'Pleare report the issue to the HyperSpy developers providing'
                u' the file if possible')
        N = int(self.shape[0] / 2)      # think about a 2Nx2N matrix
        # create an empty 2Nx2N ndarray of complex
        data = np.zeros(shape, dtype=u"complex64")

        # fill in the real values:
        data[N, 0] = tmpdata[0]
        data[0, 0] = tmpdata[1]
        data[N, N] = tmpdata[2 * N ** 2]  # Nyquist frequency
        data[0, N] = tmpdata[2 * N ** 2 + 1]  # Nyquist frequency

        # fill in the non-redundant complex values:
        # top right quarter, except 1st column
        for i in xrange(N):  # this could be optimized
            start = 2 * i * N + 2
            stop = start + 2 * (N - 1) - 1
            step = 2
            realpart = tmpdata[start:stop:step]
            imagpart = tmpdata[start + 1:stop + 1:step]
            data[i, N + 1:2 * N] = realpart + imagpart * 1j
        # 1st column, bottom left quarter
        start = 2 * N
        stop = start + 2 * N * (N - 1) - 1
        step = 2 * N
        realpart = tmpdata[start:stop:step]
        imagpart = tmpdata[start + 1:stop + 1:step]
        data[N + 1:2 * N, 0] = realpart + imagpart * 1j
        # 1st row, bottom right quarter
        start = 2 * N ** 2 + 2
        stop = start + 2 * (N - 1) - 1
        step = 2
        realpart = tmpdata[start:stop:step]
        imagpart = tmpdata[start + 1:stop + 1:step]
        data[N, N + 1:2 * N] = realpart + imagpart * 1j
        # bottom right quarter, except 1st row
        start = stop + 1
        stop = start + 2 * N * (N - 1) - 1
        step = 2
        realpart = tmpdata[start:stop:step]
        imagpart = tmpdata[start + 1:stop + 1:step]
        complexdata = realpart + imagpart * 1j
        data[
            N +
            1:2 *
            N,
            N:2 *
            N] = complexdata.reshape(
            N -
            1,
            N,
            order=self.order)

        # fill in the empty pixels: A(i)(j) = A(2N-i)(2N-j)*
        # 1st row, top left quarter, except 1st element
        data[0, 1:N] = np.conjugate(data[0, -1:-N:-1])
        # 1st row, bottom left quarter, except 1st element
        data[N, 1:N] = np.conjugate(data[N, -1:-N:-1])
        # 1st column, top left quarter, except 1st element
        data[1:N, 0] = np.conjugate(data[-1:-N:-1, 0])
        # 1st column, top right quarter, except 1st element
        data[1:N, N] = np.conjugate(data[-1:-N:-1, N])
        # top left quarter, except 1st row and 1st column
        data[1:N, 1:N] = np.conjugate(data[-1:-N:-1, -1:-N:-1])
        # bottom left quarter, except 1st row and 1st column
        data[N + 1:2 * N, 1:N] = np.conjugate(data[-N - 1:-2 * N:-1, -1:-N:-1])

        return data

    def get_axes_dict(self):
        return [{u'name': name,
                 u'size': size,
                 u'index_in_array': i,
                 u'scale': scale,
                 u'offset': offset,
                 u'units': unicode(units), }
                for i, (name, size, scale, offset, units) in enumerate(
                    izip(self.names, self.shape, self.scales, self.offsets,
                        self.units))]

    def get_metadata(self, metadata={}):
        if u"General" not in metadata:
            metadata[u'General'] = {}
        if u"Signal" not in metadata:
            metadata[u'Signal'] = {}
        metadata[u'General'][u'title'] = self.title
        metadata[u"Signal"][u'record_by'] = self.record_by
        metadata[u"Signal"][u'signal_type'] = self.signal_type
        return metadata

mapping = {
    u"ImageList.TagGroup0.ImageTags.EELS.Experimental_Conditions." +
    u"Collection_semi_angle_mrad": (
        u"Acquisition_instrument.TEM.Detector.EELS.collection_angle",
        None),
    u"ImageList.TagGroup0.ImageTags.EELS.Experimental_Conditions." +
    u"Convergence_semi_angle_mrad": (
        u"Acquisition_instrument.TEM.convergence_angle",
        None),
    u"ImageList.TagGroup0.ImageTags.Acquisition.Parameters.Detector." +
    u"exposure_s": (
        u"Acquisition_instrument.TEM.dwell_time",
        None),
    u"ImageList.TagGroup0.ImageTags.Microscope_Info.Voltage": (
        u"Acquisition_instrument.TEM.beam_energy",
        lambda x: x / 1e3),
    u"ImageList.TagGroup0.ImageTags.EDS.Detector_Info.Azimuthal_angle": (
        u"Acquisition_instrument.TEM.Detector.EDS.azimuth_angle",
        None),
    u"ImageList.TagGroup0.ImageTags.EDS.Detector_Info.Elevation_angle": (
        u"Acquisition_instrument.TEM.Detector.EDS.elevation_angle",
        None),
    u"ImageList.TagGroup0.ImageTags.EDS.Detector_Info.Stage_tilt": (
        u"Acquisition_instrument.TEM.tilt_stage",
        None),
    u"ImageList.TagGroup0.ImageTags.EDS.Solid_angle": (
        u"Acquisition_instrument.TEM.Detector.EDS.solid_angle",
        None),
    u"ImageList.TagGroup0.ImageTags.EDS.Live_time": (
        u"Acquisition_instrument.TEM.Detector.EDS.live_time",
        None),
    u"ImageList.TagGroup0.ImageTags.EDS.Real_time": (
        u"Acquisition_instrument.TEM.Detector.EDS.real_time",
        None),
}


def file_reader(filename, record_by=None, order=None, verbose=False):
    u"""Reads a DM3 file and loads the data into the appropriate class.
    data_id can be specified to load a given image within a DM3 file that
    contains more than one dataset.

    Parameters
    ----------
    record_by: Str
        One of: SI, Image
    order: Str
        One of 'C' or 'F'

    """

    with open(filename, u"rb") as f:
        dm = DigitalMicrographReader(f, verbose=verbose)
        dm.parse_file()
        images = [ImageObject(imdict, f, order=order, record_by=record_by)
                  for imdict in dm.get_image_dictionaries()]
        imd = []
        del dm.tags_dict[u'ImageList']
        dm.tags_dict[u'ImageList'] = {}

        for image in images:
            dm.tags_dict[u'ImageList'][
                u'TagGroup0'] = image.imdict.as_dictionary()
            axes = image.get_axes_dict()
            mp = image.get_metadata()
            mp[u'General'][u'original_filename'] = os.path.split(filename)[1]
            post_process = []
            if image.to_spectrum is True:
                post_process.append(lambda s: s.to_spectrum())
            post_process.append(lambda s: s.squeeze())
            imd.append(
                {u'data': image.get_data(),
                 u'axes': axes,
                 u'metadata': mp,
                 u'original_metadata': dm.tags_dict,
                 u'post_process': post_process,
                 u'mapping': mapping,
                 })

    return imd
