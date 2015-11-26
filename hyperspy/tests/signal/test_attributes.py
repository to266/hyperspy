# -*- coding: utf-8 -*-
from nose.tools import assert_equal

import hyperspy.signals
import hyperspy.signal


def test_signal_record_by():
    assert_equal(hyperspy.signal.Signal._record_by, u"")


def test_signal_signal_type():
    assert_equal(hyperspy.signal.Signal._signal_type, u"")


def test_signal_signal_origin():
    assert_equal(hyperspy.signal.Signal._signal_origin, u"")


def test_spectrum_record_by():
    assert_equal(hyperspy.signals.Spectrum._record_by, u"spectrum")


def test_spectrum_signal_type():
    assert_equal(hyperspy.signals.Spectrum._signal_type, u"")


def test_spectrum_signal_origin():
    assert_equal(hyperspy.signals.Spectrum._signal_origin, u"")


def test_image_record_by():
    assert_equal(hyperspy.signals.Image._record_by, u"image")


def test_image_signal_type():
    assert_equal(hyperspy.signals.Image._signal_type, u"")


def test_image_signal_origin():
    assert_equal(hyperspy.signals.Image._signal_origin, u"")


def test_simulation_record_by():
    assert_equal(hyperspy.signals.Simulation._record_by, u"")


def test_simulation_signal_type():
    assert_equal(hyperspy.signals.Simulation._signal_type, u"")


def test_simulation_signal_origin():
    assert_equal(hyperspy.signals.Simulation._signal_origin, u"simulation")


def test_spectrum_simulation_record_by():
    assert_equal(hyperspy.signals.SpectrumSimulation._record_by, u"spectrum")


def test_spectrum_simulation_signal_type():
    assert_equal(hyperspy.signals.SpectrumSimulation._signal_type, u"")


def test_spectrum_simulation_signal_origin():
    assert_equal(hyperspy.signals.SpectrumSimulation._signal_origin,
                 u"simulation")


def test_image_simulation_record_by():
    assert_equal(hyperspy.signals.ImageSimulation._record_by, u"image")


def test_image_simulation_signal_type():
    assert_equal(hyperspy.signals.ImageSimulation._signal_type, u"")


def test_image_simulation_signal_origin():
    assert_equal(hyperspy.signals.ImageSimulation._signal_origin,
                 u"simulation")


def test_eels_record_by():
    assert_equal(hyperspy.signals.EELSSpectrum._record_by, u"spectrum")


def test_eels_signal_type():
    assert_equal(hyperspy.signals.EELSSpectrum._signal_type, u"EELS")


def test_eels_signal_origin():
    assert_equal(hyperspy.signals.EELSSpectrum._signal_origin, u"")
