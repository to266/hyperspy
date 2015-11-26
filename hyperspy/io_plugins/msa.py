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
import locale
import time
import datetime
import codecs
import warnings
import os

import numpy as np

from hyperspy.misc.config_dir import os_name
from hyperspy import Release
from hyperspy.misc.utils import DictionaryTreeBrowser
from itertools import izip

# Plugin characteristics
# ----------------------
format_name = u'MSA'
description = u''
full_support = False
file_extensions = (u'msa', u'ems', u'mas', u'emsa', u'EMS', u'MAS', u'EMSA', u'MSA')
default_extension = 0

writes = [(1, 0), ]
# ----------------------

# For a description of the EMSA/MSA format, incluiding the meaning of the
# following keywords:
# http://www.amc.anl.gov/ANLSoftwareLibrary/02-MMSLib/XEDS/EMMFF/EMMFF.IBM/Emmff.Total
keywords = {
    # Required parameters
    u'FORMAT': {u'dtype': unicode, u'mapped_to': None},
    u'VERSION': {u'dtype': unicode, u'mapped_to': None},
    u'TITLE': {u'dtype': unicode, u'mapped_to': u'General.title'},
    u'DATE': {u'dtype': unicode, u'mapped_to': None},
    u'TIME': {u'dtype': unicode, u'mapped_to': None},
    u'OWNER': {u'dtype': unicode, u'mapped_to': None},
    u'NPOINTS': {u'dtype': float, u'mapped_to': None},
    u'NCOLUMNS': {u'dtype': float, u'mapped_to': None},
    u'DATATYPE': {u'dtype': unicode, u'mapped_to': None},
    u'XPERCHAN': {u'dtype': float, u'mapped_to': None},
    u'OFFSET': {u'dtype': float, u'mapped_to': None},
    # Optional parameters
    # Spectrum characteristics
    u'SIGNALTYPE': {u'dtype': unicode, u'mapped_to':
                   u'Signal.signal_type'},
    u'XLABEL': {u'dtype': unicode, u'mapped_to': None},
    u'YLABEL': {u'dtype': unicode, u'mapped_to': None},
    u'XUNITS': {u'dtype': unicode, u'mapped_to': None},
    u'YUNITS': {u'dtype': unicode, u'mapped_to': None},
    u'CHOFFSET': {u'dtype': float, u'mapped_to': None},
    u'COMMENT': {u'dtype': unicode, u'mapped_to': None},
    # Microscope
    u'BEAMKV': {u'dtype': float, u'mapped_to':
               u'Acquisition_instrument.TEM.beam_energy'},
    u'EMISSION': {u'dtype': float, u'mapped_to': None},
    u'PROBECUR': {u'dtype': float, u'mapped_to':
                 u'Acquisition_instrument.TEM.beam_current'},
    u'BEAMDIAM': {u'dtype': float, u'mapped_to': None},
    u'MAGCAM': {u'dtype': float, u'mapped_to': None},
    u'OPERMODE': {u'dtype': unicode, u'mapped_to': None},
    u'CONVANGLE': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.convergence_angle'},

    # Specimen
    u'THICKNESS': {u'dtype': float, u'mapped_to':
                  u'Sample.thickness'},
    u'XTILTSTGE': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.tilt_stage'},
    u'YTILTSTGE': {u'dtype': float, u'mapped_to': None},
    u'XPOSITION': {u'dtype': float, u'mapped_to': None},
    u'YPOSITION': {u'dtype': float, u'mapped_to': None},
    u'ZPOSITION': {u'dtype': float, u'mapped_to': None},

    # EELS
    # in ms:
    u'INTEGTIME': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.Detector.EELS.exposure'},
    # in ms:
    u'DWELLTIME': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.Detector.EELS.dwell_time'},
    u'COLLANGLE': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.Detector.EELS.collection_angle'},
    u'ELSDET': {u'dtype': unicode, u'mapped_to': None},

    # EDS
    u'ELEVANGLE': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.Detector.EDS.elevation_angle'},
    u'AZIMANGLE': {u'dtype': float, u'mapped_to':
                  u'Acquisition_instrument.TEM.Detector.EDS.azimuth_angle'},
    u'SOLIDANGLE': {u'dtype': float, u'mapped_to':
                   u'Acquisition_instrument.TEM.Detector.EDS.solid_angle'},
    u'LIVETIME': {u'dtype': float, u'mapped_to':
                 u'Acquisition_instrument.TEM.Detector.EDS.live_time'},
    u'REALTIME': {u'dtype': float, u'mapped_to':
                 u'Acquisition_instrument.TEM.Detector.EDS.real_time'},
    u'FWHMMNKA': {u'dtype': float, u'mapped_to':
                 u'Acquisition_instrument.TEM.Detector.EDS.' +
                 u'energy_resolution_MnKa'},
    u'TBEWIND': {u'dtype': float, u'mapped_to': None},
    u'TAUWIND': {u'dtype': float, u'mapped_to': None},
    u'TDEADLYR': {u'dtype': float, u'mapped_to': None},
    u'TACTLYR': {u'dtype': float, u'mapped_to': None},
    u'TALWIND': {u'dtype': float, u'mapped_to': None},
    u'TPYWIND': {u'dtype': float, u'mapped_to': None},
    u'TBNWIND': {u'dtype': float, u'mapped_to': None},
    u'TDIWIND': {u'dtype': float, u'mapped_to': None},
    u'THCWIND': {u'dtype': float, u'mapped_to': None},
    u'EDSDET': {u'dtype': unicode, u'mapped_to':
               u'Acquisition_instrument.TEM.Detector.EDS.EDS_det'},
}


