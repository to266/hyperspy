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
from distutils.version import StrictVersion
import warnings
import datetime

import h5py
import numpy as np
from traits.api import Undefined
from hyperspy.misc.utils import ensure_unicode
from hyperspy.axes import AxesManager
from itertools import izip


# Plugin characteristics
# ----------------------
format_name = u'HDF5'
description = \
    u'The default file format for HyperSpy based on the HDF5 standard'

full_support = False
# Recognised file extension
file_extensions = [u'hdf', u'h4', u'hdf4', u'h5', u'hdf5', u'he4', u'he5']
default_extension = 4

# Writing capabilities
writes = True
version = u"1.3"

# -----------------------
# File format description
# -----------------------
# The root must contain a group called Experiments
# The experiments group can contain any number of subgroups
# Each subgroup is an experiment or signal
# Each subgroup must contain at least one dataset called data
# The data is an array of arbitrary dimension
# In addition a number equal to the number of dimensions of the data
# dataset + 1 of empty groups called coordinates followed by a number
# must exists with the following attributes:
#    'name'
#    'offset'
#    'scale'
#    'units'
#    'size'
#    'index_in_array'
# The experiment group contains a number of attributes that will be
# directly assigned as class attributes of the Signal instance. In
# addition the experiment groups may contain 'original_metadata' and
# 'metadata'subgroup that will be
# assigned to the same name attributes of the Signal instance as a
# Dictionary Browsers
# The Experiments group can contain attributes that may be common to all
# the experiments and that will be accessible as attributes of the
# Experiments instance
#
# New in v1.3
# -----------
# - Added support for lists, tuples and binary strings

not_valid_format = u'The file is not a valid HyperSpy hdf5 file'

current_file_version = None  # Format version of the file being read
default_version = StrictVersion(version)


def get_hspy_format_version(f):
    if u"file_format_version" in f.attrs:
        version = f.attrs[u"file_format_version"]
        if isinstance(version, str):
            version = version.decode()
        if isinstance(version, float):
            version = unicode(round(version, 2))
    elif u"Experiments" in f:
        # Chances are that this is a HSpy hdf5 file version 1.0
        version = u"1.0"
    else:
        raise IOError(not_valid_format)
    return StrictVersion(version)


def file_reader(filename, record_by, mode=u'r', driver=u'core',
                backing_store=False, load_to_memory=True, **kwds):
    f = h5py.File(filename, mode=mode, driver=driver, **kwds)
    # Getting the format version here also checks if it is a valid HSpy
    # hdf5 file, so the following two lines must not be deleted or moved
    # elsewhere.
    global current_file_version
    current_file_version = get_hspy_format_version(f)
    global default_version
    if current_file_version > default_version:
        warnings.warn(
            u"This file was written using a newer version of the "
            u"HyperSpy hdf5 file format. I will attempt to load it, but, "
            u"if I fail, it is likely that I will be more successful at "
            u"this and other tasks if you upgrade me.")

    experiments = []
    exp_dict_list = []
    if u'Experiments' in f:
        for ds in f[u'Experiments']:
            if isinstance(f[u'Experiments'][ds], h5py.Group):
                if u'data' in f[u'Experiments'][ds]:
                    experiments.append(ds)
                    d = f[u'Experiments'][ds][u'data']
        if not experiments:
            raise IOError(not_valid_format)
        # Parse the file
        for experiment in experiments:
            exg = f[u'Experiments'][experiment]
            exp = hdfgroup2signaldict(exg, load_to_memory)
            exp_dict_list.append(exp)
    else:
        raise IOError(u'This is not a valid HyperSpy HDF5 file. '
                      u'You can still load the data using a hdf5 reader, '
                      u'e.g. h5py, and manually create a Signal. '
                      u'Please, refer to the User Guide for details')
    if load_to_memory:
        f.close()
    return exp_dict_list


