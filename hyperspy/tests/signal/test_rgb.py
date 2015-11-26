import numpy as np
from nose.tools import assert_true, raises

from hyperspy.misc import rgb_tools
import hyperspy.api as hs


class TestRGBA8(object):

    def setUp(self):
        self.s = hs.signals.Spectrum(np.array(
            [[[1, 1, 1, 0],
              [2, 2, 2, 0]],
             [[3, 3, 3, 0],
              [4, 4, 4, 0]]],
            dtype=u"uint8"))
        self.im = hs.signals.Spectrum(np.array(
            [[(1, 1, 1, 0), (2, 2, 2, 0)],
             [(3, 3, 3, 0), (4, 4, 4, 0)]],
            dtype=rgb_tools.rgba8))

    def test_torgb(self):
        self.s.change_dtype(u"rgba8")
        assert_true(np.all(self.s.data == self.im.data))

    def test_touint(self):
        self.im.change_dtype(u"uint8")
        assert_true(np.all(self.s.data == self.im.data))

    @raises(AttributeError)
    def test_wrong_bs(self):
        self.s.change_dtype(u"rgba16")

    @raises(AttributeError)
    def test_wrong_rgb(self):
        self.im.change_dtype(u"rgb8")


class TestRGBA16(object):

    def setUp(self):
        self.s = hs.signals.Spectrum(np.array(
            [[[1, 1, 1, 0],
              [2, 2, 2, 0]],
             [[3, 3, 3, 0],
              [4, 4, 4, 0]]],
            dtype=u"uint16"))
        self.im = hs.signals.Spectrum(np.array(
            [[(1, 1, 1, 0), (2, 2, 2, 0)],
             [(3, 3, 3, 0), (4, 4, 4, 0)]],
            dtype=rgb_tools.rgba16))

    def test_torgb(self):
        self.s.change_dtype(u"rgba16")
        assert_true(np.all(self.s.data == self.im.data))

    def test_touint(self):
        self.im.change_dtype(u"uint16")
        assert_true(np.all(self.s.data == self.im.data))

    @raises(AttributeError)
    def test_wrong_bs(self):
        self.s.change_dtype(u"rgba8")

    @raises(AttributeError)
    def test_wrong_rgb(self):
        self.im.change_dtype(u"rgb16")
