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

#  for more information on the RPL/RAW format, see
#  http://www.nist.gov/lispix/
#  and
#  http://www.nist.gov/lispix/doc/image-file-formats/raw-file-format.htm

from __future__ import with_statement
import codecs
import os.path
from io import StringIO

import numpy as np

from hyperspy.misc.io.utils_readfile import *
from hyperspy import Release
from hyperspy.misc.utils import DictionaryTreeBrowser

# Plugin characteristics
# ----------------------
format_name = u'Ripple'
description = u'RPL file contains the information on how to read\n'
description += u'the RAW file with the same name.'
description += u'\nThis format may not provide information on the calibration.'
description += u'\nIf so, you should add that after loading the file.'
full_support = False  # but maybe True
# Recognised file extension
file_extensions = [u'rpl', u'RPL']
default_extension = 0
# Writing capabilities
writes = [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), ]
# ----------------------

# The format only support the followng data types
newline = (u'\n', u'\r\n')
comment = u';'
sep = u'\t'

dtype2keys = {
    u'float64': (u'float', 8),
    u'float32': (u'float', 4),
    u'uint8': (u'unsigned', 1),
    u'uint16': (u'unsigned', 2),
    u'int32': (u'signed', 4),
    u'int64': (u'signed', 8), }

endianess2rpl = {
    u'=': u'dont-care',
    u'<': u'little-endian',
    u'>': u'big-endian'}

rpl_keys = {
    # spectrum/image keys
    u'width': int,
    u'height': int,
    u'depth': int,
    u'offset': int,
    u'data-length': [u'1', u'2', u'4', u'8'],
    u'data-type': [u'signed', u'unsigned', u'float'],
    u'byte-order': [u'little-endian', u'big-endian', u'dont-care'],
    u'record-by': [u'image', u'vector', u'dont-care'],
    # X-ray keys
    u'ev-per-chan': float,    # usually 5 or 10 eV
    u'detector-peak-width-ev': float,  # usually 150 eV
    # HyperSpy-specific keys
    u'depth-origin': float,
    u'depth-scale': float,
    u'depth-units': unicode,
    u'width-origin': float,
    u'width-scale': float,
    u'width-units': unicode,
    u'height-origin': float,
    u'height-scale': float,
    u'height-units': unicode,
    u'signal': unicode,
    # EELS HyperSpy keys
    u'collection-angle': float,
    # TEM Hyperespy keys
    u'convergence-angle': float,
    u'beam-energy': float,
    # EDS Hyperespy keys
    u'elevation-angle': float,
    u'azimuth-angle': float,
    u'live-time': float,
    u'energy-resolution': float,
    u'tilt-stage': float,
}


def correct_INCA_format(fp):
    fp_list = list()
    fp.seek(0)
    if u'(' in fp.readline():
        for line in fp:
            line = line.replace(
                u"(MLX::",
                u"").replace(
                u" : ",
                u"\t").replace(
                u" :",
                u"\t").replace(
                u" ",
                u"\t").lower().strip().replace(
                u")",
                u"\n")
            if u"record-by" in line:
                if u"image" in line:
                    line = u"record-by\timage"
                if u"vector" in line:
                    line = u"record-by\tvector"
                if u"dont-care" in line:
                    line = u"record-by\tdont-care"
            fp_list.append(line)
        fp = StringIO()
        fp.writelines(fp_list)
    fp.seek(0)
    return fp