def hdfgroup2signaldict(group, load_to_memory=True):
    global current_file_version
    global default_version
    if current_file_version < StrictVersion(u"1.2"):
        metadata = u"mapped_parameters"
        original_metadata = u"original_parameters"
    else:
        metadata = u"metadata"
        original_metadata = u"original_metadata"

    exp = {u'metadata': hdfgroup2dict(group[metadata], load_to_memory=load_to_memory),
           u'original_metadata': hdfgroup2dict(group[original_metadata], load_to_memory=load_to_memory)
           }

    data = group[u'data']
    if load_to_memory:
        data = np.asanyarray(data)
    exp[u'data'] = data
    axes = []
    for i in xrange(len(exp[u'data'].shape)):
        try:
            axes.append(dict(group[u'axis-%i' % i].attrs))
            axis = axes[-1]
            for key, item in axis.items():
                axis[key] = ensure_unicode(item)
        except KeyError:
            break
    if len(axes) != len(exp[u'data'].shape):  # broke from the previous loop
        try:
            axes = [i for k, i in sorted(iter(hdfgroup2dict(
                group[u'_list_' + unicode(len(exp[u'data'].shape)) + u'_axes'],
                load_to_memory=load_to_memory).items()))]
        except KeyError:
            raise IOError(not_valid_format)
    exp[u'axes'] = axes
    exp[u'attributes'] = {}
    if u'learning_results' in group.keys():
        exp[u'attributes'][u'learning_results'] = \
            hdfgroup2dict(
                group[u'learning_results'],
                load_to_memory=load_to_memory)
    if u'peak_learning_results' in group.keys():
        exp[u'attributes'][u'peak_learning_results'] = \
            hdfgroup2dict(
                group[u'peak_learning_results'],
                load_to_memory=load_to_memory)

    # If the title was not defined on writing the Experiment is
    # then called __unnamed__. The next "if" simply sets the title
    # back to the empty string
    if u"General" in exp[u"metadata"] and u"title" in exp[u"metadata"][u"General"]:
        if u'__unnamed__' == exp[u'metadata'][u'General'][u'title']:
            exp[u'metadata'][u"General"][u'title'] = u''

    if current_file_version < StrictVersion(u"1.1"):
        # Load the decomposition results written with the old name,
        # mva_results
        if u'mva_results' in group.keys():
            exp[u'attributes'][u'learning_results'] = hdfgroup2dict(
                group[u'mva_results'], load_to_memory=load_to_memory)
        if u'peak_mva_results' in group.keys():
            exp[u'attributes'][u'peak_learning_results'] = hdfgroup2dict(
                group[u'peak_mva_results'], load_to_memory=load_to_memory)
        # Replace the old signal and name keys with their current names
        if u'signal' in exp[u'metadata']:
            if u"Signal" not in exp[u"metadata"]:
                exp[u"metadata"][u"Signal"] = {}
            exp[u'metadata'][u"Signal"][u'signal_type'] = \
                exp[u'metadata'][u'signal']
            del exp[u'metadata'][u'signal']

        if u'name' in exp[u'metadata']:
            if u"General" not in exp[u"metadata"]:
                exp[u"metadata"][u"General"] = {}
            exp[u'metadata'][u'General'][u'title'] = \
                exp[u'metadata'][u'name']
            del exp[u'metadata'][u'name']

    if current_file_version < StrictVersion(u"1.2"):
        if u'_internal_parameters' in exp[u'metadata']:
            exp[u'metadata'][u'_HyperSpy'] = \
                exp[u'metadata'][u'_internal_parameters']
            del exp[u'metadata'][u'_internal_parameters']
            if u'stacking_history' in exp[u'metadata'][u'_HyperSpy']:
                exp[u'metadata'][u'_HyperSpy'][u"Stacking_history"] = \
                    exp[u'metadata'][u'_HyperSpy'][u'stacking_history']
                del exp[u'metadata'][u'_HyperSpy'][u"stacking_history"]
            if u'folding' in exp[u'metadata'][u'_HyperSpy']:
                exp[u'metadata'][u'_HyperSpy'][u"Folding"] = \
                    exp[u'metadata'][u'_HyperSpy'][u'folding']
                del exp[u'metadata'][u'_HyperSpy'][u"folding"]
        if u'Variance_estimation' in exp[u'metadata']:
            if u"Noise_properties" not in exp[u"metadata"]:
                exp[u"metadata"][u"Noise_properties"] = {}
            exp[u'metadata'][u'Noise_properties'][u"Variance_linear_model"] = \
                exp[u'metadata'][u'Variance_estimation']
            del exp[u'metadata'][u'Variance_estimation']
        if u"TEM" in exp[u"metadata"]:
            if u"Acquisition_instrument" not in exp[u"metadata"]:
                exp[u"metadata"][u"Acquisition_instrument"] = {}
            exp[u"metadata"][u"Acquisition_instrument"][u"TEM"] = \
                exp[u"metadata"][u"TEM"]
            del exp[u"metadata"][u"TEM"]
            tem = exp[u"metadata"][u"Acquisition_instrument"][u"TEM"]
            if u"EELS" in tem:
                if u"dwell_time" in tem:
                    tem[u"EELS"][u"dwell_time"] = tem[u"dwell_time"]
                    del tem[u"dwell_time"]
                if u"dwell_time_units" in tem:
                    tem[u"EELS"][u"dwell_time_units"] = tem[u"dwell_time_units"]
                    del tem[u"dwell_time_units"]
                if u"exposure" in tem:
                    tem[u"EELS"][u"exposure"] = tem[u"exposure"]
                    del tem[u"exposure"]
                if u"exposure_units" in tem:
                    tem[u"EELS"][u"exposure_units"] = tem[u"exposure_units"]
                    del tem[u"exposure_units"]
                if u"Detector" not in tem:
                    tem[u"Detector"] = {}
                tem[u"Detector"] = tem[u"EELS"]
                del tem[u"EELS"]
            if u"EDS" in tem:
                if u"Detector" not in tem:
                    tem[u"Detector"] = {}
                if u"EDS" not in tem[u"Detector"]:
                    tem[u"Detector"][u"EDS"] = {}
                tem[u"Detector"][u"EDS"] = tem[u"EDS"]
                del tem[u"EDS"]
            del tem
        if u"SEM" in exp[u"metadata"]:
            if u"Acquisition_instrument" not in exp[u"metadata"]:
                exp[u"metadata"][u"Acquisition_instrument"] = {}
            exp[u"metadata"][u"Acquisition_instrument"][u"SEM"] = \
                exp[u"metadata"][u"SEM"]
            del exp[u"metadata"][u"SEM"]
            sem = exp[u"metadata"][u"Acquisition_instrument"][u"SEM"]
            if u"EDS" in sem:
                if u"Detector" not in sem:
                    sem[u"Detector"] = {}
                if u"EDS" not in sem[u"Detector"]:
                    sem[u"Detector"][u"EDS"] = {}
                sem[u"Detector"][u"EDS"] = sem[u"EDS"]
                del sem[u"EDS"]
            del sem

        if u"Sample" in exp[u"metadata"] and u"Xray_lines" in exp[
                u"metadata"][u"Sample"]:
            exp[u"metadata"][u"Sample"][u"xray_lines"] = exp[
                u"metadata"][u"Sample"][u"Xray_lines"]
            del exp[u"metadata"][u"Sample"][u"Xray_lines"]

        for key in [u"title", u"date", u"time", u"original_filename"]:
            if key in exp[u"metadata"]:
                if u"General" not in exp[u"metadata"]:
                    exp[u"metadata"][u"General"] = {}
                exp[u"metadata"][u"General"][key] = exp[u"metadata"][key]
                del exp[u"metadata"][key]
        for key in [u"record_by", u"signal_origin", u"signal_type"]:
            if key in exp[u"metadata"]:
                if u"Signal" not in exp[u"metadata"]:
                    exp[u"metadata"][u"Signal"] = {}
                exp[u"metadata"][u"Signal"][key] = exp[u"metadata"][key]
                del exp[u"metadata"][key]

    return exp


