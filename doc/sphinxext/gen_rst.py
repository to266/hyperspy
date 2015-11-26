# This is a modified version of matplotlib's file of the same name
# The matplotlib license of choice applies to this file


u"""
generate the rst files for the examples by iterating over the examples
"""
import os
import glob

import os
import re
import sys
fileList = []


def out_of_date(original, derived):
    u"""
    Returns True if derivative is out-of-date wrt original,
    both of which are full file paths.

    TODO: this check isn't adequate in some cases.  Eg, if we discover
    a bug when building the examples, the original and derived will be
    unchanged but we still want to force a rebuild.
    """
    return (not os.path.exists(derived) or
            os.stat(derived).st_mtime < os.stat(original).st_mtime)

noplot_regex = re.compile(ur"#\s*-\*-\s*noplot\s*-\*-")


def generate_example_rst(app):
    rootdir = os.path.join(app.builder.srcdir, u'hspy_examples')
    exampledir = os.path.join(app.builder.srcdir, u'examples')
    if not os.path.exists(exampledir):
        os.makedirs(exampledir)

    datad = {}
    for root, subFolders, files in os.walk(rootdir):
        for fname in files:
            if (fname.startswith(u'.') or fname.startswith(u'#')
                    or fname.startswith(u'_') or not fname.endswith(u'.py')):
                continue

            fullpath = os.path.join(root, fname)
            contents = file(fullpath).read()
            # indent
            relpath = os.path.split(root)[-1]
            datad.setdefault(relpath, []).append((fullpath, fname, contents))

    subdirs = sorted(datad.keys())

    fhindex = file(os.path.join(exampledir, u'index.rst'), u'w')
    fhindex.write(u"""\
.. _examples-index:

####################
HyperSpy Examples
####################

.. htmlonly::

    :Release: |version|
    :Date: |today|

.. toctree::
    :maxdepth: 2

""")

    for subdir in subdirs:
        rstdir = os.path.join(exampledir, subdir)
        if not os.path.exists(rstdir):
            os.makedirs(rstdir)

        outputdir = os.path.join(app.builder.outdir, u'examples')
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        outputdir = os.path.join(outputdir, subdir)
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        subdirIndexFile = os.path.join(rstdir, u'index.rst')
        fhsubdirIndex = file(subdirIndexFile, u'w')
        fhindex.write(u'    %s/index.rst\n\n' % subdir)

        fhsubdirIndex.write(u"""\
.. _%s-examples-index:

##############################################
%s Examples
##############################################

.. htmlonly::

    :Release: |version|
    :Date: |today|

.. toctree::
    :maxdepth: 1

""" % (subdir, subdir))

        sys.stdout.write(subdir + u", ")
        sys.stdout.flush()

        data = sorted(datad[subdir])

        for fullpath, fname, contents in data:
            basename, ext = os.path.splitext(fname)
            outputfile = os.path.join(outputdir, fname)
            #thumbfile = os.path.join(thumb_dir, '%s.png'%basename)
            # print '    static_dir=%s, basename=%s, fullpath=%s, fname=%s,
            # thumb_dir=%s, thumbfile=%s'%(static_dir, basename, fullpath,
            # fname, thumb_dir, thumbfile)

            rstfile = u'%s.rst' % basename
            outrstfile = os.path.join(rstdir, rstfile)

            fhsubdirIndex.write(
                u'    %s <%s>\n' %
                (os.path.basename(basename), rstfile))

            if not out_of_date(fullpath, outrstfile):
                continue

            fh = file(outrstfile, u'w')
            fh.write(u'.. _%s-%s:\n\n' % (subdir, basename))
            title = u'%s example code: %s' % (subdir, fname)
            #title = '<img src=%s> %s example code: %s'%(thumbfile, subdir, fname)

            fh.write(title + u'\n')
            fh.write(u'=' * len(title) + u'\n\n')

            do_plot = (subdir in (u'api',
                                  u'pylab_examples',
                                  u'units',
                                  u'mplot3d',
                                  u'axes_grid',
                                  ) and
                       not noplot_regex.search(contents))

            if do_plot:
                fh.write(u"\n\n.. plot:: %s\n\n::\n\n" % fullpath)
            else:
                fh.write(u"[`source code <%s>`_]\n\n::\n\n" % fname)
                fhstatic = file(outputfile, u'w')
                fhstatic.write(contents)
                fhstatic.close()

            # indent the contents
            contents = u'\n'.join([u'    %s' % row.rstrip()
                                 for row in contents.split(u'\n')])
            fh.write(contents)

            fh.write(
                u'\n\nKeywords: hyperspy, example, codex (see :ref:`how-to-search-examples`)')
            fh.close()

        fhsubdirIndex.close()

    fhindex.close()

    print


def setup(app):
    app.connect(u'builder-inited', generate_example_rst)
