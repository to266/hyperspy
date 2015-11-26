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
import struct
from glob import glob
import os
import xml.etree.ElementTree as ET
from io import open
try:
    from collections import OrderedDict
    ordict = True
except ImportError:
    ordict = False

import numpy as np
import traits.api as t

from hyperspy.misc.array_tools import sarray2dict
from hyperspy.misc.utils import DictionaryTreeBrowser

ser_extensions = (u'ser', u'SER')
emi_extensions = (u'emi', u'EMI')
# Plugin characteristics
# ----------------------
format_name = u'FEI TIA'
description = u''
full_support = False
# Recognised file extension
file_extensions = ser_extensions + emi_extensions
default_extension = 0

# Writing capabilities
writes = False
# ----------------------

data_types = {
    u'1': u'<u1',
    u'2': u'<u2',
    u'3': u'<u4',
    u'4': u'<i1',
    u'5': u'<i2',
    u'6': u'<i4',
    u'7': u'<f4',
    u'8': u'<f8',
    u'9': u'<c8',
    u'10': u'<c16',
}


def readLELong(file):
    u"""Read 4 bytes as *little endian* integer in file"""
    read_bytes = file.read(4)
    return struct.unpack(u'<L', read_bytes)[0]


def readLEShort(file):
    u"""Read 2 bytes as *little endian* integer in file"""
    read_bytes = file.read(2)
    return struct.unpack(u'<H', read_bytes)[0]


def dimension_array_dtype(n, DescriptionLength, UnitsLength):
    dt_list = [
        (u"Dim-%s_DimensionSize" % n, (u"<u4")),
        (u"Dim-%s_CalibrationOffset" % n, u"<f8"),
        (u"Dim-%s_CalibrationDelta" % n, u"<f8"),
        (u"Dim-%s_CalibrationElement" % n, u"<u4"),
        (u"Dim-%s_DescriptionLength" % n, u"<u4"),
        (u"Dim-%s_Description" % n, (unicode, DescriptionLength)),
        (u"Dim-%s_UnitsLength" % n, u"<u4"),
        (u"Dim-%s_Units" % n, (unicode, UnitsLength)),
    ]
    return dt_list


def get_lengths(file):
    file.seek(24, 1)
    description_length = readLELong(file)
    file.seek(description_length, 1)
    unit_length = readLELong(file)
    file.seek(unit_length, 1)
    return description_length, unit_length


def get_header_dtype_list(file):
    header_list = [
        (u"ByteOrder", (u"<u2")),
        (u"SeriesID", u"<u2"),
        (u"SeriesVersion", u"<u2"),
        (u"DataTypeID", u"<u4"),
        (u"TagTypeID", u"<u4"),
        (u"TotalNumberElements", u"<u4"),
        (u"ValidNumberElements", u"<u4"),
        (u"OffsetArrayOffset", u"<u4"),
        (u"NumberDimensions", u"<u4"),
    ]
    header = np.fromfile(file,
                         dtype=np.dtype(header_list),
                         count=1)
    # Go to the beginning of the dimension array section
    file.seek(30)
    for n in xrange(1, header[u"NumberDimensions"] + 1):
        description_length, unit_length = get_lengths(file)
        header_list += dimension_array_dtype(
            n, description_length, unit_length)
    file.seek(0)
    return header_list


def get_data_dtype_list(file, offset, record_by):
    if record_by == u'spectrum':
        file.seek(offset + 20)
        data_type = readLEShort(file)
        array_size = readLELong(file)
        header = [
            (u"CalibrationOffset", (u"<f8")),
            (u"CalibrationDelta", u"<f8"),
            (u"CalibrationElement", u"<u4"),
            (u"DataType", u"<u2"),
            (u"ArrayLength", u"<u4"),
            (u"Array", (data_types[unicode(data_type)], array_size)),
        ]
    elif record_by == u'image':  # Untested
        file.seek(offset + 40)
        data_type = readLEShort(file)
        array_size_x = readLELong(file)
        array_size_y = readLELong(file)
        array_size = array_size_x * array_size_y
        header = [
            (u"CalibrationOffsetX", (u"<f8")),
            (u"CalibrationDeltaX", u"<f8"),
            (u"CalibrationElementX", u"<u4"),
            (u"CalibrationOffsetY", (u"<f8")),
            (u"CalibrationDeltaY", u"<f8"),
            (u"CalibrationElementY", u"<u4"),
            (u"DataType", u"<u2"),
            (u"ArraySizeX", u"<u4"),
            (u"ArraySizeY", u"<u4"),
            (u"Array",
             (data_types[unicode(data_type)], (array_size_x, array_size_y))),
        ]
    return header


