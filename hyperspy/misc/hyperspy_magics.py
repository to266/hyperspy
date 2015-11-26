from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring
import warnings

from hyperspy.defaults_parser import preferences


class HyperspyMagics(Magics):

    @line_magic
    @magic_arguments()
    @argument(u'-r', u'--replace', action=u'store_true', default=None,
              help=u"""After running the the magic as usual, overwrites the current input cell with just executed
              code that can be run directly without magic"""
              )
    @argument(u'toolkit', nargs=u'?', default=None,
              help=u"""Name of the matplotlib backend to use.  If given, the corresponding matplotlib backend
              is used, otherwise it will be the HyperSpy's default.  Available toolkits: {qt4, wx, None, gtk,
              tk}. Note that gtk and tk toolkits are not fully supported
              """
              )
    def hyperspy(self, line):
        u"""
        Load HyperSpy, numpy and matplotlib to work interactively.

        %hyperspy runs the following commands in various cases:

        >>> # if toolkit is "None" only
        >>> import matplotlib
        >>> matplotlib.use('Agg')

        >>> # if toolkit is "qt4" only
        >>> import os
        >>> os.environ['QT_API'] = 'pyqt'

        >>> # if toolkit is not "None"
        >>> %matplotlib [toolkit]

        >>> # run in all cases
        >>> import numpy as np
        >>> import hyperspy.api as hs
        >>> import matplotlib.pyplot as plt

        """
        sh = self.shell

        gui = False
        args = parse_argstring(self.hyperspy, line)
        overwrite = not args.replace is None
        toolkit = args.toolkit
        if toolkit is None:
            toolkit = preferences.General.default_toolkit

        if toolkit not in [u'qt4', u'gtk', u'wx', u'tk', u'None']:
            raise ValueError(u"The '%s' toolkit is not supported.\n" % toolkit +
                             u"Supported toolkits: {qt4, gtk, wx, tk, None}")

        mpl_code = u""
        if toolkit == u"None":
            mpl_code = (u"import matplotlib\n"
                        u"matplotlib.use('Agg')\n")
        elif toolkit == u'qt4':
            gui = True
            mpl_code = (u"import os\n"
                        u"os.environ['QT_API'] = 'pyqt'\n")
        else:
            gui = True

        exec(mpl_code, sh.user_ns)
        if gui:
            sh.enable_matplotlib(toolkit)
        first_import_part = (u"import numpy as np\n"
                             u"import hyperspy.api as hs\n"
                             u"import matplotlib.pyplot as plt\n")
        exec(first_import_part, sh.user_ns)

        if preferences.General.import_hspy:
            second_import_part = u"from hyperspy.hspy import *\n"
            warnings.warn(
                u"Importing everything from ``hyperspy.hspy`` will be removed in "
                u"HyperSpy 0.9. Please use the new API imported as ``hs`` "
                u"instead. See the "
                u"`Getting started` section of the User Guide for details.",
                UserWarning)
            exec(second_import_part, sh.user_ns)
            first_import_part += second_import_part

        header = u"\nHyperSpy imported!\nThe following commands were just executed:\n"
        header += u"---------------\n"
        ans = mpl_code
        if gui:
            ans += u"%matplotlib " + toolkit + u"\n"

        ans += first_import_part
        print header + ans
        if overwrite:
            sh.set_next_input(
                u"# %hyperspy -r " +
                toolkit +
                u"\n" +
                ans +
                u"\n\n",
                replace=True)

HyperspyMagics = magics_class(HyperspyMagics)