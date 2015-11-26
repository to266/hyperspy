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
import os.path
import ConfigParser

import traits.api as t

from hyperspy.misc.config_dir import config_path, os_name, data_path
from hyperspy import messages
from hyperspy.misc.ipython_tools import turn_logging_on, turn_logging_off
from hyperspy.io_plugins import default_write_ext
from io import open

defaults_file = os.path.join(config_path, u'hyperspyrc')
eels_gos_files = os.path.join(data_path, u'EELS_GOS.tar.gz')


def guess_gos_path():
    if os_name == u'windows':
        # If DM is installed, use the GOS tables from the default
        # installation
        # location in windows
        program_files = os.environ[u'PROGRAMFILES']
        gos = u'Gatan\DigitalMicrograph\EELS Reference Data\H-S GOS Tables'
        gos_path = os.path.join(program_files, gos)

        # Else, use the default location in the .hyperspy forlder
        if os.path.isdir(gos_path) is False and \
                u'PROGRAMFILES(X86)' in os.environ:
            program_files = os.environ[u'PROGRAMFILES(X86)']
            gos_path = os.path.join(program_files, gos)
            if os.path.isdir(gos_path) is False:
                gos_path = os.path.join(config_path, u'EELS_GOS')
    else:
        gos_path = os.path.join(config_path, u'EELS_GOS')
    return gos_path


if os.path.isfile(defaults_file):
    # Remove config file if obsolated
    f = open(defaults_file)
    if u'Not really' in f.readline():
        # It is the old config file
        f.close()
        messages.information(u'Removing obsoleted config file')
        os.remove(defaults_file)
        defaults_file_exists = False
    else:
        defaults_file_exists = True
else:
    defaults_file_exists = False

# Defaults template definition starts#####################################
# This "section" is all that has to be modified to add or remove sections and
# options from the defaults


class GeneralConfig(t.HasTraits):

    default_file_format = t.Enum(
        u'hdf5',
        u'rpl',
        desc=u'Using the hdf5 format is highly reccomended because is the '
        u'only one fully supported. The Ripple (rpl) format it is useful '
        u'tk is provided for when none of the other toolkits are'
        u' available. However, when using this toolkit the '
        u'user interface elements are not available. '
        u'to export data to other software that do not support hdf5')
    default_toolkit = t.Enum(
        u"qt4",
        u"gtk",
        u"wx",
        u"tk",
        u"None",
        desc=u"Default toolkit for matplotlib and the user interface "
        u"elements. "
        u"When using gtk and tk the user interface elements are not"
        u" available."
        u"user interface elements are not available. "
        u"None is suitable to run headless. "
        u"HyperSpy must be restarted for changes to take effect")
    default_export_format = t.Enum(
        *default_write_ext,
        desc=u'Using the hdf5 format is highly reccomended because is the '
        u'only one fully supported. The Ripple (rpl) format it is useful '
        u'to export data to other software that do not support hdf5')
    interactive = t.CBool(
        True,
        desc=u'If enabled, HyperSpy will prompt the user when optios are '
        u'available, otherwise it will use the default values if possible')
    logger_on = t.CBool(
        False,
        label=u'Automatic logging',
        desc=u'If enabled, HyperSpy will store a log in the current directory '
        u'of all the commands typed')

    show_progressbar = t.CBool(
        True,
        label=u'Show progress bar',
        desc=u'If enabled, show a progress bar when available')

    import_hspy = t.CBool(
        True,
        label=u'from hspy import all',
        desc=u'If enabled, when starting HyperSpy using the `hyperspy` '
             u'IPython magic of the starting scripts, all the contents of '
             u'``hyperspy.hspy`` are imported in the user namespace. ')

    dtb_expand_structures = t.CBool(
        True,
        label=u'Expand structures in DictionaryTreeBrowser',
        desc=u'If enabled, when printing DictionaryTreeBrowser (e.g. metadata), '
             u'long lists and tuples will be expanded and any dictionaries in them will be '
             u'printed similar to DictionaryTreeBrowser, but with double lines')

    def _logger_on_changed(self, old, new):
        if new is True:
            turn_logging_on()
        else:
            turn_logging_off()


class ModelConfig(t.HasTraits):
    default_fitter = t.Enum(u'leastsq', u'mpfit',
                            desc=u'Choose leastsq if no bounding is required. '
                            u'Otherwise choose mpfit')


class MachineLearningConfig(t.HasTraits):
    export_factors_default_file_format = t.Enum(*default_write_ext)
    export_loadings_default_file_format = t.Enum(*default_write_ext)
    multiple_files = t.Bool(
        True,
        label=u'Export to multiple files',
        desc=u'If enabled, on exporting the PCA or ICA results one file'
        u'per factor and loading will be created. Otherwise only two files'
        u'will contain the factors and loadings')
    same_window = t.Bool(
        True,
        label=u'Plot components in the same window',
        desc=u'If enabled the principal and independent components will all'
        u' be plotted in the same window')


