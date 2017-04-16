# Copyright 2007-2016 The HyperSpy developers
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

import scipy.misc
import pytest
import matplotlib.pyplot as plt
import os
from shutil import copyfile

import hyperspy.api as hs
from hyperspy.misc.test_utils import update_close_figure
from hyperspy.tests.drawing.test_plot_signal import _TestPlot


scalebar_color = 'blue'
default_tol = 2.0
baseline_dir = 'plot_signal1d'

style = ['default', 'overlap', 'cascade', 'mosaic', 'heatmap']


def _generate_filename_list():
    path = os.path.dirname(__file__)
    filename_list = ['test_plot_spectra_%s' % s for s in style]
    filename_list2 = []
    for filename in filename_list:
        for i in range(0, 4):
            filename_list2.append(os.path.join(path, baseline_dir,
                                               '%s%i.png' % (filename, i)))
    return filename_list2


class TestPlotSpectra():

    s = hs.signals.Signal1D(scipy.misc.ascent()[100:160:10])

    @classmethod
    def setup_class(cls):
        # duplicate baseline images to match the test_name when the
        # parametrized 'test_plot_spectra' are run.
        for filename in _generate_filename_list():
            copyfile("%s.png" % filename[:-5], filename)

    @classmethod
    def teardown_class(cls):
        for filename in _generate_filename_list():
            os.remove(filename)

    def _generate_parameters(style):
        parameters = []
        for s in style:
            for fig in [True, None]:
                for ax in [True, None]:
                    parameters.append([s, fig, ax])
        return parameters

    def _generate_ids(style, duplicate=4):
        ids = []
        for s in style:
            ids.extend([s] * duplicate)
        return ids

    @pytest.mark.parametrize(("style", "fig", "ax"),
                             _generate_parameters(style[:-2]),
                             ids=_generate_ids(style[:-2]))
    @pytest.mark.mpl_image_compare(baseline_dir=baseline_dir,
                                   tolerance=default_tol)
    def test_plot_spectra(self, mpl_cleanup, style, fig, ax):
        if fig:
            fig = plt.figure()
        if ax:
            fig = plt.figure()
            ax = fig.add_subplot(111)

        ax = hs.plot.plot_spectra(self.s, style=style, legend='auto',
                                  fig=fig, ax=ax)
        if style == 'mosaic':
            ax = ax[0]
        return ax.figure

    @pytest.mark.parametrize("figure", ['1nav', '1sig', '2nav', '2sig'])
    @pytest.mark.mpl_image_compare(baseline_dir=baseline_dir,
                                   tolerance=default_tol)
    def test_plot_spectra_sync(self, mpl_cleanup, figure):
        s1 = hs.signals.Signal1D(scipy.misc.face()).as_signal1D(0).inav[:, :3]
        s2 = s1.deepcopy() * -1
        hs.plot.plot_signals([s1, s2])
        if figure == '1nav':
            return s1._plot.signal_plot.figure
        if figure == '1sig':
            return s1._plot.navigator_plot.figure
        if figure == '2nav':
            return s2._plot.navigator_plot.figure
        if figure == '2sig':
            return s2._plot.navigator_plot.figure


@update_close_figure
def test_plot_nav0_close():
    test_plot = _TestPlot(ndim=0, sdim=1)
    test_plot.signal.plot()
    return test_plot.signal


@update_close_figure
def test_plot_nav1_close():
    test_plot = _TestPlot(ndim=1, sdim=1)
    test_plot.signal.plot()
    return test_plot.signal


@update_close_figure
def test_plot_nav2_close():
    test_plot = _TestPlot(ndim=2, sdim=1)
    test_plot.signal.plot()
    return test_plot.signal


def _test_plot_two_cursors(ndim):
    test_plot = _TestPlot(ndim=ndim, sdim=1)  # sdim=2 not supported
    test_plot.signal.plot()
    s = test_plot.signal
    s.metadata.General.title = 'Nav %i, Sig 1, two cursor' % ndim
    s.axes_manager[0].index = 4
    s.plot()
    s._plot.add_right_pointer()
    s._plot.right_pointer.axes_manager[0].index = 2
    if ndim == 2:
        s.axes_manager[1].index = 2
        s._plot.right_pointer.axes_manager[1].index = 3
    return s


def _generate_parameter():
    parameters = []
    for ndim in [1, 2]:
        for plot_type in ['nav', 'sig']:
            parameters.append([ndim, plot_type])
    return parameters


@pytest.mark.parametrize(("ndim", "plot_type"),
                         _generate_parameter())
@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir,
                               tolerance=default_tol)
def test_plot_two_cursors(mpl_cleanup, ndim, plot_type):
    s = _test_plot_two_cursors(ndim=ndim)
    if plot_type == "sig":
        return s._plot.signal_plot.figure
    else:
        return s._plot.navigator_plot.figure


@update_close_figure
def test_plot_nav2_sig1_two_cursors_close():
    return _test_plot_two_cursors(ndim=2)
