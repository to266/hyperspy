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


from __future__ import division
import numpy as np
import nose.tools

from hyperspy.signals import EDSSEMSpectrum
from hyperspy.defaults_parser import preferences
from hyperspy.components import Gaussian
from hyperspy import utils


class Test_metadata(object):

    def setUp(self):
        # Create an empty spectrum
        s = EDSSEMSpectrum(np.ones((4, 2, 1024)))
        s.axes_manager.signal_axes[0].scale = 1e-3
        s.axes_manager.signal_axes[0].units = u"keV"
        s.axes_manager.signal_axes[0].name = u"Energy"
        s.metadata.Acquisition_instrument.SEM.Detector.EDS.live_time = 3.1
        s.metadata.Acquisition_instrument.SEM.beam_energy = 15.0
        s.metadata.Acquisition_instrument.SEM.tilt_stage = -38
        s.metadata.Acquisition_instrument.SEM.Detector.EDS.azimuth_angle = 63
        s.metadata.Acquisition_instrument.SEM.Detector.EDS.elevation_angle = 35
        self.signal = s

    def test_sum_live_time(self):
        s = self.signal
        old_metadata = s.metadata.deepcopy()
        sSum = s.sum(0)
        nose.tools.assert_equal(
            sSum.metadata.Acquisition_instrument.SEM.Detector.EDS.live_time,
            3.1 *
            2)
        # Check that metadata is unchanged
        print old_metadata, s.metadata      # Capture for comparison on error
        nose.tools.assert_dict_equal(old_metadata.as_dictionary(),
                                     s.metadata.as_dictionary(),
                                     u"Source metadata changed")

    def test_rebin_live_time(self):
        s = self.signal
        old_metadata = s.metadata.deepcopy()
        dim = s.axes_manager.shape
        s = s.rebin([dim[0] / 2, dim[1] / 2, dim[2]])
        nose.tools.assert_equal(
            s.metadata.Acquisition_instrument.SEM.Detector.EDS.live_time,
            3.1 *
            2 *
            2)
        # Check that metadata is unchanged
        print old_metadata, self.signal.metadata    # Captured on error
        nose.tools.assert_dict_equal(old_metadata.as_dictionary(),
                                     self.signal.metadata.as_dictionary(),
                                     u"Source metadata changed")

    def test_add_elements(self):
        s = self.signal
        s.add_elements([u'Al', u'Ni'])
        nose.tools.assert_equal(s.metadata.Sample.elements, [u'Al', u'Ni'])
        s.add_elements([u'Al', u'Ni'])
        nose.tools.assert_equal(s.metadata.Sample.elements, [u'Al', u'Ni'])
        s.add_elements([u"Fe", ])
        nose.tools.assert_equal(s.metadata.Sample.elements, [u'Al', u"Fe", u'Ni'])
        s.set_elements([u'Al', u'Ni'])
        nose.tools.assert_equal(s.metadata.Sample.elements, [u'Al', u'Ni'])

    def test_add_lines(self):
        s = self.signal
        s.add_lines(lines=())
        nose.tools.assert_equal(s.metadata.Sample.xray_lines, [])
        s.add_lines((u"Fe_Ln",))
        nose.tools.assert_equal(s.metadata.Sample.xray_lines, [u"Fe_Ln"])
        s.add_lines((u"Fe_Ln",))
        nose.tools.assert_equal(s.metadata.Sample.xray_lines, [u"Fe_Ln"])
        s.add_elements([u"Ti", ])
        s.add_lines(())
        nose.tools.assert_equal(
            s.metadata.Sample.xray_lines, [u'Fe_Ln', u'Ti_La'])
        s.set_lines((), only_one=False, only_lines=False)
        nose.tools.assert_equal(s.metadata.Sample.xray_lines,
                                [u'Fe_La', u'Fe_Lb3', u'Fe_Ll', u'Fe_Ln', u'Ti_La',
                                 u'Ti_Lb3', u'Ti_Ll', u'Ti_Ln'])
        s.metadata.Acquisition_instrument.SEM.beam_energy = 0.4
        s.set_lines((), only_one=False, only_lines=False)
        nose.tools.assert_equal(s.metadata.Sample.xray_lines, [u'Ti_Ll'])

    def test_add_lines_auto(self):
        s = self.signal
        s.axes_manager.signal_axes[0].scale = 1e-2
        s.set_elements([u"Ti", u"Al"])
        s.set_lines([u'Al_Ka'])
        nose.tools.assert_equal(
            s.metadata.Sample.xray_lines, [u'Al_Ka', u'Ti_Ka'])

        del s.metadata.Sample.xray_lines
        s.set_elements([u'Al', u'Ni'])
        s.add_lines()
        nose.tools.assert_equal(
            s.metadata.Sample.xray_lines, [u'Al_Ka', u'Ni_Ka'])
        s.metadata.Acquisition_instrument.SEM.beam_energy = 10.0
        s.set_lines([])
        nose.tools.assert_equal(
            s.metadata.Sample.xray_lines, [u'Al_Ka', u'Ni_La'])
        s.metadata.Acquisition_instrument.SEM.beam_energy = 200
        s.set_elements([u'Au', u'Ni'])
        s.set_lines([])
        nose.tools.assert_equal(s.metadata.Sample.xray_lines,
                                [u'Au_La', u'Ni_Ka'])

    def test_default_param(self):
        s = self.signal
        mp = s.metadata
        nose.tools.assert_equal(
            mp.Acquisition_instrument.SEM.Detector.EDS.energy_resolution_MnKa,
            preferences.EDS.eds_mn_ka)

    def test_SEM_to_TEM(self):
        s = self.signal.inav[0, 0]
        signal_type = u'EDS_TEM'
        mp = s.metadata
        mp.Acquisition_instrument.SEM.Detector.EDS.energy_resolution_MnKa = \
            125.3
        sTEM = s.deepcopy()
        sTEM.set_signal_type(signal_type)
        mpTEM = sTEM.metadata
        results = [
            mp.Acquisition_instrument.SEM.Detector.EDS.energy_resolution_MnKa,
            signal_type]
        resultsTEM = [
            mpTEM.Acquisition_instrument.TEM.Detector.EDS.energy_resolution_MnKa,
            mpTEM.Signal.signal_type]
        nose.tools.assert_equal(results, resultsTEM)

    def test_get_calibration_from(self):
        s = self.signal
        scalib = EDSSEMSpectrum(np.ones(1024))
        energy_axis = scalib.axes_manager.signal_axes[0]
        energy_axis.scale = 0.01
        energy_axis.offset = -0.10
        s.get_calibration_from(scalib)
        nose.tools.assert_equal(s.axes_manager.signal_axes[0].scale,
                                energy_axis.scale)

    def test_take_off_angle(self):
        s = self.signal
        nose.tools.assert_equal(s.get_take_off_angle(), 12.886929785732487)