def parse_ripple(fp):
    u"""Parse information from ripple (.rpl) file.
    Accepts file object 'fp. Returns dictionary rpl_info.
    """

    fp = correct_INCA_format(fp)

    rpl_info = {}
    for line in fp.readlines():
        line = line.replace(u' ', u'')
        # correct_brucker_format
        line = line.replace(u'data-Length', u'data-length')
        if line[:2] not in newline and line[0] != comment:
            line = line.strip(u'\r\n')
            if comment in line:
                line = line[:line.find(comment)]
            if sep not in line:
                err = u'Separator in line "%s" is wrong, ' % line
                err += u'it should be a <TAB> ("\\t")'
                raise IOError(err)
            line = line.split(sep)  # now it's a list
            if (line[0] in rpl_keys) is True:
                # is rpl_keys[line[0]] an iterable?
                if hasattr(rpl_keys[line[0]], u'__iter__'):
                    if line[1] not in rpl_keys[line[0]]:
                        err = \
                            u'Wrong value for key %s.\n' \
                            u'Value read is %s'  \
                            u' but it should be one of %s' % \
                            (line[0], line[1], unicode(rpl_keys[line[0]]))
                        raise IOError(err)
                else:
                    # rpl_keys[line[0]] must then be a type
                    line[1] = rpl_keys[line[0]](line[1])

            rpl_info[line[0]] = line[1]

    if rpl_info[u'depth'] == 1 and rpl_info[u'record-by'] != u'dont-care':
        err = u'"depth" and "record-by" keys mismatch.\n'
        err += u'"depth" cannot be "1" if "record-by" is "dont-care" '
        err += u'and vice versa.'
        err += u'Check %s' % fp.name
        raise IOError(err)
    if rpl_info[u'data-type'] == u'float' and int(rpl_info[u'data-length']) < 4:
        err = u'"data-length" for float "data-type" must be "4" or "8".\n'
        err += u'Check %s' % fp.name
        raise IOError(err)
    if (rpl_info[u'data-length'] == u'1' and
            rpl_info[u'byte-order'] != u'dont-care'):
        err = u'"data-length" and "byte-order" mismatch.\n'
        err += u'"data-length" cannot be "1" if "byte-order" is not "dont-care"'
        err += u' and vice versa.'
        err += u'Check %s' % fp.name
        raise IOError(err)
    return rpl_info


def read_raw(rpl_info, fp, mmap_mode=u'c'):
    u"""Read the raw file object 'fp' based on the information given in the
    'rpl_info' dictionary.

    Parameters
    ----------
    rpl_info: dict
        A dictionary containing the keywords as parsed by read_rpl
    fp:
    mmap_mode: {None, 'r+', 'r', 'w+', 'c'}, optional
    If not None, then memory-map the file, using the given mode
    (see `numpy.memmap`).  The mode has no effect for pickled or
    zipped files.
    A memory-mapped array is stored on disk, and not directly loaded
    into memory.  However, it can be accessed and sliced like any
    ndarray.  Memory mapping is especially useful for accessing
    small fragments of large files without reading the entire file
    into memory.


    """
    width = rpl_info[u'width']
    height = rpl_info[u'height']
    depth = rpl_info[u'depth']
    offset = rpl_info[u'offset']
    data_length = rpl_info[u'data-length']
    data_type = rpl_info[u'data-type']
    endian = rpl_info[u'byte-order']
    record_by = rpl_info[u'record-by']

    if data_type == u'signed':
        data_type = u'int'
    elif data_type == u'unsigned':
        data_type = u'uint'
    elif data_type == u'float':
        pass
    else:
        raise TypeError(u'Unknown "data-type" string.')

    if endian == u'big-endian':
        endian = u'>'
    elif endian == u'little-endian':
        endian = u'<'
    else:
        endian = u'='

    data_type += unicode(int(data_length) * 8)
    data_type = np.dtype(data_type)
    data_type = data_type.newbyteorder(endian)

    data = np.memmap(fp,
                     offset=offset,
                     dtype=data_type,
                     mode=mmap_mode)

    if record_by == u'vector':   # spectral image
        size = (height, width, depth)
        data = data.reshape(size)
    elif record_by == u'image':  # stack of images
        size = (depth, height, width)
        data = data.reshape(size)
    elif record_by == u'dont-care':  # stack of images
        size = (height, width)
        data = data.reshape(size)
    return data


