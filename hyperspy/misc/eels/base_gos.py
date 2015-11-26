

from __future__ import division
import numpy as np

from hyperspy.misc.math_tools import get_linear_interpolation
from hyperspy.misc.elements import elements


class GOSBase(object):

    def read_elements(self):
        element = self.element
        subshell = self.subshell
        # Convert to the "GATAN" nomenclature
        if (element in elements) is not True:
            raise ValueError(u"The given element " + element +
                             u" is not in the database.")
        elif subshell not in elements[element][u'Atomic_properties'][u'Binding_energies']:
            raise ValueError(
                u"The given subshell " + subshell +
                u" is not in the database.\n" +
                u"The available subshells are:\n" +
                unicode(list(elements[element][u'Atomic_properties'][u'subshells'].keys())))

        self.onset_energy = \
            elements[
                element][
                u'Atomic_properties'][
                u'Binding_energies'][
                subshell][
                u'onset_energy (eV)']
        self.subshell_factor = \
            elements[
                element][
                u'Atomic_properties'][
                u'Binding_energies'][
                subshell][
                u'factor']
        self.Z = elements[element][u'General_properties'][u'Z']
        self.element_dict = elements[element]

    def get_parametrized_qaxis(self, k1, k2, n):
        return k1 * (np.exp(np.arange(n) * k2) - 1) * 1e10

    def get_parametrized_energy_axis(self, k1, k2, n):
        return k1 * (np.exp(np.arange(n) * k2 / k1) - 1)

    def get_qaxis_and_gos(self, ienergy, qmin, qmax):
        qgosi = self.gos_array[ienergy, :]
        if qmax > self.qaxis[-1]:
            # Linear extrapolation
            g1, g2 = qgosi[-2:]
            q1, q2 = self.qaxis[-2:]
            gosqmax = get_linear_interpolation((q1, g1), (q2, g2), qmax)
            qaxis = np.hstack((self.qaxis, qmax))
            qgosi = np.hstack((qgosi, gosqmax))
        else:
            index = self.qaxis.searchsorted(qmax)
            g1, g2 = qgosi[index - 1:index + 1]
            q1, q2 = self.qaxis[index - 1: index + 1]
            gosqmax = get_linear_interpolation((q1, g1), (q2, g2), qmax)
            qaxis = np.hstack((self.qaxis[:index], qmax))
            qgosi = np.hstack((qgosi[:index, ], gosqmax))

        if qmin > 0:
            index = self.qaxis.searchsorted(qmin)
            g1, g2 = qgosi[index - 1:index + 1]
            q1, q2 = qaxis[index - 1:index + 1]
            gosqmin = get_linear_interpolation((q1, g1), (q2, g2), qmin)
            qaxis = np.hstack((qmin, qaxis[index:]))
            qgosi = np.hstack((gosqmin, qgosi[index:],))
        return qaxis, qgosi.clip(0)
