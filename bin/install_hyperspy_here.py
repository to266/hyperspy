import _winreg
import sys
import os


def install_hyperspy_here(hspy_qtconsole_logo_path, hspy_notebook_logo_path):
    # First uninstall old HyperSpy context menu entries
    try:
        if sys.getwindowsversion()[0] < 6.:  # Older than Windows Vista:
            _winreg.DeleteKey(
                _winreg.HKEY_LOCAL_MACHINE,
                ur'Software\Classes\Folder\Shell\HyperSpy_here\Command')
            _winreg.DeleteKey(
                _winreg.HKEY_LOCAL_MACHINE,
                ur'Software\Classes\Folder\Shell\HyperSpy_here')
        else:  # Vista or newer
            _winreg.DeleteKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\shell\hyperspy_here\Command')
            _winreg.DeleteKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\shell\hyperspy_here')
            _winreg.DeleteKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\Background\shell\hyperspy_here\Command')
            _winreg.DeleteKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\Background\shell\hyperspy_here')
        uninstall_hyperspy_here()
    except:
        # The old entries were not present, so we do nothing
        pass

    # Install the context menu entries for the qtconsole and the IPython
    # notebook
    logos = {
        u'qtconsole': hspy_qtconsole_logo_path,
        u'notebook': hspy_notebook_logo_path}
    for env in (u'qtconsole', u'notebook'):
        script = os.path.join(sys.prefix, u'Scripts', u"hyperspy_%s.bat" % env)
        if sys.getwindowsversion()[0] < 6.:  # Before Windows Vista
            key = _winreg.CreateKey(
                _winreg.HKEY_LOCAL_MACHINE,
                ur'Software\Classes\Folder\Shell\HyperSpy_%s_here' %
                env)
            _winreg.SetValueEx(
                key,
                u"",
                0,
                _winreg.REG_SZ,
                u"HyperSpy %s here" %
                env)
            key.Close()
            key = _winreg.CreateKey(
                _winreg.HKEY_LOCAL_MACHINE,
                ur'Software\Classes\Folder\Shell\HyperSpy_%s_here\Command' %
                env)
            _winreg.SetValueEx(
                key,
                u"",
                0,
                _winreg.REG_EXPAND_SZ,
                script +
                u" \"%L\"")
            key.Close()
        else:  # Windows Vista and above
            key = _winreg.CreateKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\shell\hyperspy_%s_here' %
                env)
            _winreg.SetValueEx(
                key,
                u"",
                0,
                _winreg.REG_SZ,
                u"HyperSpy %s here" %
                env)
            _winreg.SetValueEx(
                key,
                u'Icon',
                0,
                _winreg.REG_SZ,
                logos[env]
            )
            key.Close()
            key = _winreg.CreateKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\shell\hyperspy_%s_here\Command' %
                env)
            _winreg.SetValueEx(
                key,
                u"",
                0,
                _winreg.REG_EXPAND_SZ,
                script +
                u" \"%L\"")
            key.Close()
            key = _winreg.CreateKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\Background\shell\hyperspy_%s_here' %
                env)
            _winreg.SetValueEx(
                key,
                u"",
                0,
                _winreg.REG_SZ,
                u"HyperSpy %s Here" %
                env)
            _winreg.SetValueEx(
                key,
                u'Icon',
                0,
                _winreg.REG_SZ,
                logos[env]
            )
            key.Close()
            key = _winreg.CreateKey(
                _winreg.HKEY_CLASSES_ROOT,
                ur'Directory\Background\shell\hyperspy_%s_here\Command' %
                env)
            _winreg.SetValueEx(key, u"", 0, _winreg.REG_EXPAND_SZ, script)
            key.Close()

    print u"HyperSpy here correctly installed"

if __name__ == u"__main__":
    import hyperspy
    hyperspy_install_path = os.path.dirname(hyperspy.__file__)
    logo_path = os.path.expandvars(os.path.join(hyperspy_install_path,
                                   u'data'))
    hspy_qt_logo_path = os.path.join(logo_path,
                                     u'hyperspy_qtconsole_logo.ico')
    hspy_nb_logo_path = os.path.join(logo_path,
                                     u'hyperspy_notebook_logo.ico')
    install_hyperspy_here(hspy_qt_logo_path, hspy_nb_logo_path)