def file_reader(filename, rpl_info=None, encoding=u"latin-1",
                mmap_mode=u'c', *args, **kwds):
    u"""Parses a Lispix (http://www.nist.gov/lispix/) ripple (.rpl) file
    and reads the data from the corresponding raw (.raw) file;
    or, read a raw file if the dictionary rpl_info is provided.

    This format is often uses in EDS/EDX experiments.

    Images and spectral images or data cubes that are written in the
    (Lispix) raw file format are just a continuous string of numbers.

    Data cubes can be stored image by image, or spectrum by spectrum.
    Single images are stored row by row, vector cubes are stored row by row
    (each row spectrum by spectrum), image cubes are stored image by image.

    All of the numbers are in the same format, such as 16 bit signed integer,
    IEEE 8-byte real, 8-bit unsigned byte, etc.

    The "raw" file should be accompanied by text file with the same name and
    ".rpl" extension. This file lists the characteristics of the raw file so
    that it can be loaded without human intervention.

    Alternatively, dictionary 'rpl_info' containing the information can
    be given.

    Some keys are specific to HyperSpy and will be ignored by other software.

    RPL stands for "Raw Parameter List", an ASCII text, tab delimited file in
    which HyperSpy reads the image parameters for a raw file.

                    TABLE OF RPL PARAMETERS
        key             type     description
      ----------   ------------ --------------------
      # Mandatory      keys:
      width            int      # pixels per row
      height           int      # number of rows
      depth            int      # number of images or spectral pts
      offset           int      # bytes to skip
      data-type        str      # 'signed', 'unsigned', or 'float'
      data-length      str      # bytes per pixel  '1', '2', '4', or '8'
      byte-order       str      # 'big-endian', 'little-endian', or 'dont-care'
      record-by        str      # 'image', 'vector', or 'dont-care'
      # X-ray keys:
      ev-per-chan      int      # optional, eV per channel
      detector-peak-width-ev  int   # optional, FWHM for the Mn K-alpha line
      # HyperSpy-specific keys
      depth-origin    int      # energy offset in pixels
      depth-scale     float    # energy scaling (units per pixel)
      depth-units     str      # energy units, usually eV
      depth-name      str      # Name of the magnitude stored as depth
      width-origin         int      # column offset in pixels
      width-scale          float    # column scaling (units per pixel)
      width-units          str      # column units, usually nm
      width-name      str           # Name of the magnitude stored as width
      height-origin         int      # row offset in pixels
      height-scale          float    # row scaling (units per pixel)
      height-units          str      # row units, usually nm
      height-name      str           # Name of the magnitude stored as height
      signal            str        # Name of the signal stored, e.g. HAADF
      convergence-angle float   # TEM convergence angle in mrad
      collection-angle  float   # EELS spectrometer collection angle in mrad
      beam-energy       float   # TEM beam energy in keV
      elevation-angle   float   # Elevation angle of the EDS detector
      azimuth-angle     float   # Elevation angle of the EDS detector
      live-time         float   # Live time per spectrum
      energy-resolution float   # Resolution of the EDS (FHWM of MnKa)
      tilt-stage       float   # The tilt of the stage

    NOTES

    When 'data-length' is 1, the 'byte order' is not relevant as there is only
    one byte per datum, and 'byte-order' should be 'dont-care'.

    When 'depth' is 1, the file has one image, 'record-by' is not relevant and
    should be 'dont-care'. For spectral images, 'record-by' is 'vector'.
    For stacks of images, 'record-by' is 'image'.

    Floating point numbers can be IEEE 4-byte, or IEEE 8-byte. Therefore if
    data-type is float, data-length MUST be 4 or 8.

    The rpl file is read in a case-insensitive manner. However, when providing
    a dictionary as input, the keys MUST be lowercase.

    Comment lines, beginning with a semi-colon ';' are allowed anywhere.

    The first non-comment in the rpl file line MUST have two column names:
    'name_1'<TAB>'name_2'; any name would do e.g. 'key'<TAB>'value'.

    Parameters can be in ANY order.

    In the rpl file, the parameter name is followed by ONE tab (spaces are
    ignored) e.g.: 'data-length'<TAB>'2'

    In the rpl file, other data and more tabs can follow the two items on
    each row, and are ignored.

    Other keys and values can be included and are ignored.

    Any number of spaces can go along with each tab.

    """

    if not rpl_info:
        if filename[-3:] in file_extensions:
            with codecs.open(filename, encoding=encoding,
                             errors=u'replace') as f:
                rpl_info = parse_ripple(f)
        else:
            raise IOError(u'File has wrong extension: "%s"' % filename[-3:])
    for ext in [u'raw', u'RAW']:
        rawfname = filename[:-3] + ext
        if os.path.exists(rawfname):
            break
        else:
            rawfname = u''
    if not rawfname:
        raise IOError(u'RAW file "%s" does not exists' % rawfname)
    else:
        data = read_raw(rpl_info, rawfname, mmap_mode=mmap_mode)

    if rpl_info[u'record-by'] == u'vector':
        print u'Loading as spectrum'
        record_by = u'spectrum'
    elif rpl_info[u'record-by'] == u'image':
        print u'Loading as Image'
        record_by = u'image'
    else:
        if len(data.shape) == 1:
            print u'Loading as spectrum'
            record_by = u'spectrum'
        else:
            print u'Loading as image'
            record_by = u'image'

    if rpl_info[u'record-by'] == u'vector':
        idepth, iheight, iwidth = 2, 0, 1
        names = [u'height', u'width', u'depth', ]
    else:
        idepth, iheight, iwidth = 0, 1, 2
        names = [u'depth', u'height', u'width']

    scales = [1, 1, 1]
    origins = [0, 0, 0]
    units = [u'', u'', u'']
    sizes = [rpl_info[names[i]] for i in xrange(3)]

    if u'signal' not in rpl_info:
        rpl_info[u'signal'] = u""

    if u'detector-peak-width-ev' in rpl_info:
        original_metadata[u'detector-peak-width-ev'] = \
            rpl_info[u'detector-peak-width-ev']

    if u'depth-scale' in rpl_info:
        scales[idepth] = rpl_info[u'depth-scale']
    # ev-per-chan is the only calibration supported by the original ripple
    # format
    elif u'ev-per-chan' in rpl_info:
        scales[idepth] = rpl_info[u'ev-per-chan']

    if u'depth-origin' in rpl_info:
        origins[idepth] = rpl_info[u'depth-origin']

    if u'depth-units' in rpl_info:
        units[idepth] = rpl_info[u'depth-units']

    if u'depth-name' in rpl_info:
        names[idepth] = rpl_info[u'depth-name']

    if u'width-origin' in rpl_info:
        origins[iwidth] = rpl_info[u'width-origin']

    if u'width-scale' in rpl_info:
        scales[iwidth] = rpl_info[u'width-scale']

    if u'width-units' in rpl_info:
        units[iwidth] = rpl_info[u'width-units']

    if u'width-name' in rpl_info:
        names[iwidth] = rpl_info[u'width-name']

    if u'height-origin' in rpl_info:
        origins[iheight] = rpl_info[u'height-origin']

    if u'height-scale' in rpl_info:
        scales[iheight] = rpl_info[u'height-scale']

    if u'height-units' in rpl_info:
        units[iheight] = rpl_info[u'height-units']

    if u'height-name' in rpl_info:
        names[iheight] = rpl_info[u'height-name']

    mp = DictionaryTreeBrowser({

        u'General': {u'original_filename': os.path.split(filename)[1]},
        u"Signal": {u'signal_type': rpl_info[u'signal'],
                   u'record_by': record_by, },
    })

    if u'convergence-angle' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.convergence_angle',
                    rpl_info[u'convergence-angle'])
    if u'tilt-stage' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.tilt_stage',
                    rpl_info[u'tilt-stage'])
    if u'collection-angle' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.Detector.EELS.' +
                    u'collection_angle',
                    rpl_info[u'collection-angle'])
    if u'beam-energy' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.beam_energy',
                    rpl_info[u'beam-energy'])
    if u'elevation-angle' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.Detector.EDS.elevation_angle',
                    rpl_info[u'elevation-angle'])
    if u'azimuth-angle' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.Detector.EDS.azimuth_angle',
                    rpl_info[u'azimuth-angle'])
    if u'energy-resolution' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.Detector.EDS.' +
                    u'energy_resolution_MnKa',
                    rpl_info[u'energy-resolution'])
    if u'live-time' in rpl_info:
        mp.set_item(u'Acquisition_instrument.TEM.Detector.EDS.live_time',
                    rpl_info[u'live-time'])

    axes = []
    index_in_array = 0
    for i in xrange(3):
        if sizes[i] > 1:
            axes.append({
                u'size': sizes[i],
                u'index_in_array': index_in_array,
                u'name': names[i],
                u'scale': scales[i],
                u'offset': origins[i],
                u'units': units[i],
            })
            index_in_array += 1

    dictionary = {
        u'data': data.squeeze(),
        u'axes': axes,
        u'metadata': mp.as_dictionary(),
        u'original_metadata': rpl_info
    }
    return [dictionary, ]


