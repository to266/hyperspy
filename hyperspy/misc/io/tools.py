import os
from hyperspy.messages import information


def dump_dictionary(file, dic, string=u'root', node_separator=u'.',
                    value_separator=u' = '):
    for key in dic.keys():
        if isinstance(dic[key], dict):
            dump_dictionary(file, dic[key], string + node_separator + key)
        else:
            file.write(string + node_separator + key + value_separator +
                       unicode(dic[key]) + u'\n')


def append2pathname(filename, to_append):
    u"""Append a string to a path name

    Parameters
    ----------
    filename : str
    to_append : str

    """
    pathname, extension = os.path.splitext(filename)
    return pathname + to_append + extension


def incremental_filename(filename, i=1):
    u"""If a file with the same file name exists, returns a new filename that
    does not exists.

    The new file name is created by appending `-n` (where `n` is an integer)
    to path name

    Parameters
    ----------
    filename : str
    i : int
       The number to be appended.
    """

    if os.path.isfile(filename):
        new_filename = append2pathname(filename, u'-%s' % i)
        if os.path.isfile(new_filename):
            return incremental_filename(filename, i + 1)
        else:
            return new_filename
    else:
        return filename


def ensure_directory(path):
    u"""Check if the path exists and if it does not create the directory"""
    directory = os.path.split(path)[0]
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def overwrite(fname):
    u""" If file exists 'fname', ask for overwriting and return True or False,
    else return True.

    """
    if os.path.isfile(fname):
        message = u"Overwrite '%s' (y/n)?\n" % fname
        try:
            answer = raw_input(message)
            answer = answer.lower()
            while (answer != u'y') and (answer != u'n'):
                print u'Please answer y or n.'
                answer = raw_input(message)
            if answer.lower() == u'y':
                return True
            elif answer.lower() == u'n':
                # print('Operation canceled.')
                return False
        except:
            # We are running in the IPython notebook that does not
            # support raw_input
            information(u"Your terminal does not support raw input. "
                        u"Not overwriting. "
                        u"To overwrite the file use `overwrite=True`")
            return False
    else:
        return True
