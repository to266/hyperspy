from nose.tools import assert_true

import hyperspy.api as hs
from hyperspy.io import assign_signal_subclass


def test_signal():
    assert_true(assign_signal_subclass(
        record_by=u"",
        signal_type=u"",
        signal_origin=u"") is hs.signals.Signal)


def test_spectrum():
    assert_true(assign_signal_subclass(
        record_by=u"spectrum",
        signal_type=u"",
        signal_origin=u"") is hs.signals.Spectrum)


def test_image():
    assert_true(assign_signal_subclass(
        record_by=u"image",
        signal_type=u"",
        signal_origin=u"") is hs.signals.Image)


def test_image_simulation():
    assert_true(assign_signal_subclass(
        record_by=u"image",
        signal_type=u"",
        signal_origin=u"simulation") is hs.signals.ImageSimulation)


def test_eels_spectrum():
    assert_true(assign_signal_subclass(
        record_by=u"spectrum",
        signal_type=u"EELS",
        signal_origin=u"") is hs.signals.EELSSpectrum)


def test_eels_spectrum_simulation():
    assert_true(assign_signal_subclass(
        record_by=u"spectrum",
        signal_type=u"EELS",
        signal_origin=u"simulation") is
        hs.signals.EELSSpectrumSimulation)


def test_weird_spectrum():
    cls = assign_signal_subclass(
        record_by=u"spectrum",
        signal_type=u"weird",
        signal_origin=u"")
    assert_true(cls is hs.signals.Spectrum)


class TestSignalAssignSubclass(object):

    def setUp(self):
        self.s = hs.signals.Spectrum([0])

    def test_type_to_eels(self):
        self.s.set_signal_type(u"EELS")
        assert_true(isinstance(self.s, hs.signals.EELSSpectrum))

    def test_type_to_spectrumsimulation(self):
        self.s.set_signal_origin(u"simulation")
        assert_true(isinstance(self.s, hs.signals.SpectrumSimulation))