def get_data_tag_dtype_list(data_type_id):
    # "TagTypeID" = 16706
    if data_type_id == 16706:
        header = [
            (u"TagTypeID", (u"<u2")),
            (u"Unknown", (u"<u2")),  # Not in Boothroyd description. = 0
            (u"Time", u"<u4"),   # The precision is one second...
            (u"PositionX", u"<f8"),
            (u"PositionY", u"<f8"),
        ]
    else:  # elif data_type_id == ?????
        header = [
            (u"TagTypeID", (u"<u2")),
            # Not in Boothroyd description. = 0. Not tested.
            (u"Unknown", (u"<u2")),
            (u"Time", u"<u4"),   # The precision is one second...
        ]
    return header


def print_struct_array_values(struct_array):
    for key in struct_array.dtype.names:
        if not isinstance(struct_array[key], np.ndarray) or \
                np.array(struct_array[key].shape).sum() == 1:
            print u"%s : %s" % (key, struct_array[key])
        else:
            print u"%s : Array" % key


def guess_record_by(record_by_id):
    if record_by_id == 16672:
        return u'spectrum'
    else:
        return u'image'


def parse_ExperimentalDescription(et, dictree):
    dictree.add_node(et.tag)
    dictree = dictree[et.tag]
    for data in et.find(u"Root").findall(u"Data"):
        label = data.find(u"Label").text
        value = data.find(u"Value").text
        units = data.find(u"Unit").text
        item = label if not units else label + u"_%s" % units
        value = float(value) if units else value
        dictree[item] = value


def parse_TrueImageHeaderInfo(et, dictree):
    dictree.add_node(et.tag)
    dictree = dictree[et.tag]
    et = ET.fromstring(et.text)
    for data in et.findall(u"Data"):
        dictree[data.find(u"Index").text] = float(data.find(u"Value").text)


def emixml2dtb(et, dictree):
    if et.tag == u"ExperimentalDescription":
        parse_ExperimentalDescription(et, dictree)
        return
    elif et.tag == u"TrueImageHeaderInfo":
        parse_TrueImageHeaderInfo(et, dictree)
        return
    if et.text:
        dictree[et.tag] = et.text
        return
    else:
        dictree.add_node(et.tag)
        for child in et:
            emixml2dtb(child, dictree[et.tag])


def emi_reader(filename, dump_xml=False, verbose=False, **kwds):
    # TODO: recover the tags from the emi file. It is easy: just look for
    # <ObjectInfo> and </ObjectInfo>. It is standard xml :)
    objects = get_xml_info_from_emi(filename)
    filename = os.path.splitext(filename)[0]
    if dump_xml is True:
        for i, obj in enumerate(objects):
            with open(filename + u'-object-%s.xml' % i, u'w') as f:
                f.write(obj)

    ser_files = glob(filename + u'_[0-9].ser')
    sers = []
    for f in ser_files:
        if verbose is True:
            print u"Opening ", f
        try:
            sers.append(ser_reader(f, objects))
        except IOError:  # Probably a single spectrum that we don't support
            continue

        index = int(os.path.splitext(f)[0].split(u"_")[-1]) - 1
        op = DictionaryTreeBrowser(sers[-1][u'original_metadata'])
        emixml2dtb(ET.fromstring(objects[index]), op)
        sers[-1][u'original_metadata'] = op.as_dictionary()
    return sers


def file_reader(filename, *args, **kwds):
    ext = os.path.splitext(filename)[1][1:]
    if ext in ser_extensions:
        return [ser_reader(filename, *args, **kwds), ]
    elif ext in emi_extensions:
        return emi_reader(filename, *args, **kwds)


