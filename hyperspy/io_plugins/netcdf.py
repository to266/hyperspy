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

import os

import numpy as np

from hyperspy import messages

no_netcdf = False
try:
    from netCDF4 import Dataset
    which_netcdf = u'netCDF4'
except:
    try:
        from netCDF3 import Dataset
        which_netcdf = u'netCDF3'
    except:
        try:
            from Scientific.IO.NetCDF import NetCDFFile as Dataset
            which_netcdf = u'Scientific Python'
        except:
            no_netcdf = True

# Plugin characteristics
# ----------------------
format_name = u'netCDF'
description = u''
full_support = True
file_extensions = (u'nc', u'NC')
default_extension = 0


# Writing features
writes = False

# ----------------------


attrib2netcdf = \
    {
        u'energyorigin': u'energy_origin',
        u'energyscale': u'energy_scale',
        u'energyunits': u'energy_units',
        u'xorigin': u'x_origin',
        u'xscale': u'x_scale',
        u'xunits': u'x_units',
        u'yorigin': u'y_origin',
        u'yscale': u'y_scale',
        u'yunits': u'y_units',
        u'zorigin': u'z_origin',
        u'zscale': u'z_scale',
        u'zunits': u'z_units',
        u'exposure': u'exposure',
        u'title': u'title',
        u'binning': u'binning',
        u'readout_frequency': u'readout_frequency',
        u'ccd_height': u'ccd_height',
        u'blanking': u'blanking'
    }

acquisition2netcdf = \
    {
        u'exposure': u'exposure',
        u'binning': u'binning',
        u'readout_frequency': u'readout_frequency',
        u'ccd_height': u'ccd_height',
        u'blanking': u'blanking',
        u'gain': u'gain',
        u'pppc': u'pppc',
    }

treatments2netcdf = \
    {
        u'dark_current': u'dark_current',
        u'readout': u'readout',
    }


def file_reader(filename, *args, **kwds):
    if no_netcdf is True:
        raise ImportError(u"No netCDF library installed. "
                          u"To read EELSLab netcdf files install "
                          u"one of the following packages:"
                          u"netCDF4, netCDF3, netcdf, scientific")

    ncfile = Dataset(filename, u'r')

    if hasattr(ncfile, u'file_format_version'):
        if ncfile.file_format_version == u'EELSLab 0.1':
            dictionary = nc_hyperspy_reader_0dot1(
                ncfile,
                filename,
                *
                args,
                **kwds)
    else:
        ncfile.close()
        messages.warning_exit(u'Unsupported netCDF file')

    return dictionary,


def nc_hyperspy_reader_0dot1(ncfile, filename, *args, **kwds):
    calibration_dict, acquisition_dict, treatments_dict = {}, {}, {}
    dc = ncfile.variables[u'data_cube']
    data = dc[:]
    if u'history' in calibration_dict:
        calibration_dict[u'history'] = eval(ncfile.history)
    for attrib in attrib2netcdf.items():
        if hasattr(dc, attrib[1]):
            value = eval(u'dc.' + attrib[1])
            if isinstance(value, np.ndarray):
                calibration_dict[attrib[0]] = value[0]
            else:
                calibration_dict[attrib[0]] = value
        else:
            print u"Warning: the \'%s\' attribute is not defined in the file\
            " % attrib[0]
    for attrib in acquisition2netcdf.items():
        if hasattr(dc, attrib[1]):
            value = eval(u'dc.' + attrib[1])
            if isinstance(value, np.ndarray):
                acquisition_dict[attrib[0]] = value[0]
            else:
                acquisition_dict[attrib[0]] = value
        else:
            print u"Warning: the \'%s\' attribute is not defined in the file\
            " % attrib[0]
    for attrib in treatments2netcdf.items():
        if hasattr(dc, attrib[1]):
            treatments_dict[attrib[0]] = eval(u'dc.' + attrib[1])
        else:
            print u"Warning: the \'%s\' attribute is not defined in the file\
            " % attrib[0]
    original_metadata = {u'record_by': ncfile.type,
                         u'calibration': calibration_dict,
                         u'acquisition': acquisition_dict,
                         u'treatments': treatments_dict}
    ncfile.close()
    # Now we'll map some parameters
    record_by = u'image' if original_metadata[
        u'record_by'] == u'Image' else u'spectrum'
    if record_by == u'image':
        dim = len(data.shape)
        names = [u'Z', u'Y', u'X'][3 - dim:]
        scaleskeys = [u'zscale', u'yscale', u'xscale']
        originskeys = [u'zorigin', u'yorigin', u'xorigin']
        unitskeys = [u'zunits', u'yunits', u'xunits']

    elif record_by == u'spectrum':
        dim = len(data.shape)
        names = [u'Y', u'X', u'Energy'][3 - dim:]
        scaleskeys = [u'yscale', u'xscale', u'energyscale']
        originskeys = [u'yorigin', u'xorigin', u'energyorigin']
        unitskeys = [u'yunits', u'xunits', u'energyunits']

    # The images are recorded in the Fortran order
    data = data.T.copy()
    try:
        scales = [calibration_dict[key] for key in scaleskeys[3 - dim:]]
    except KeyError:
        scales = [1, 1, 1][3 - dim:]
    try:
        origins = [calibration_dict[key] for key in originskeys[3 - dim:]]
    except KeyError:
        origins = [0, 0, 0][3 - dim:]
    try:
        units = [calibration_dict[key] for key in unitskeys[3 - dim:]]
    except KeyError:
        units = [u'', u'', u'']
    axes = [
        {
            u'size': int(data.shape[i]),
            u'index_in_array': i,
            u'name': names[i],
            u'scale': scales[i],
            u'offset': origins[i],
            u'units': units[i], }
        for i in xrange(dim)]
    metadata = {u'General': {}, u'Signal': {}}
    metadata[u'General'][u'original_filename'] = os.path.split(filename)[1]
    metadata[u"Signal"][u'record_by'] = record_by
    metadata[u"General"][u'signal_type'] = u""
    dictionary = {
        u'data': data,
        u'axes': axes,
        u'metadata': metadata,
        u'original_metadata': original_metadata,
    }

    return dictionary
