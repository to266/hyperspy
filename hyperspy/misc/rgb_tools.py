import numpy as np

rgba8 = np.dtype({u'names': [u'R', u'G', u'B', u'A'],
                  u'formats': [u'u1', u'u1', u'u1', u'u1']})
rgb8 = np.dtype({u'names': [u'R', u'G', u'B'],
                 u'formats': [u'u1', u'u1', u'u1']})

rgba16 = np.dtype({u'names': [u'R', u'G', u'B', u'A'],
                   u'formats': [u'u2', u'u2', u'u2', u'u2']})
rgb16 = np.dtype({u'names': [u'R', u'G', u'B'],
                  u'formats': [u'u2', u'u2', u'u2']})
rgb_dtypes = {
    u'rgb8': rgb8,
    u'rgb16': rgb16,
    u'rgba8': rgba8,
    u'rgba16': rgba16}


def is_rgba(array):
    if array.dtype in (rgba8, rgba16):
        return True
    else:
        return False


def is_rgb(array):
    if array.dtype in (rgb8, rgb16):
        return True
    else:
        return False


def is_rgbx(array):
    if is_rgb(array) or is_rgba(array):
        return True
    else:
        return False


def rgbx2regular_array(data, plot_friendly=False):
    u"""Transforms a RGBx array into a standard one

    Parameters
    ----------
    data : numpy array of RGBx dtype
    plot_friendly : bool
        If True change the dtype to float when dtype is not uint8 and
        normalize the array so that it is ready to be plotted by matplotlib.

    """
    # Make sure that the data is contiguous
    if data.flags[u'C_CONTIGUOUS'] is False:
        if np.ma.is_masked(data):
            data = data.copy(order=u'C')
        else:
            data = np.ascontiguousarray(data)
    if is_rgba(data) is True:
        dt = data.dtype.fields[u'B'][0]
        data = data.view((dt, 4))
    elif is_rgb(data) is True:
        dt = data.dtype.fields[u'B'][0]
        data = data.view((dt, 3))
    else:
        return data
    if plot_friendly is True and data.dtype == np.dtype(u"uint16"):
        data = data.astype(u"float")
        data /= 2 ** 16 - 1
    return data


def regular_array2rgbx(data):
    # Make sure that the data is contiguous
    if data.flags[u'C_CONTIGUOUS'] is False:
        if np.ma.is_masked(data):
            data = data.copy(order=u'C')
        else:
            data = np.ascontiguousarray(data)
    if data.shape[-1] == 3:
        names = rgb8.names
    elif data.shape[-1] == 4:
        names = rgba8.names
    else:
        raise ValueError(u"The last dimension size of the array must be 3 or 4")
    if data.dtype in (np.dtype(u"u1"), np.dtype(u"u2")):
        formats = [data.dtype] * len(names)
    else:
        raise ValueError(u"The data dtype must be uint16 or uint8")
    return data.view(np.dtype({u"names": names,
                               u"formats": formats})).reshape(data.shape[:-1])
