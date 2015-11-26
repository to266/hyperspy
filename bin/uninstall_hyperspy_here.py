import _winreg
import sys


def uninstall_hyperspy_here():
    for env in (u'qtconsole', u'notebook'):
        try:
            if sys.getwindowsversion()[0] < 6.:  # Older than Windows Vista:
                _winreg.DeleteKey(
                    _winreg.HKEY_LOCAL_MACHINE,
                    ur'Software\Classes\Folder\Shell\HyperSpy_%s_here\Command' %
                    env)
                _winreg.DeleteKey(
                    _winreg.HKEY_LOCAL_MACHINE,
                    ur'Software\Classes\Folder\Shell\HyperSpy_%s_here' %
                    env)
            else:  # Vista or newer
                _winreg.DeleteKey(
                    _winreg.HKEY_CLASSES_ROOT,
                    ur'Directory\shell\hyperspy_%s_here\Command' %
                    env)
                _winreg.DeleteKey(
                    _winreg.HKEY_CLASSES_ROOT,
                    ur'Directory\shell\hyperspy_%s_here' %
                    env)
                _winreg.DeleteKey(
                    _winreg.HKEY_CLASSES_ROOT,
                    ur'Directory\Background\shell\hyperspy_%s_here\Command' %
                    env)
                _winreg.DeleteKey(
                    _winreg.HKEY_CLASSES_ROOT,
                    ur'Directory\Background\shell\hyperspy_%s_here' %
                    env)
            print (u"HyperSpy %s here correctly uninstalled" % env)
        except:
            print (u"Failed to uninstall HyperSpy %s here" % env)

if __name__ == u"__main__":
    uninstall_hyperspy_here()