def file_reader(filename, encoding=u'latin-1', **kwds):
    parameters = {}
    mapped = DictionaryTreeBrowser({})
    with codecs.open(
            filename,
            encoding=encoding,
            errors=u'replace') as spectrum_file:
        y = []
        # Read the keywords
        data_section = False
        for line in spectrum_file.readlines():
            if data_section is False:
                if line[0] == u"#":
                    try:
                        key, value = line.split(u': ')
                        value = value.strip()
                    except ValueError:
                        key = line
                        value = None
                    key = key.strip(u'#').strip()

                    if key != u'SPECTRUM':
                        parameters[key] = value
                    else:
                        data_section = True
            else:
                # Read the data
                if line[0] != u"#" and line.strip():
                    if parameters[u'DATATYPE'] == u'XY':
                        xy = line.replace(u',', u' ').strip().split()
                        y.append(float(xy[1]))
                    elif parameters[u'DATATYPE'] == u'Y':
                        data = [
                            float(i) for i in line.replace(
                                u',',
                                u' ').strip().split()]
                        y.extend(data)
    # We rewrite the format value to be sure that it complies with the
    # standard, because it will be used by the writer routine
    parameters[u'FORMAT'] = u"EMSA/MAS Spectral Data File"

    # Convert the parameters to the right type and map some
    # TODO: the msa format seems to support specifying the units of some
    # parametes. We should add this feature here
    for parameter, value in parameters.items():
        # Some parameters names can contain the units information
        # e.g. #AZIMANGLE-dg: 90.
        if u'-' in parameter:
            clean_par, units = parameter.split(u'-')
            clean_par, units = clean_par.strip(), units.strip()
        else:
            clean_par, units = parameter, None
        if clean_par in keywords:
            try:
                parameters[parameter] = keywords[clean_par][u'dtype'](value)
            except:
                # Normally the offending mispelling is a space in the scientic
                # notation, e.g. 2.0 E-06, so we try to correct for it
                try:
                    parameters[parameter] = keywords[clean_par][u'dtype'](
                        value.replace(u' ', u''))
                except:
                    print u"The %s keyword value, %s " % (parameter, value) +
                          u"could not be converted to the right type"

            if keywords[clean_par][u'mapped_to'] is not None:
                mapped.set_item(keywords[clean_par][u'mapped_to'],
                                parameters[parameter])
                if units is not None:
                    mapped.set_item(keywords[clean_par][u'mapped_to'] +
                                    u'_units', units)

    # The data parameter needs some extra care
    # It is necessary to change the locale to US english to read the date
    # keyword
    loc = locale.getlocale(locale.LC_TIME)
    # Setting locale can raise an exception because
    # their name depends on library versions, platform etc.
    try:
        if os_name == u'posix':
            locale.setlocale(locale.LC_TIME, (u'en_US', u'utf8'))
        elif os_name == u'windows':
            locale.setlocale(locale.LC_TIME, u'english')
        try:
            H, M = time.strptime(parameters[u'TIME'], u"%H:%M")[3:5]
            mapped.set_item(u'General.time', datetime.time(H, M))
        except:
            if u'TIME' in parameters and parameters[u'TIME']:
                print u'The time information could not be retrieved'
        try:
            Y, M, D = time.strptime(parameters[u'DATE'], u"%d-%b-%Y")[0:3]
            mapped.set_item(u'General.date', datetime.date(Y, M, D))
        except:
            if u'DATE' in parameters and parameters[u'DATE']:
                print u'The date information could not be retrieved'
    except:
        warnings.warn(u"I couldn't write the date information due to"
                      u"an unexpected error. Please report this error to "
                      u"the developers")
    locale.setlocale(locale.LC_TIME, loc)  # restore saved locale

    axes = [{
        u'size': len(y),
        u'index_in_array': 0,
        u'name': parameters[u'XLABEL'] if u'XLABEL' in parameters else u'',
        u'scale': parameters[u'XPERCHAN'] if u'XPERCHAN' in parameters else 1,
        u'offset': parameters[u'OFFSET'] if u'OFFSET' in parameters else 0,
        u'units': parameters[u'XUNITS'] if u'XUNITS' in parameters else u'',
    }]

    mapped.set_item(u'General.original_filename', os.path.split(filename)[1])
    mapped.set_item(u'Signal.record_by', u'spectrum')
    if mapped.has_item(u'Signal.signal_type'):
        if mapped.Signal.signal_type == u'ELS':
            mapped.Signal.signal_type = u'EELS'
    else:
        # Defaulting to EELS looks reasonable
        mapped.set_item(u'Signal.signal_type', u'EELS')

    dictionary = {
        u'data': np.array(y),
        u'axes': axes,
        u'metadata': mapped.as_dictionary(),
        u'original_metadata': parameters
    }
    return [dictionary, ]


