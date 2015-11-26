

from __future__ import division
import numpy as np
import math

from hyperspy.misc.elements import elements as elements_db
def _get_element_and_line(Xray_line):
    lim = Xray_line.find(u'_')
    return Xray_line[:lim], Xray_line[lim + 1:]


def _get_energy_xray_line(xray_line):
    element, line = _get_element_and_line(xray_line)
    return elements_db[element][u'Atomic_properties'][u'Xray_lines'][
        line][u'energy (keV)']


def _parse_only_lines(only_lines):
    if hasattr(only_lines, u'__iter__'):
        if any(isinstance(line, unicode) is False for line in only_lines):
            return only_lines
    elif isinstance(only_lines, unicode) is False:
        return only_lines
    only_lines = list(only_lines)
    for only_line in only_lines:
        if only_line == u'a':
            only_lines.extend([u'Ka', u'La', u'Ma'])
        elif only_line == u'b':
            only_lines.extend([u'Kb', u'Lb1', u'Mb'])
    return only_lines


def get_xray_lines_near_energy(energy, width=0.2, only_lines=None):
    u"""Find xray lines near a specific energy, more specifically all xray lines
    that satisfy only_lines and are within the given energy window width around
    the passed energy.

    Parameters
    ----------
    energy : float
        Energy to search near in keV
    width : float
        Window width in keV around energy in which to find nearby energies,
        i.e. a value of 0.2 keV (the default) means to search +/- 0.1 keV.
    only_lines :
        If not None, only the given lines will be added (eg. ('a','Kb')).

    Returns
    -------
    List of xray-lines sorted by energy difference to given energy.
    """
    only_lines = _parse_only_lines(only_lines)
    valid_lines = []
    E_min, E_max = energy - width/2., energy + width/2.
    for element, el_props in elements_db.items():
        # Not all elements in the DB have the keys, so catch KeyErrors
        try:
            lines = el_props[u'Atomic_properties'][u'Xray_lines']
        except KeyError:
            continue
        for line, l_props in lines.items():
            if only_lines and line not in only_lines:
                continue
            line_energy = l_props[u'energy (keV)']
            if E_min <= line_energy <= E_max:
                # Store line in Element_Line format, and energy difference
                valid_lines.append((element + u"_" + line,
                                    np.abs(line_energy - energy)))
    # Sort by energy difference, but return only the line names
    return [line for line, _ in sorted(valid_lines, key=lambda x: x[1])]


def get_FWHM_at_Energy(energy_resolution_MnKa, E):
    u"""Calculates the FWHM of a peak at energy E.

    Parameters
    ----------
    energy_resolution_MnKa : float
        Energy resolution of Mn Ka in eV
    E : float
        Energy of the peak in keV

    Returns
    -------
    float : FWHM of the peak in keV

    Notes
    -----
    From the textbook of Goldstein et al., Plenum publisher,
    third edition p 315

    """
    FWHM_ref = energy_resolution_MnKa
    E_ref = _get_energy_xray_line(u'Mn_Ka')

    FWHM_e = 2.5 * (E - E_ref) * 1000 + FWHM_ref * FWHM_ref

    return math.sqrt(FWHM_e) / 1000  # In mrad


def xray_range(xray_line, beam_energy, density=u'auto'):
    u"""Return the Anderson-Hasler X-ray range.

    Return the maximum range of X-ray generation in a pure bulk material.

    Parameters
    ----------
    xray_line: str
        The X-ray line, e.g. 'Al_Ka'
    beam_energy: float
        The energy of the beam in kV.
    density: {float, 'auto'}
        The density of the material in g/cm3. If 'auto', the density
        of the pure element is used.

    Returns
    -------
    X-ray range in micrometer.

    Examples
    --------
    >>> # X-ray range of Cu Ka in pure Copper at 30 kV in micron
    >>> hs.eds.xray_range('Cu_Ka', 30.)
    1.9361716759499248

    >>> # X-ray range of Cu Ka in pure Carbon at 30kV in micron
    >>> hs.eds.xray_range('Cu_Ka', 30., hs.material.elements.C.
    >>>                      Physical_properties.density_gcm3)
    7.6418811280855454

    Notes
    -----
    From Anderson, C.A. and M.F. Hasler (1966). In proceedings of the
    4th international conference on X-ray optics and microanalysis.

    See also the textbook of Goldstein et al., Plenum publisher,
    third edition p 286

    """

    element, line = _get_element_and_line(xray_line)
    if density == u'auto':
        density = elements_db[
            element][
            u'Physical_properties'][
            u'density (g/cm^3)']
    Xray_energy = _get_energy_xray_line(xray_line)

    return 0.064 / density * (np.power(beam_energy, 1.68) -
                              np.power(Xray_energy, 1.68))


def electron_range(element, beam_energy, density=u'auto', tilt=0):
    u"""Return the Kanaya-Okayama electron range.

    Return the maximum electron range in a pure bulk material.

    Parameters
    ----------
    element: str
        The element symbol, e.g. 'Al'.
    beam_energy: float
        The energy of the beam in keV.
    density: {float, 'auto'}
        The density of the material in g/cm3. If 'auto', the density of
        the pure element is used.
    tilt: float.
        The tilt of the sample in degrees.

    Returns
    -------
    Electron range in micrometers.

    Examples
    --------
    >>> # Electron range in pure Copper at 30 kV in micron
    >>> hs.eds.electron_range('Cu', 30.)
    2.8766744984001607

    Notes
    -----
    From Kanaya, K. and S. Okayama (1972). J. Phys. D. Appl. Phys. 5, p43

    See also the textbook of Goldstein et al., Plenum publisher,
    third edition p 72.

    """

    if density == u'auto':
        density = elements_db[
            element][u'Physical_properties'][u'density (g/cm^3)']
    Z = elements_db[element][u'General_properties'][u'Z']
    A = elements_db[element][u'General_properties'][u'atomic_weight']

    return (0.0276 * A / np.power(Z, 0.89) / density *
            np.power(beam_energy, 1.67) * math.cos(math.radians(tilt)))