class Test_get_lines_intentisity(object):

    def setUp(self):
        # Create an empty spectrum
        s = EDSSEMSpectrum(np.zeros((2, 2, 3, 100)))
        energy_axis = s.axes_manager.signal_axes[0]
        energy_axis.scale = 0.04
        energy_axis.units = u'keV'
        energy_axis.name = u"Energy"
        g = Gaussian()
        g.sigma.value = 0.05
        g.centre.value = 1.487
        s.data[:] = g.function(energy_axis.axis)
        s.metadata.Acquisition_instrument.SEM.Detector.EDS.live_time = 3.1
        s.metadata.Acquisition_instrument.SEM.beam_energy = 15.0
        self.signal = s

    def test(self):
        s = self.signal
        sAl = s.get_lines_intensity([u"Al_Ka"],
                                    plot_result=False,
                                    integration_windows=5)[0]
        nose.tools.assert_true(
            np.allclose(24.99516, sAl.data[0, 0, 0], atol=1e-3))
        sAl = s.inav[0].get_lines_intensity([u"Al_Ka"],
                                       plot_result=False,
                                       integration_windows=5)[0]
        nose.tools.assert_true(
            np.allclose(24.99516, sAl.data[0, 0], atol=1e-3))
        sAl = s.inav[0, 0].get_lines_intensity([u"Al_Ka"],
                                          plot_result=False,
                                          integration_windows=5)[0]
        nose.tools.assert_true(np.allclose(24.99516, sAl.data[0], atol=1e-3))
        sAl = s.inav[0, 0, 0].get_lines_intensity([u"Al_Ka"],
                                             plot_result=False,
                                             integration_windows=5)[0]
        nose.tools.assert_true(np.allclose(24.99516, sAl.data, atol=1e-3))
        s.axes_manager[-1].offset = 1.0
        sC = s.get_lines_intensity([u"C_Ka"], plot_result=False)
        nose.tools.assert_equal(len(sC), 0)
        nose.tools.assert_true(sAl.metadata.Sample.elements, [u"Al"])
        nose.tools.assert_true(sAl.metadata.Sample.xray_lines, [u"Al_Ka"])

    def test_eV(self):
        s = self.signal
        energy_axis = s.axes_manager.signal_axes[0]
        energy_axis.scale = 40
        energy_axis.units = u'eV'

        sAl = s.get_lines_intensity([u"Al_Ka"],
                                    plot_result=False,
                                    integration_windows=5)[0]
        nose.tools.assert_true(
            np.allclose(24.99516, sAl.data[0, 0, 0], atol=1e-3))

    def test_background_substraction(self):
        s = self.signal
        intens = s.get_lines_intensity([u"Al_Ka"], plot_result=False)[0].data
        s += 1.
        nose.tools.assert_true(np.allclose(s.estimate_background_windows(
            xray_lines=[u"Al_Ka"])[0, 0], 1.25666201, atol=1e-3))
        nose.tools.assert_true(np.allclose(s.get_lines_intensity(
            [u"Al_Ka"], background_windows=s.estimate_background_windows(
                [4, 4], xray_lines=[u"Al_Ka"]), plot_result=False)[0].data,
            intens, atol=1e-3))

    def test_estimate_integration_windows(self):
        s = self.signal
        nose.tools.assert_true(np.allclose(
            s.estimate_integration_windows(3.0, [u"Al_Ka"]),
            [[1.371, 1.601]], atol=1e-2))

    def test_with_signals_examples(self):
        from hyperspy.misc.example_signals_loading import \
            load_1D_EDS_SEM_spectrum as EDS_SEM_Spectrum
        s = EDS_SEM_Spectrum()
        np.allclose(utils.stack(s.get_lines_intensity()).data,
                    np.array([84163, 89063, 96117, 96700, 99075]))


