import numpy as np
import nose.tools

import hyperspy.api as hs
from hyperspy.misc.utils import slugify
from itertools import izip


class TestModel(object):

    def setUp(self):
        s = hs.signals.Spectrum(np.empty(1))
        m = s.create_model()
        self.model = m

    def test_access_component_by_name(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g2.name = u"test"
        m.extend((g1, g2))
        nose.tools.assert_is(m[u"test"], g2)

    def test_access_component_by_index(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g2.name = u"test"
        m.extend((g1, g2))
        nose.tools.assert_is(m[1], g2)

    def test_component_name_when_append(self):
        m = self.model
        gs = [
            hs.model.components.Gaussian(),
            hs.model.components.Gaussian(),
            hs.model.components.Gaussian()]
        m.extend(gs)
        nose.tools.assert_is(m[u'Gaussian'], gs[0])
        nose.tools.assert_is(m[u'Gaussian_0'], gs[1])
        nose.tools.assert_is(m[u'Gaussian_1'], gs[2])

    @nose.tools.raises(ValueError)
    def test_several_component_with_same_name(self):
        m = self.model
        gs = [
            hs.model.components.Gaussian(),
            hs.model.components.Gaussian(),
            hs.model.components.Gaussian()]
        m.extend(gs)
        m[0]._name = u"hs.model.components.Gaussian"
        m[1]._name = u"hs.model.components.Gaussian"
        m[2]._name = u"hs.model.components.Gaussian"
        m[u'Gaussian']

    @nose.tools.raises(ValueError)
    def test_no_component_with_that_name(self):
        m = self.model
        m[u'Voigt']

    @nose.tools.raises(ValueError)
    def test_component_already_in_model(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.extend((g1, g1))

    def test_remove_component(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        m.remove(g1)
        nose.tools.assert_equal(len(m), 0)

    def test_remove_component_by_index(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        m.remove(0)
        nose.tools.assert_equal(len(m), 0)

    def test_remove_component_by_name(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        m.remove(g1.name)
        nose.tools.assert_equal(len(m), 0)

    def test_delete_component_by_index(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        del m[0]
        nose.tools.assert_not_in(g1, m)

    def test_delete_component_by_name(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        del m[g1.name]
        nose.tools.assert_not_in(g1, m)

    def test_delete_slice(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g3 = hs.model.components.Gaussian()
        m.extend([g1, g2, g3])
        del m[:2]
        nose.tools.assert_not_in(g1, m)
        nose.tools.assert_not_in(g2, m)
        nose.tools.assert_in(g3, m)

    def test_get_component_by_name(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g2.name = u"test"
        m.extend((g1, g2))
        nose.tools.assert_is(m._get_component(u"test"), g2)

    def test_get_component_by_index(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g2.name = u"test"
        m.extend((g1, g2))
        nose.tools.assert_is(m._get_component(1), g2)

    def test_get_component_by_component(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g2.name = u"test"
        m.extend((g1, g2))
        nose.tools.assert_is(m._get_component(g2), g2)

    @nose.tools.raises(ValueError)
    def test_get_component_wrong(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        g2 = hs.model.components.Gaussian()
        g2.name = u"test"
        m.extend((g1, g2))
        m._get_component(1.2)

    def test_components_class_default(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        nose.tools.assert_is(getattr(m.components, g1.name), g1)

    def test_components_class_change_name(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        g1.name = u"test"
        nose.tools.assert_is(getattr(m.components, g1.name), g1)

    @nose.tools.raises(AttributeError)
    def test_components_class_change_name_del_default(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        g1.name = u"test"
        getattr(m.components, u"Gaussian")

    def test_components_class_change_invalid_name(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        g1.name = u"1, Test This!"
        nose.tools.assert_is(
            getattr(m.components,
                    slugify(g1.name, valid_variable_name=True)), g1)

    @nose.tools.raises(AttributeError)
    def test_components_class_change_name_del_default(self):
        m = self.model
        g1 = hs.model.components.Gaussian()
        m.append(g1)
        invalid_name = u"1, Test This!"
        g1.name = invalid_name
        g1.name = u"test"
        getattr(m.components, slugify(invalid_name))


class TestModelFitBinned(object):

    def setUp(self):
        np.random.seed(1)
        s = hs.signals.Spectrum(
            np.random.normal(
                scale=2,
                size=10000)).get_histogram()
        s.metadata.Signal.binned = True
        g = hs.model.components.Gaussian()
        m = s.create_model()
        m.append(g)
        g.sigma.value = 1
        g.centre.value = 0.5
        g.A.value = 1e3
        self.m = m

    def test_fit_fmin_leastsq(self):
        self.m.fit(fitter=u"fmin", method=u"ls")
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14519369)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.110610743285)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380705455)

    def test_fit_fmin_ml(self):
        self.m.fit(fitter=u"fmin", method=u"ml")
        np.testing.assert_almost_equal(self.m[0].A.value, 10001.39613936,
                                       decimal=3)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.104151206314,
                                       decimal=6)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 2.00053642434)

    def test_fit_leastsq(self):
        self.m.fit(fitter=u"leastsq")
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14526082, 1)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.110610727064)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380707571, 5)

    def test_fit_mpfit(self):
        self.m.fit(fitter=u"mpfit")
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14526286, 5)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.110610718444)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380707614)

    def test_fit_odr(self):
        self.m.fit(fitter=u"odr")
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14531979, 3)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.110610724054)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380709939)

    def test_fit_leastsq_grad(self):
        self.m.fit(fitter=u"leastsq", grad=True)
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14526084)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.11061073306)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380707552)

    def test_fit_mpfit_grad(self):
        self.m.fit(fitter=u"mpfit", grad=True)
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14526084)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.11061073306)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380707552)

    def test_fit_odr_grad(self):
        self.m.fit(fitter=u"odr", grad=True)
        np.testing.assert_almost_equal(self.m[0].A.value, 9976.14531979, 3)
        np.testing.assert_almost_equal(self.m[0].centre.value, -0.110610724054)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 1.98380709939)

    def test_fit_bounded(self):
        self.m[0].centre.bmin = 0.5
        self.m[0].bounded = True
        self.m.fit(fitter=u"mpfit", bounded=True)
        np.testing.assert_almost_equal(self.m[0].A.value, 9991.65422046, 4)
        np.testing.assert_almost_equal(self.m[0].centre.value, 0.5)
        np.testing.assert_almost_equal(self.m[0].sigma.value, 2.08398236966)

    @nose.tools.raises(ValueError)
    def test_wrong_method(self):
        self.m.fit(method=u"dummy")