def load_ser_file(filename, verbose=False):
    if verbose:
        print u"Opening the file: ", filename
    with open(filename, u'rb') as f:
        header = np.fromfile(f,
                             dtype=np.dtype(get_header_dtype_list(f)),
                             count=1)
        if verbose is True:
            print u"Extracting the information"
            print u"\n"
            print u"Header info:"
            print u"------------"
            print_struct_array_values(header[0])

        if header[u'ValidNumberElements'] == 0:
            raise IOError(
                u"The file does not contains valid data. "
                u"If it is a single spectrum, the data is contained in the  "
                u".emi file but HyperSpy cannot currently extract this information.")

        # Read the first element of data offsets
        f.seek(header[u"OffsetArrayOffset"][0])
        data_offsets = readLELong(f)
        data_dtype_list = get_data_dtype_list(
            f,
            data_offsets,
            guess_record_by(header[u'DataTypeID']))
        tag_dtype_list = get_data_tag_dtype_list(header[u'TagTypeID'])
        f.seek(data_offsets)
        data = np.fromfile(f,
                           dtype=np.dtype(data_dtype_list + tag_dtype_list),
                           count=header[u"TotalNumberElements"])
        if verbose is True:
            print u"\n"
            print u"Data info:"
            print u"----------"
            print_struct_array_values(data[0])
    return header, data


def get_xml_info_from_emi(emi_file):
    with open(emi_file, u'rb') as f:
        tx = f.read()
    objects = []
    i_start = 0
    while i_start != -1:
        i_start += 1
        i_start = tx.find(u'<ObjectInfo>', i_start)
        i_end = tx.find(u'</ObjectInfo>', i_start)
        objects.append(tx[i_start:i_end + 13])
    return objects[:-1]