class EELSConfig(t.HasTraits):
    eels_gos_files_path = t.Directory(
        guess_gos_path(),
        label=u'GOS directory',
        desc=u'The GOS files are required to create the EELS edge components')
    fine_structure_width = t.CFloat(
        30,
        label=u'Fine structure length',
        desc=u'The default length of the fine structure from the edge onset')
    fine_structure_active = t.CBool(
        False,
        label=u'Enable fine structure',
        desc=u"If enabled, the regions of the EELS spectrum defined as fine "
        u"structure will be fitted with a spline. Please note that it "
        u"enabling this feature only makes sense when the model is "
        u"convolved to account for multiple scattering")
    fine_structure_smoothing = t.Range(
        0.,
        1.,
        value=0.3,
        label=u'Fine structure smoothing factor',
        desc=u'The lower the value the smoother the fine structure spline fit')
    synchronize_cl_with_ll = t.CBool(False)
    preedge_safe_window_width = t.CFloat(
        2,
        label=u'Pre-onset region (in eV)',
        desc=u'Some functions needs to define the regions between two '
        u'ionisation edges. Due to limited energy resolution or chemical '
        u'shift, the region is limited on its higher energy side by '
        u'the next ionisation edge onset minus an offset defined by this '
        u'parameters')
    min_distance_between_edges_for_fine_structure = t.CFloat(
        0,
        label=u'Minimum distance between edges',
        desc=u'When automatically setting the fine structure energy regions, '
        u'the fine structure of an EELS edge component is automatically '
        u'disable if the next ionisation edge onset distance to the '
        u'higher energy side of the fine structure region is lower that '
        u'the value of this parameter')


class EDSConfig(t.HasTraits):
    eds_mn_ka = t.CFloat(130.,
                         label=u'Energy resolution at Mn Ka (eV)',
                         desc=u'default value for FWHM of the Mn Ka peak in eV,'
                         u'This value is used as a first approximation'
                         u'of the energy resolution of the detector.')
    eds_tilt_stage = t.CFloat(
        0.,
        label=u'Stage tilt',
        desc=u'default value for the stage tilt in degree.')
    eds_detector_azimuth = t.CFloat(
        0.,
        label=u'Azimuth angle',
        desc=u'default value for the azimuth angle in degree. If the azimuth'
        u' is zero, the detector is perpendicular to the tilt axis.')
    eds_detector_elevation = t.CFloat(
        35.,
        label=u'Elevation angle',
        desc=u'default value for the elevation angle in degree.')


class PlotConfig(t.HasTraits):
    default_style_to_compare_spectra = t.Enum(
        u'overlap',
        u'cascade',
        u'mosaic',
        u'heatmap',
        desc=u' the default style use to compare spectra with the'
        u' function utils.plot.plot_spectra')
    plot_on_load = t.CBool(
        False,
        desc=u'If enabled, the object will be plot automatically on loading')
    pylab_inline = t.CBool(
        False,
        desc=u"If True the figure are displayed inline."
        u"HyperSpy must be restarted for changes to take effect")

template = {
    u'General': GeneralConfig(),
    u'Model': ModelConfig(),
    u'EELS': EELSConfig(),
    u'EDS': EDSConfig(),
    u'MachineLearning': MachineLearningConfig(),
    u'Plot': PlotConfig(), }

# Set the enums defaults
template[u'MachineLearning'].export_factors_default_file_format = u'rpl'
template[u'MachineLearning'].export_loadings_default_file_format = u'rpl'
template[u'General'].default_export_format = u'rpl'

# Defaults template definition ends ######################################


def template2config(template, config):
    for section, traited_class in template.items():
        config.add_section(section)
        for key, item in traited_class.get().items():
            config.set(section, key, unicode(item))


def config2template(template, config):
    for section, traited_class in template.items():
        config_dict = {}
        for name, value in config.items(section):
            if value == u'True':
                value = True
            elif value == u'False':
                value = False
            if name == u'fine_structure_smoothing':
                value = float(value)
            config_dict[name] = value
        traited_class.set(True, **config_dict)


def dictionary_from_template(template):
    dictionary = {}
    for section, traited_class in template.items():
        dictionary[section] = traited_class.get()
    return dictionary

config = ConfigParser.SafeConfigParser(allow_no_value=True)
template2config(template, config)
rewrite = False
if defaults_file_exists:
    # Parse the config file. It only copy to config the options that are
    # already defined. If the file contains any option that was not already
    # define the config file is rewritten because it is obsolate

    config2 = ConfigParser.SafeConfigParser(allow_no_value=True)
    config2.read(defaults_file)
    for section in config2.sections():
        if config.has_section(section):
            for option in config2.options(section):
                if config.has_option(section, option):
                    config.set(section, option, config2.get(section, option))
                else:
                    rewrite = True
        else:
            rewrite = True

if not defaults_file_exists or rewrite is True:
    messages.information(u'Writing the config file')
    config.write(open(defaults_file, u'w'))

# Use the traited classes to cast the content of the ConfigParser
config2template(template, config)


class Preferences(t.HasTraits):
    global current_toolkit
    EELS = t.Instance(EELSConfig)
    EDS = t.Instance(EDSConfig)
    Model = t.Instance(ModelConfig)
    General = t.Instance(GeneralConfig)
    MachineLearning = t.Instance(MachineLearningConfig)
    Plot = t.Instance(PlotConfig)

    def gui(self):
        import hyperspy.gui.preferences
        self.EELS.trait_view(u"traits_view",
                             hyperspy.gui.preferences.eels_view)
        self.edit_traits(view=hyperspy.gui.preferences.preferences_view)

    def save(self):
        config = ConfigParser.SafeConfigParser(allow_no_value=True)
        template2config(template, config)
        config.write(open(defaults_file, u'w'))

preferences = Preferences(
    EELS=template[u'EELS'],
    EDS=template[u'EDS'],
    General=template[u'General'],
    Model=template[u'Model'],
    MachineLearning=template[u'MachineLearning'],
    Plot=template[u'Plot'])

if preferences.General.logger_on:
    turn_logging_on(verbose=0)

current_toolkit = preferences.General.default_toolkit


def file_version(fname):
    with open(fname, u'r') as f:
        for l in f.readlines():
            if u'__version__' in l:
                return l[l.find(u'=') + 1:].strip()
    return u'0'