class TestModelWeighted(object):

    def setUp(self):
        np.random.seed(1)
        s = hs.signals.SpectrumSimulation(np.arange(10, 100, 0.1))
        s.metadata.set_item(u"Signal.Noise_properties.variance",
                            hs.signals.Spectrum(np.arange(10, 100, 0.01)))
        s.axes_manager[0].scale = 0.1
        s.axes_manager[0].offset = 10
        s.add_poissonian_noise()
        m = s.create_model()
        m.append(hs.model.components.Polynomial(1))
        self.m = m

    def test_fit_leastsq_binned(self):
        self.m.spectrum.metadata.Signal.binned = True
        self.m.fit(fitter=u"leastsq", method=u"ls")
        for result, expected in izip(self.m[0].coefficients.value,
                                    (9.9165596693502778, 1.6628238107916631)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_odr_binned(self):
        self.m.spectrum.metadata.Signal.binned = True
        self.m.fit(fitter=u"odr", method=u"ls")
        for result, expected in izip(self.m[0].coefficients.value,
                                    (9.9165596548961972, 1.6628247412317521)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_mpfit_binned(self):
        self.m.spectrum.metadata.Signal.binned = True
        self.m.fit(fitter=u"mpfit", method=u"ls")
        for result, expected in izip(self.m[0].coefficients.value,
                                    (9.9165596607108739, 1.6628243846485873)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_fmin_binned(self):
        self.m.spectrum.metadata.Signal.binned = True
        self.m.fit(
            fitter=u"fmin",
            method=u"ls",
        )
        for result, expected in izip(self.m[0].coefficients.value,
                                    (9.9137288425667442, 1.8446013472266145)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_leastsq_unbinned(self):
        self.m.spectrum.metadata.Signal.binned = False
        self.m.fit(fitter=u"leastsq", method=u"ls")
        for result, expected in izip(
                self.m[0].coefficients.value,
                (0.99165596391487121, 0.16628254242532492)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_odr_unbinned(self):
        self.m.spectrum.metadata.Signal.binned = False
        self.m.fit(fitter=u"odr", method=u"ls")
        for result, expected in izip(
                self.m[0].coefficients.value,
                (0.99165596548961943, 0.16628247412317315)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_mpfit_unbinned(self):
        self.m.spectrum.metadata.Signal.binned = False
        self.m.fit(fitter=u"mpfit", method=u"ls")
        for result, expected in izip(
                self.m[0].coefficients.value,
                (0.99165596295068958, 0.16628257462820528)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_fit_fmin_unbinned(self):
        self.m.spectrum.metadata.Signal.binned = False
        self.m.fit(
            fitter=u"fmin",
            method=u"ls",
        )
        for result, expected in izip(
                self.m[0].coefficients.value,
                (0.99136169230026261, 0.18483060534056939)):
            np.testing.assert_almost_equal(result, expected, decimal=5)

    def test_chisq(self):
        self.m.spectrum.metadata.Signal.binned = True
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.chisq.data, 3029.16949561)

    def test_red_chisq(self):
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.red_chisq.data, 3.37700055)


class TestModelScalarVariance(object):

    def setUp(self):
        s = hs.signals.SpectrumSimulation(np.ones(100))
        m = s.create_model()
        m.append(hs.model.components.Offset())
        self.s = s
        self.m = m

    def test_std1_chisq(self):
        std = 1
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.metadata.set_item(u"Signal.Noise_properties.variance", std ** 2)
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.chisq.data, 78.35015229)

    def test_std10_chisq(self):
        std = 10
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.metadata.set_item(u"Signal.Noise_properties.variance", std ** 2)
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.chisq.data, 78.35015229)

    def test_std1_red_chisq(self):
        std = 1
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.metadata.set_item(u"Signal.Noise_properties.variance", std ** 2)
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.red_chisq.data, 0.79949135)

    def test_std10_red_chisq(self):
        std = 10
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.metadata.set_item(u"Signal.Noise_properties.variance", std ** 2)
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.red_chisq.data, 0.79949135)

    def test_std1_red_chisq_in_range(self):
        std = 1
        self.m.set_signal_range(10, 50)
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.metadata.set_item(u"Signal.Noise_properties.variance", std ** 2)
        self.m.fit(fitter=u"leastsq", method=u"ls")
        np.testing.assert_almost_equal(self.m.red_chisq.data, 0.86206965)


class TestModelSignalVariance(object):

    def setUp(self):
        variance = hs.signals.SpectrumSimulation(
            np.arange(
                100, 300).reshape(
                (2, 100)))
        s = variance.deepcopy()
        np.random.seed(1)
        std = 10
        s.add_gaussian_noise(std)
        s.add_poissonian_noise()
        s.metadata.set_item(u"Signal.Noise_properties.variance",
                            variance + std ** 2)
        m = s.create_model()
        m.append(hs.model.components.Polynomial(order=1))
        self.s = s
        self.m = m

    def test_std1_red_chisq(self):
        self.m.multifit(fitter=u"leastsq", method=u"ls", show_progressbar=None)
        np.testing.assert_almost_equal(self.m.red_chisq.data[0],
                                        0.79693355673230915)
        np.testing.assert_almost_equal(self.m.red_chisq.data[1],
                                        0.91453032901427167)


class TestMultifit(object):

    def setUp(self):
        s = hs.signals.Spectrum(np.empty((2, 200)))
        s.axes_manager[-1].offset = 1
        s.data[:] = 2 * s.axes_manager[-1].axis ** (-3)
        m = s.create_model()
        m.append(hs.model.components.PowerLaw())
        m[0].A.value = 2
        m[0].r.value = 2
        m.store_current_values()
        m.axes_manager.indices = (1,)
        m[0].r.value = 100
        m[0].A.value = 2
        m.store_current_values()
        m[0].A.free = False
        self.m = m
        m.axes_manager.indices = (0,)
        m[0].A.value = 100

    def test_fetch_only_fixed_false(self):
        self.m.multifit(fetch_only_fixed=False, show_progressbar=None)
        np.testing.assert_array_almost_equal(self.m[0].r.map[u'values'],
                                             [3., 100.])
        np.testing.assert_array_almost_equal(self.m[0].A.map[u'values'],
                                             [2., 2.])

    def test_fetch_only_fixed_true(self):
        self.m.multifit(fetch_only_fixed=True, show_progressbar=None)
        np.testing.assert_array_almost_equal(self.m[0].r.map[u'values'],
                                             [3., 3.])
        np.testing.assert_array_almost_equal(self.m[0].A.map[u'values'],
                                             [2., 2.])


class TestStoreCurrentValues(object):

    def setUp(self):
        self.m = hs.signals.Spectrum(np.arange(10)).create_model()
        self.o = hs.model.components.Offset()
        self.m.append(self.o)

    def test_active(self):
        self.o.offset.value = 2
        self.o.offset.std = 3
        self.m.store_current_values()
        nose.tools.assert_equal(self.o.offset.map[u"values"][0], 2)
        nose.tools.assert_equal(self.o.offset.map[u"is_set"][0], True)

    def test_not_active(self):
        self.o.active = False
        self.o.offset.value = 2
        self.o.offset.std = 3
        self.m.store_current_values()
        nose.tools.assert_not_equal(self.o.offset.map[u"values"][0], 2)


class TestSetCurrentValuesTo(object):

    def setUp(self):
        self.m = hs.signals.Spectrum(
            np.arange(10).reshape(2, 5)).create_model()
        self.comps = [
            hs.model.components.Offset(),
            hs.model.components.Offset()]
        self.m.extend(self.comps)

    def test_set_all(self):
        for c in self.comps:
            c.offset.value = 2
        self.m.assign_current_values_to_all()
        nose.tools.assert_true((self.comps[0].offset.map[u"values"] == 2).all())
        nose.tools.assert_true((self.comps[1].offset.map[u"values"] == 2).all())

    def test_set_1(self):
        self.comps[1].offset.value = 2
        self.m.assign_current_values_to_all([self.comps[1]])
        nose.tools.assert_true((self.comps[0].offset.map[u"values"] != 2).all())
        nose.tools.assert_true((self.comps[1].offset.map[u"values"] == 2).all())


class TestAsSignal(object):

    def setUp(self):
        self.m = hs.signals.Spectrum(
            np.arange(10).reshape(2, 5)).create_model()
        self.comps = [
            hs.model.components.Offset(),
            hs.model.components.Offset()]
        self.m.extend(self.comps)
        for c in self.comps:
            c.offset.value = 2
        self.m.assign_current_values_to_all()

    def test_all_components_simple(self):
        s = self.m.as_signal(show_progressbar=None)
        nose.tools.assert_true(np.all(s.data == 4.))

    def test_one_component_simple(self):
        s = self.m.as_signal(component_list=[0], show_progressbar=None)
        nose.tools.assert_true(np.all(s.data == 2.))
        nose.tools.assert_true(self.m[1].active)

    def test_all_components_multidim(self):
        self.m[0].active_is_multidimensional = True

        s = self.m.as_signal(show_progressbar=None)
        nose.tools.assert_true(np.all(s.data == 4.))

        self.m[0]._active_array[0] = False
        s = self.m.as_signal(show_progressbar=None)
        nose.tools.assert_true(
            np.all(s.data == np.array([np.ones(5) * 2, np.ones(5) * 4])))
        nose.tools.assert_true(self.m[0].active_is_multidimensional)

    def test_one_component_multidim(self):
        self.m[0].active_is_multidimensional = True

        s = self.m.as_signal(component_list=[0], show_progressbar=None)
        nose.tools.assert_true(np.all(s.data == 2.))
        nose.tools.assert_true(self.m[1].active)
        nose.tools.assert_false(self.m[1].active_is_multidimensional)

        s = self.m.as_signal(component_list=[1], show_progressbar=None)
        nose.tools.assert_true(np.all(s.data == 2.))
        nose.tools.assert_true(self.m[0].active_is_multidimensional)

        self.m[0]._active_array[0] = False
        s = self.m.as_signal(component_list=[1], show_progressbar=None)
        nose.tools.assert_true(np.all(s.data == 2.))

        s = self.m.as_signal(component_list=[0], show_progressbar=None)
        nose.tools.assert_true(
            np.all(s.data == np.array([np.zeros(5), np.ones(5) * 2])))


class TestCreateModel(object):

    def setUp(self):
        self.s = hs.signals.Spectrum(np.asarray([0, ]))

    def test_create_model(self):
        from hyperspy.model import Model
        nose.tools.assert_is_instance(
            self.s.create_model(), Model)