def dict2hdfgroup(dictionary, group, compression=None):
    from hyperspy.misc.utils import DictionaryTreeBrowser
    from hyperspy.signal import Signal

    def parse_structure(key, group, value, _type, compression):
        try:
            # Here we check if there are any signals in the container, as casting a long list of signals to a
            # numpy array takes a very long time. So we check if there are any,
            # and save numpy the trouble
            if np.any([isinstance(t, Signal) for t in value]):
                tmp = np.array([[0]])
            else:
                tmp = np.array(value)
        except ValueError:
            tmp = np.array([[0]])
        if tmp.dtype is np.dtype(u'O') or tmp.ndim is not 1:
            dict2hdfgroup(dict(izip(
                [unicode(i) for i in xrange(len(value))], value)),
                group.create_group(_type + unicode(len(value)) + u'_' + key),
                compression=compression)
        elif tmp.dtype.type is np.unicode_:
            group.create_dataset(_type + key,
                                 tmp.shape,
                                 dtype=h5py.special_dtype(vlen=unicode),
                                 compression=compression)
            group[_type + key][:] = tmp[:]
        else:
            group.create_dataset(
                _type + key,
                data=tmp,
                compression=compression)

    for key, value in dictionary.items():
        if isinstance(value, dict):
            dict2hdfgroup(value, group.create_group(key),
                          compression=compression)
        elif isinstance(value, DictionaryTreeBrowser):
            dict2hdfgroup(value.as_dictionary(),
                          group.create_group(key),
                          compression=compression)
        elif isinstance(value, Signal):
            if key.startswith(u'_sig_'):
                try:
                    write_signal(value, group[key])
                except:
                    write_signal(value, group.create_group(key))
            else:
                write_signal(value, group.create_group(u'_sig_' + key))
        elif isinstance(value, np.ndarray):
            group.create_dataset(key,
                                 data=value,
                                 compression=compression)
        elif value is None:
            group.attrs[key] = u'_None_'
        elif isinstance(value, str):
            try:
                _ = value.index('\x00')
                group.attrs[u'_bs_' + key] = np.void(value)
            except ValueError:
                group.attrs[key] = value.decode()
        elif isinstance(value, unicode):
            group.attrs[key] = value
        elif isinstance(value, AxesManager):
            dict2hdfgroup(value.as_dictionary(),
                          group.create_group(u'_hspy_AxesManager_' + key),
                          compression=compression)
        elif isinstance(value, (datetime.date, datetime.time)):
            group.attrs[u"_datetime_" + key] = repr(value)
        elif isinstance(value, list):
            if len(value):
                parse_structure(key, group, value, u'_list_', compression)
            else:
                group.attrs[u'_list_empty_' + key] = u'_None_'
        elif isinstance(value, tuple):
            if len(value):
                parse_structure(key, group, value, u'_tuple_', compression)
            else:
                group.attrs[u'_tuple_empty_' + key] = u'_None_'

        elif value is Undefined:
            continue
        else:
            try:
                group.attrs[key] = value
            except:
                print u"The hdf5 writer could not write the following "
                      u"information in the file"
                print u'%s : %s' % (key, value)