def file_writer(filename, signal, format=None, separator=u', ',
                encoding=u'latin-1'):
    loc_kwds = {}
    FORMAT = u"EMSA/MAS Spectral Data File"
    if hasattr(signal.original_metadata, u'FORMAT') and \
            signal.original_metadata.FORMAT == FORMAT:
        loc_kwds = signal.original_metadata.as_dictionary()
        if format is not None:
            loc_kwds[u'DATATYPE'] = format
        else:
            if u'DATATYPE' in loc_kwds:
                format = loc_kwds[u'DATATYPE']
    else:
        if format is None:
            format = u'Y'
        if signal.metadata.has_item(u"General.date"):
            # Setting locale can raise an exception because
            # their name depends on library versions, platform etc.
            try:
                loc = locale.getlocale(locale.LC_TIME)
                if os_name == u'posix':
                    locale.setlocale(locale.LC_TIME, (u'en_US', u'latin-1'))
                elif os_name == u'windows':
                    locale.setlocale(locale.LC_TIME, u'english')
                loc_kwds[u'DATE'] = signal.metadata.data.strftime(
                    u"%d-%b-%Y")
                locale.setlocale(locale.LC_TIME, loc)  # restore saved locale
            except:
                warnings.warn(
                    u"I couldn't write the date information due to"
                    u"an unexpected error. Please report this error to "
                    u"the developers")
    keys_from_signal = {
        # Required parameters
        u'FORMAT': FORMAT,
        u'VERSION': u'1.0',
        # 'TITLE' : signal.title[:64] if hasattr(signal, "title") else '',
        u'DATE': u'',
        u'TIME': u'',
        u'OWNER': u'',
        u'NPOINTS': signal.axes_manager._axes[0].size,
        u'NCOLUMNS': 1,
        u'DATATYPE': format,
        u'SIGNALTYPE': signal.metadata.Signal.signal_type,
        u'XPERCHAN': signal.axes_manager._axes[0].scale,
        u'OFFSET': signal.axes_manager._axes[0].offset,
        # Spectrum characteristics

        u'XLABEL': signal.axes_manager._axes[0].name,
        #        'YLABEL' : '',
        u'XUNITS': signal.axes_manager._axes[0].units,
        #        'YUNITS' : '',
        u'COMMENT': u'File created by HyperSpy version %s' % Release.version,
        # Microscope
        #        'BEAMKV' : ,
        #        'EMISSION' : ,
        #        'PROBECUR' : ,
        #        'BEAMDIAM' : ,
        #        'MAGCAM' : ,
        #        'OPERMODE' : ,
        #        'CONVANGLE' : ,
        # Specimen
        #        'THICKNESS' : ,
        #        'XTILTSTGE' : ,
        #        'YTILTSTGE' : ,
        #        'XPOSITION' : ,
        #        'YPOSITION' : ,
        #        'ZPOSITION' : ,
        #
        # EELS
        # 'INTEGTIME' : , # in ms
        # 'DWELLTIME' : , # in ms
        #        'COLLANGLE' : ,
        #        'ELSDET' :  ,
    }

    # Update the loc_kwds with the information retrieved from the signal class
    for key, value in keys_from_signal.items():
        if key not in loc_kwds or value != u'':
            loc_kwds[key] = value

    for key, dic in keywords.items():

        if dic[u'mapped_to'] is not None:
            if u'SEM' in signal.metadata.Signal.signal_type:
                dic[u'mapped_to'] = dic[u'mapped_to'].replace(u'TEM', u'SEM')
            if signal.metadata.has_item(dic[u'mapped_to']):
                loc_kwds[key] = eval(u'signal.metadata.%s' %
                                     dic[u'mapped_to'])

    with codecs.open(
            filename,
            u'w',
            encoding=encoding,
            errors=u'ignore') as f:
        # Remove the following keys from loc_kwds if they are in
        # (although they shouldn't)
        for key in [u'SPECTRUM', u'ENDOFDATA']:
            if key in loc_kwds:
                del(loc_kwds[key])

        f.write(u'#%-12s: %s\u000D\u000A' % (u'FORMAT', loc_kwds.pop(u'FORMAT')))
        f.write(
            u'#%-12s: %s\u000D\u000A' %
            (u'VERSION', loc_kwds.pop(u'VERSION')))
        for keyword, value in loc_kwds.items():
            f.write(u'#%-12s: %s\u000D\u000A' % (keyword, value))

        f.write(u'#%-12s: Spectral Data Starts Here\u000D\u000A' % u'SPECTRUM')

        if format == u'XY':
            for x, y in izip(signal.axes_manager._axes[0].axis, signal.data):
                f.write(u"%g%s%g" % (x, separator, y))
                f.write(u'\u000D\u000A')
        elif format == u'Y':
            for y in signal.data:
                f.write(u'%f%s' % (y, separator))
                f.write(u'\u000D\u000A')
        else:
            raise ValueError(u'format must be one of: None, \'XY\' or \'Y\'')

        f.write(u'#%-12s: End Of Data and File' % u'ENDOFDATA')
