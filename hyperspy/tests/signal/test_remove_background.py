import numpy as np
from nose.tools import (
    assert_true,)

from hyperspy import signals
from hyperspy import components


class TestRemoveBackground1DGaussian(object):

    def setUp(self):
        gaussian = components.Gaussian()
        gaussian.A.value = 10
        gaussian.centre.value = 10
        gaussian.sigma.value = 1
        self.signal = signals.Spectrum(
            gaussian.function(np.arange(0, 20, 0.01)))
        self.signal.axes_manager[0].scale = 0.01
        self.signal.metadata.Signal.binned = False

    def test_background_remove_gaussian(self):
        s1 = self.signal.remove_background(
            signal_range=(None, None),
            background_type=u'Gaussian',
            show_progressbar=None)
        assert_true(np.allclose(s1.data, np.zeros(len(s1.data))))

    def test_background_remove_gaussian_full_fit(self):
        s1 = self.signal.remove_background(
            signal_range=(None, None),
            background_type=u'Gaussian',
            estimate_background=False)
        assert_true(np.allclose(s1.data, np.zeros(len(s1.data))))


class TestRemoveBackground1DPowerLaw(object):

    def setUp(self):
        pl = components.PowerLaw()
        pl.A.value = 1e10
        pl.r.value = 3
        self.signal = signals.Spectrum(
            pl.function(np.arange(100, 200)))
        self.signal.axes_manager[0].offset = 100
        self.signal.metadata.Signal.binned = False

    def test_background_remove_pl(self):
        s1 = self.signal.remove_background(
            signal_range=(None, None),
            background_type=u'PowerLaw',
            show_progressbar=None)
        assert_true(np.allclose(s1.data, np.zeros(len(s1.data)), atol=60))

    def test_background_remove_pl_int(self):
        self.signal.change_dtype(u"int")
        s1 = self.signal.remove_background(
            signal_range=(None, None),
            background_type=u'PowerLaw',
            show_progressbar=None)
        assert_true(np.allclose(s1.data, np.zeros(len(s1.data)), atol=60))