def file_writer(filename, signal, encoding=u'latin-1', *args, **kwds):

    # Set the optional keys to None
    ev_per_chan = None

    # Check if the dtype is supported
    dc = signal.data
    dtype_name = signal.data.dtype.name
    if dtype_name not in dtype2keys.keys():
        err = u'The ripple format does not support writting data of %s type' % (
            dtype_name)
        raise IOError(err)
    # Check if the dimensions are supported
    dimension = len(signal.data.shape)
    if dimension > 3:
        err = u'This file format does not support %i dimension data' % (
            dimension)
        raise IOError(err)

    # Gather the information to write the rpl
    data_type, data_length = dtype2keys[dc.dtype.name]
    byte_order = endianess2rpl[dc.dtype.byteorder.replace(u'|', u'=')]
    offset = 0
    if signal.metadata.has_item(u"Signal.signal_type"):
        signal_type = signal.metadata.Signal.signal_type
    else:
        signal_type = u""
    if signal.axes_manager.signal_dimension == 1:
        record_by = u'vector'
        depth_axis = signal.axes_manager.signal_axes[0]
        ev_per_chan = int(round(depth_axis.scale))
        if dimension == 3:
            width_axis = signal.axes_manager.navigation_axes[0]
            height_axis = signal.axes_manager.navigation_axes[1]
            depth, width, height = \
                depth_axis.size, width_axis.size, height_axis.size
        elif dimension == 2:
            width_axis = signal.axes_manager.navigation_axes[0]
            depth, width, height = depth_axis.size, width_axis.size, 1
        elif dimension == 1:
            record_by == u'dont-care'
            depth, width, height = depth_axis.size, 1, 1

    elif signal.axes_manager.signal_dimension == 2:
        width_axis = signal.axes_manager.signal_axes[0]
        height_axis = signal.axes_manager.signal_axes[1]
        if dimension == 3:
            depth_axis = signal.axes_manager.navigation_axes[0]
            record_by = u'image'
            depth, width, height =  \
                depth_axis.size, width_axis.size, height_axis.size
        elif dimension == 2:
            record_by = u'dont-care'
            width, height, depth = width_axis.size, height_axis.size, 1
        elif dimension == 1:
            record_by = u'dont-care'
            depth, width, height = width_axis.size, 1, 1
    else:
        print u"Only Spectrum and Image objects can be saved"
        return

    # Fill the keys dictionary
    keys_dictionary = {
        u'width': width,
        u'height': height,
        u'depth': depth,
        u'offset': offset,
        u'data-type': data_type,
        u'data-length': data_length,
        u'byte-order': byte_order,
        u'record-by': record_by,
        u'signal': signal_type
    }
    if ev_per_chan is not None:
        keys_dictionary[u'ev-per-chan'] = ev_per_chan
    keys = [u'depth', u'height', u'width']
    for key in keys:
        if eval(key) > 1:
            keys_dictionary[u'%s-scale' % key] = eval(
                u'%s_axis.scale' % key)
            keys_dictionary[u'%s-origin' % key] = eval(
                u'%s_axis.offset' % key)
            keys_dictionary[u'%s-units' % key] = eval(
                u'%s_axis.units' % key)
            keys_dictionary[u'%s-name' % key] = eval(
                u'%s_axis.name' % key)

    if u"EDS" in signal.metadata.Signal.signal_type:
        if signal.metadata.Signal.signal_type == u"EDS_SEM":
            mp = signal.metadata.Acquisition_instrument.SEM
        elif signal.metadata.Signal.signal_type == u"EDS_TEM":
            mp = signal.metadata.Acquisition_instrument.TEM

        if mp.has_item(u'beam_energy'):
            keys_dictionary[u'beam-energy'] = mp.beam_energy
        if mp.has_item(u'convergence_angle'):
            keys_dictionary[u'convergence-angle'] = mp.convergence_angle
        if mp.has_item(u'Detector.EELS.collection_angle'):
            keys_dictionary[
                u'collection-angle'] = mp.Detector.EELS.collection_angle

        if mp.has_item(u'Detector.EDS.elevation_angle'):
            keys_dictionary[
                u'elevation-angle'] = mp.Detector.EDS.elevation_angle
        if mp.has_item(u'tilt_stage'):
            keys_dictionary[u'tilt-stage'] = mp.tilt_stage
        if mp.has_item(u'Detector.EDS.azimuth_angle'):
            keys_dictionary[u'azimuth-angle'] = mp.Detector.EDS.azimuth_angle
        if mp.has_item(u'Detector.EDS.live_time'):
            keys_dictionary[u'live-time'] = mp.Detector.EDS.live_time
        if mp.has_item(u'Detector.EDS.energy_resolution_MnKa'):
            keys_dictionary[
                u'energy-resolution'] = mp.Detector.EDS.energy_resolution_MnKa

    write_rpl(filename, keys_dictionary, encoding)
    write_raw(filename, signal, record_by)