def hdfgroup2dict(group, dictionary=None, load_to_memory=True):
    if dictionary is None:
        dictionary = {}
    for key, value in group.attrs.items():
        if isinstance(value, str):
            value = value.decode()
        if isinstance(value, (np.string_, unicode)):
            if value == u'_None_':
                value = None
        elif isinstance(value, np.bool_):
            value = bool(value)

        elif isinstance(value, np.ndarray) and \
                value.dtype == np.dtype(u'|S1'):
            value = value.tolist()
        # skip signals - these are handled below.
        if key.startswith(u'_sig_'):
            pass
        elif key.startswith(u'_list_empty_'):
            dictionary[key[len(u'_list_empty_'):]] = []
        elif key.startswith(u'_tuple_empty_'):
            dictionary[key[len(u'_tuple_empty_'):]] = ()
        elif key.startswith(u'_bs_'):
            dictionary[key[len(u'_bs_'):]] = value.tostring()
        elif key.startswith(u'_datetime_'):
            dictionary[key.replace(u"_datetime_", u"")] = eval(value)
        else:
            dictionary[key] = value
    if not isinstance(group, h5py.Dataset):
        for key in group.keys():
            if key.startswith(u'_sig_'):
                from hyperspy.io import dict2signal
                dictionary[key[len(u'_sig_'):]] = (
                    dict2signal(hdfgroup2signaldict(group[key],
                                                    load_to_memory=load_to_memory)))
            elif isinstance(group[key], h5py.Dataset):
                if key.startswith(u"_list_"):
                    ans = np.array(group[key])
                    ans = ans.tolist()
                    kn = key[6:]
                elif key.startswith(u"_tuple_"):
                    ans = np.array(group[key])
                    ans = tuple(ans.tolist())
                    kn = key[7:]
                elif load_to_memory:
                    ans = np.array(group[key])
                    kn = key
                else:
                    # leave as h5py dataset
                    ans = group[key]
                    kn = key
                dictionary[kn] = ans
            elif key.startswith(u'_hspy_AxesManager_'):
                dictionary[key[len(u'_hspy_AxesManager_'):]] = \
                    AxesManager([i
                                 for k, i in sorted(iter(
                                     hdfgroup2dict(group[key], load_to_memory=load_to_memory).items()))])
            elif key.startswith(u'_list_'):
                dictionary[key[7 + key[6:].find(u'_'):]] = \
                    [i for k, i in sorted(iter(
                        hdfgroup2dict(group[key], load_to_memory=load_to_memory).items()))]
            elif key.startswith(u'_tuple_'):
                dictionary[key[8 + key[7:].find(u'_'):]] = tuple(
                    [i for k, i in sorted(iter(
                        hdfgroup2dict(group[key], load_to_memory=load_to_memory).items()))])
            else:
                dictionary[key] = {}
                hdfgroup2dict(
                    group[key],
                    dictionary[key],
                    load_to_memory=load_to_memory)
    return dictionary