def ser_reader(filename, objects=None, verbose=False, *args, **kwds):
    u"""Reads the information from the file and returns it in the HyperSpy
    required format.

    """

    header, data = load_ser_file(filename, verbose=verbose)
    record_by = guess_record_by(header[u'DataTypeID'])
    axes = []
    ndim = int(header[u'NumberDimensions'])
    if record_by == u'spectrum':
        array_shape = [None, ] * int(ndim)
        if len(data[u'PositionY']) > 1 and \
                (data[u'PositionY'][0] == data[u'PositionY'][1]):
            # The spatial dimensions are stored in F order i.e. X, Y, ...
            order = u"F"
        else:
            # The spatial dimensions are stored in C order i.e. ..., Y, X
            order = u"C"
        # Extra dimensions
        for i in xrange(ndim):
            if i == ndim - 1:
                name = u'x'
            elif i == ndim - 2:
                name = u'y'
            else:
                name = t.Undefined
            idim = 1 + i if order == u"C" else ndim - i
            axes.append({
                u'name': name,
                u'offset': header[u'Dim-%i_CalibrationOffset' % idim][0],
                u'scale': header[u'Dim-%i_CalibrationDelta' % idim][0],
                u'units': header[u'Dim-%i_Units' % idim][0],
                u'size': header[u'Dim-%i_DimensionSize' % idim][0],
                u'index_in_array': i
            })
            array_shape[i] = \
                header[u'Dim-%i_DimensionSize' % idim][0]
        # FEI seems to use the international system of units (SI) for the
        # spatial scale. However, we prefer to work in nm
        for axis in axes:
            if axis[u'units'] == u'meters':
                axis[u'units'] = u'nm'
                axis[u'scale'] *= 10 ** 9

        # Spectral dimension
        axes.append({
            u'offset': data[u'CalibrationOffset'][0],
            u'scale': data[u'CalibrationDelta'][0],
            u'size': data[u'ArrayLength'][0],
            u'index_in_array': header[u'NumberDimensions'][0]
        })

        # FEI seems to use the international system of units (SI) for the
        # energy scale (eV).
        axes[-1][u'units'] = u'eV'
        axes[-1][u'name'] = u'Energy'

        array_shape.append(data[u'ArrayLength'][0])

    elif record_by == u'image':
        array_shape = []
        # Extra dimensions
        for i in xrange(ndim):
            if header[u'Dim-%i_DimensionSize' % (i + 1)][0] != 1:
                axes.append({
                    u'offset': header[u'Dim-%i_CalibrationOffset' % (i + 1)][0],
                    u'scale': header[u'Dim-%i_CalibrationDelta' % (i + 1)][0],
                    u'units': header[u'Dim-%i_Units' % (i + 1)][0],
                    u'size': header[u'Dim-%i_DimensionSize' % (i + 1)][0],
                })
            array_shape.append(header[u'Dim-%i_DimensionSize' % (i + 1)][0])
        # Y axis
        axes.append({
            u'name': u'y',
            u'offset': data[u'CalibrationOffsetY'][0] -
            data[u'CalibrationElementY'][0] * data[u'CalibrationDeltaY'][0],
            u'scale': data[u'CalibrationDeltaY'][0],
            u'units': u'Unknown',
            u'size': data[u'ArraySizeY'][0],
        })
        array_shape.append(data[u'ArraySizeY'][0])

        # X axis
        axes.append({
            u'name': u'x',
            u'offset': data[u'CalibrationOffsetX'][0] -
            data[u'CalibrationElementX'][0] * data[u'CalibrationDeltaX'][0],
            u'scale': data[u'CalibrationDeltaX'][0],
            u'size': data[u'ArraySizeX'][0],
        })
        array_shape.append(data[u'ArraySizeX'][0])

    # If the acquisition stops before finishing the job, the stored file will
    # report the requested size even though no values are recorded. Therefore if
    # the shapes of the retrieved array does not match that of the data
    # dimensions we must fill the rest with zeros or (better) nans if the
    # dtype is float
    if np.cumprod(array_shape)[-1] != np.cumprod(data[u'Array'].shape)[-1]:
        dc = np.zeros(np.cumprod(array_shape)[-1],
                      dtype=data[u'Array'].dtype)
        if dc.dtype is np.dtype(u'f') or dc.dtype is np.dtype(u'f8'):
            dc[:] = np.nan
        dc[:data[u'Array'].ravel().shape[0]] = data[u'Array'].ravel()
    else:
        dc = data[u'Array']

    dc = dc.reshape(array_shape)
    if record_by == u'image':
        dc = dc[..., ::-1, :]
    if ordict:
        original_metadata = OrderedDict()
    else:
        original_metadata = {}
    header_parameters = sarray2dict(header)
    sarray2dict(data, header_parameters)
    if len(axes) != len(dc.shape):
        dc = dc.squeeze()
    if len(axes) != len(dc.shape):
        raise IOError(u"Please report this issue to the HyperSpy developers.")
    # We remove the Array key to save memory avoiding duplication
    del header_parameters[u'Array']
    original_metadata[u'ser_header_parameters'] = header_parameters
    dictionary = {
        u'data': dc,
        u'metadata': {
            u'General': {
                u'original_filename': os.path.split(filename)[1]},
            u"Signal": {
                u'signal_type': u"",
                u'record_by': record_by,
            },
        },
        u'axes': axes,
        u'original_metadata': original_metadata,
        u'mapping': mapping}
    return dictionary


def get_mode(mode):
    if u"STEM" in mode:
        return u"STEM"
    else:
        return u"TEM"


def get_degree(value):
    return np.degrees(float(value))


mapping = {
    u"ObjectInfo.ExperimentalDescription.High_tension_kV": (
        u"Acquisition_instrument.TEM.beam_energy",
        None),
    u"ObjectInfo.ExperimentalDescription.Microscope": (
        u"Acquisition_instrument.TEM.microscope",
        None),
    u"ObjectInfo.ExperimentalDescription.Mode": (
        u"Acquisition_instrument.TEM.acquisition_mode",
        get_mode),
    u"ObjectInfo.ExperimentalConditions.MicroscopeConditions.Tilt1": (
        u"Acquisition_instrument.TEM.tilt_stage",
        get_degree),
}