def write_rpl(filename, keys_dictionary, encoding=u'ascii'):
    f = codecs.open(filename, u'w', encoding=encoding,
                    errors=u'ignore')
    f.write(u';File created by HyperSpy version %s\n' % Release.version)
    f.write(u'key\tvalue\n')
    # Even if it is not necessary, we sort the keywords when writing
    # to make the rpl file more human friendly
    for key, value in iter(sorted(keys_dictionary.items())):
        if not isinstance(value, unicode):
            value = unicode(value)
        f.write(key + u'\t' + value + u'\n')
    f.close()


def write_raw(filename, signal, record_by):
    u"""Writes the raw file object

    Parameters:
    -----------
    filename : string
        the filename, either with the extension or without it
    record_by : string
     'vector' or 'image'

        """
    filename = os.path.splitext(filename)[0] + u'.raw'
    dshape = signal.data.shape
    data = signal.data
    if len(dshape) == 3:
        if record_by == u'vector':
            np.rollaxis(
                data, signal.axes_manager.signal_axes[0].index_in_array, 3
            ).ravel().tofile(filename)
        elif record_by == u'image':
            data = np.rollaxis(
                data, signal.axes_manager.navigation_axes[0].index_in_array, 0
            ).ravel().tofile(filename)
    elif len(dshape) == 2:
        if record_by == u'vector':
            np.rollaxis(
                data, signal.axes_manager.signal_axes[0].index_in_array, 2
            ).ravel().tofile(filename)
        elif record_by in (u'image', u'dont-care'):
            data.ravel().tofile(filename)
    elif len(dshape) == 1:
        data.ravel().tofile(filename)