def write_signal(signal, group, compression=u'gzip'):
    if default_version < StrictVersion(u"1.2"):
        metadata = u"mapped_parameters"
        original_metadata = u"original_parameters"
    else:
        metadata = u"metadata"
        original_metadata = u"original_metadata"

    group.create_dataset(u'data',
                         data=signal.data,
                         compression=compression)
    for axis in signal.axes_manager._axes:
        axis_dict = axis.get_axis_dictionary()
        # For the moment we don't store the navigate attribute
        del(axis_dict[u'navigate'])
        coord_group = group.create_group(
            u'axis-%s' % axis.index_in_array)
        dict2hdfgroup(axis_dict, coord_group, compression=compression)
    mapped_par = group.create_group(metadata)
    metadata_dict = signal.metadata.as_dictionary()
    if default_version < StrictVersion(u"1.2"):
        metadata_dict[u"_internal_parameters"] = \
            metadata_dict.pop(u"_HyperSpy")
    dict2hdfgroup(metadata_dict,
                  mapped_par, compression=compression)
    original_par = group.create_group(original_metadata)
    dict2hdfgroup(signal.original_metadata.as_dictionary(),
                  original_par, compression=compression)
    learning_results = group.create_group(u'learning_results')
    dict2hdfgroup(signal.learning_results.__dict__,
                  learning_results, compression=compression)
    if hasattr(signal, u'peak_learning_results'):
        peak_learning_results = group.create_group(
            u'peak_learning_results')
        dict2hdfgroup(signal.peak_learning_results.__dict__,
                      peak_learning_results, compression=compression)


def file_writer(filename,
                signal,
                compression=u'gzip',
                *args, **kwds):
    with h5py.File(filename, mode=u'w') as f:
        f.attrs[u'file_format'] = u"HyperSpy"
        f.attrs[u'file_format_version'] = version
        exps = f.create_group(u'Experiments')
        group_name = signal.metadata.General.title if \
            signal.metadata.General.title else u'__unnamed__'
        expg = exps.create_group(group_name)
        write_signal(signal, expg, compression=compression)