class Test_tools_bulk(object):

    def setUp(self):
        s = EDSSEMSpectrum(np.ones(1024))
        s.metadata.Acquisition_instrument.SEM.beam_energy = 5.0
        energy_axis = s.axes_manager.signal_axes[0]
        energy_axis.scale = 0.01
        energy_axis.units = u'keV'
        s.set_elements([u'Al', u'Zn'])
        s.add_lines()
        self.signal = s

    def test_electron_range(self):
        s = self.signal
        mp = s.metadata
        elec_range = utils.eds.electron_range(
            mp.Sample.elements[0],
            mp.Acquisition_instrument.SEM.beam_energy,
            density=u'auto',
            tilt=mp.Acquisition_instrument.SEM.tilt_stage)
        nose.tools.assert_equal(elec_range, 0.41350651162374225)

    def test_xray_range(self):
        s = self.signal
        mp = s.metadata
        xr_range = utils.eds.xray_range(
            mp.Sample.xray_lines[0],
            mp.Acquisition_instrument.SEM.beam_energy,
            density=4.37499648818)
        nose.tools.assert_equal(xr_range, 0.1900368800933955)


class Test_energy_units(object):

    def setUp(self):
        s = EDSSEMSpectrum(np.ones(1024))
        s.metadata.Acquisition_instrument.SEM.beam_energy = 5.0
        s.axes_manager.signal_axes[0].units = u'keV'
        s.set_microscope_parameters(energy_resolution_MnKa=130)
        self.signal = s

    def test_beam_energy(self):
        s = self.signal
        nose.tools.assert_equal(s._get_beam_energy(), 5.0)
        s.axes_manager.signal_axes[0].units = u'eV'
        nose.tools.assert_equal(s._get_beam_energy(), 5000.0)
        s.axes_manager.signal_axes[0].units = u'keV'

    def test_line_energy(self):
        s = self.signal
        nose.tools.assert_equal(s._get_line_energy(u'Al_Ka'), 1.4865)
        s.axes_manager.signal_axes[0].units = u'eV'
        nose.tools.assert_equal(s._get_line_energy(u'Al_Ka'), 1486.5)
        s.axes_manager.signal_axes[0].units = u'keV'

        nose.tools.assert_equal(s._get_line_energy(u'Al_Ka', FWHM_MnKa=u'auto'),
                                (1.4865, 0.07661266213883969))
        nose.tools.assert_equal(s._get_line_energy(u'Al_Ka', FWHM_MnKa=128),
                                (1.4865, 0.073167615787314))