def take_off_angle(tilt_stage,
                   azimuth_angle,
                   elevation_angle):
    u"""Calculate the take-off-angle (TOA).

    TOA is the angle with which the X-rays leave the surface towards
    the detector.

    Parameters
    ----------
    tilt_stage: float
        The tilt of the stage in degrees. The sample is facing the detector
        when positively tilted.
    azimuth_angle: float
        The azimuth of the detector in degrees. 0 is perpendicular to the tilt
        axis.
    elevation_angle: float
        The elevation of the detector in degrees.

    Returns
    -------
    take_off_angle: float.
        In degrees.

    Examples
    --------
    >>> hs.eds.take_off_angle(tilt_stage=10.,
    >>>                          azimuth_angle=45., elevation_angle=22.)
    28.865971201155283

    Notes
    -----
    Defined by M. Schaffer et al., Ultramicroscopy 107(8), pp 587-597 (2007)

    """

    a = math.radians(90 + tilt_stage)
    b = math.radians(azimuth_angle)
    c = math.radians(elevation_angle)

    return math.degrees(np.arcsin(-math.cos(a) * math.cos(b) * math.cos(c)
                                  + math.sin(a) * math.sin(c)))


def quantification_cliff_lorimer(intensities,
                                 kfactors,
                                 mask=None):
    u"""
    Quantification using Cliff-Lorimer

    Parameters
    ----------
    intensities: numpy.array
        the intensities for each X-ray lines. The first axis should be the
        elements axis.
    kfactors: list of float
        The list of kfactor in same order as intensities eg. kfactors =
        [1, 1.47, 1.72] for ['Al_Ka','Cr_Ka', 'Ni_Ka']
    mask: array of bool
        The mask with the dimension of intensities[0]. If a pixel is True,
        the composition is set to zero.

    Return
    ------
    numpy.array containing the weight fraction with the same
    shape as intensities.
    """
    # Value used as an threshold to prevent using zeros as denominator
    min_intensity = 0.1
    dim = intensities.shape
    if len(dim) > 1:
        dim2 = reduce(lambda x, y: x * y, dim[1:])
        intens = intensities.reshape(dim[0], dim2)
        intens = intens.astype(u'float')
        for i in xrange(dim2):
            index = np.where(intens[:, i] > min_intensity)[0]
            if len(index) > 1:
                ref_index, ref_index2 = index[:2]
                intens[:, i] = _quantification_cliff_lorimer(
                    intens[:, i], kfactors, ref_index, ref_index2)
            else:
                intens[:, i] = np.zeros_like(intens[:, i])
                if len(index) == 1:
                    intens[index[0], i] = 1.
        intens = intens.reshape(dim)
        if mask is not None:
            for i in xrange(dim[0]):
                intens[i][mask] = 0
        return intens
    else:
        # intens = intensities.copy()
        # intens = intens.astype('float')
        index = np.where(intensities > min_intensity)[0]
        if len(index) > 1:
            ref_index, ref_index2 = index[:2]
            intens = _quantification_cliff_lorimer(
                intensities, kfactors, ref_index, ref_index2)
        else:
            intens = np.zeros_like(intensities)
            if len(index) == 1:
                intens[index[0]] = 1.
        return intens


def _quantification_cliff_lorimer(intensities,
                                  kfactors,
                                  ref_index=0,
                                  ref_index2=1):
    u"""
    Quantification using Cliff-Lorimer

    Parameters
    ----------
    intensities: numpy.array
        the intensities for each X-ray lines. The first axis should be the
        elements axis.
    kfactors: list of float
        The list of kfactor in same order as  intensities eg. kfactors =
        [1, 1.47, 1.72] for ['Al_Ka','Cr_Ka', 'Ni_Ka']
    ref_index, ref_index2: int
        index of the elements that will be in the denominator. Should be non
        zeros if possible.

    Return
    ------
    numpy.array containing the weight fraction with the same
    shape as intensities.
    """
    if len(intensities) != len(kfactors):
        raise ValueError(u'The number of kfactors must match the size of the '
                         u'first axis of intensities.')
    ab = np.zeros_like(intensities, dtype=u'float')
    composition = np.ones_like(intensities, dtype=u'float')
    # ab = Ia/Ib / kab

    other_index = range(len(kfactors))
    other_index.pop(ref_index)
    for i in other_index:
        ab[i] = intensities[ref_index] * kfactors[ref_index]  \
            / intensities[i] / kfactors[i]
    # Ca = ab /(1 + ab + ab/ac + ab/ad + ...)
    for i in other_index:
        if i == ref_index2:
            composition[ref_index] += ab[ref_index2]
        else:
            composition[ref_index] += (ab[ref_index2] / ab[i])
    composition[ref_index] = ab[ref_index2] / composition[ref_index]
    # Cb = Ca / ab
    for i in other_index:
        composition[i] = composition[ref_index] / ab[i]
    return composition
