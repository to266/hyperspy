# -*- coding: utf-8 -*-
# Copyright 2007-2011 The HyperSpy developers
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


from __future__ import with_statement
from distutils.core import setup

import distutils.dir_util

import os
import subprocess
import sys
import fileinput

import hyperspy.Release as Release
from io import open
# clean the build directory so we aren't mixing Windows and Linux
# installations carelessly.
if os.path.exists(u'build'):
    distutils.dir_util.remove_tree(u'build')

install_req = [u'scipy',
               u'ipython (>= 2.0)',
               u'matplotlib (>= 1.2)',
               u'numpy',
               u'traits',
               u'traitsui',
               u'sympy']


def are_we_building4windows():
    for arg in sys.argv:
        if u'wininst' in arg:
            return True

scripts = [u'bin/hyperspy', ]

if are_we_building4windows() or os.name in [u'nt', u'dos']:
    # In the Windows command prompt we can't execute Python scripts
    # without a .py extension. A solution is to create batch files
    # that runs the different scripts.
    # (code adapted from scitools)
    scripts.extend((u'bin/win_post_installation.py',
                    u'bin/install_hyperspy_here.py',
                    u'bin/uninstall_hyperspy_here.py'))
    batch_files = []
    for script in scripts:
        batch_file = os.path.splitext(script)[0] + u'.bat'
        f = open(batch_file, u"w")
        f.write(u'set path=%~dp0;%~dp0\..\;%PATH%\n')
        f.write(u'python "%%~dp0\%s" %%*\n' % os.path.split(script)[1])
        f.close()
        batch_files.append(batch_file)
        if script in (u'bin/hyperspy'):
            for env in (u'qtconsole', u'notebook'):
                batch_file = os.path.splitext(script)[0] + u'_%s' % env + u'.bat'
                f = open(batch_file, u"w")
                f.write(u'set path=%~dp0;%~dp0\..\;%PATH%\n')
                f.write(u'cd %1\n')
                if env == u"qtconsole":
                    f.write(u'start pythonw "%%~dp0\%s " %s \n' % (
                        os.path.split(script)[1], env))
                else:
                    f.write(u'python "%%~dp0\%s" %s \n' %
                            (os.path.split(script)[1], env))

                batch_files.append(batch_file)
    scripts.extend(batch_files)


class update_version_when_dev(object):

    def __enter__(self):
        self.release_version = Release.version

        # Get the hash from the git repository if available
        self.restore_version = False
        git_master_path = u".git/refs/heads/master"
        if u"+dev" in self.release_version and \
                os.path.isfile(git_master_path):
            try:
                p = subprocess.Popen([u"git", u"describe",
                                      u"--tags", u"--dirty", u"--always"],
                                     stdout=subprocess.PIPE)
                stdout = p.communicate()[0]
                if p.returncode != 0:
                    raise EnvironmentError
                else:
                    version = stdout[1:].strip().decode()
                    if unicode(self.release_version[:-4] + u'-') in version:
                        version = version.replace(
                            self.release_version[:-4] + u'-',
                            self.release_version[:-4] + u'+git')
                    self.version = version
            except EnvironmentError:
                # Git is not available, but the .git directory exists
                # Therefore we can get just the master hash
                with open(git_master_path) as f:
                    masterhash = f.readline()
                self.version = self.release_version.replace(
                    u"+dev", u"+git-%s" % masterhash[:7])
            for line in fileinput.FileInput(u"hyperspy/Release.py",
                                            inplace=1):
                if line.startswith(u'version = '):
                    print u"version = \"%s\"" % self.version
                else:
                    print line,
            self.restore_version = True
        else:
            self.version = self.release_version
        return self.version

    def __exit__(self, type, value, traceback):
        if self.restore_version is True:
            for line in fileinput.FileInput(u"hyperspy/Release.py",
                                            inplace=1):
                if line.startswith(u'version = '):
                    print u"version = \"%s\"" % self.release_version
                else:
                    print line,


with update_version_when_dev() as version:
    setup(
        name=u"hyperspy",
        package_dir={u'hyperspy': u'hyperspy'},
        version=version,
        packages=[u'hyperspy',
                  u'hyperspy._components',
                  u'hyperspy.datasets',
                  u'hyperspy.io_plugins',
                  u'hyperspy.docstrings',
                  u'hyperspy.drawing',
                  u'hyperspy.drawing._markers',
                  u'hyperspy.learn',
                  u'hyperspy._signals',
                  u'hyperspy.gui',
                  u'hyperspy.utils',
                  u'hyperspy.tests',
                  u'hyperspy.tests.axes',
                  u'hyperspy.tests.component',
                  u'hyperspy.tests.drawing',
                  u'hyperspy.tests.io',
                  u'hyperspy.tests.model',
                  u'hyperspy.tests.mva',
                  u'hyperspy.tests.signal',
                  u'hyperspy.tests.utils',
                  u'hyperspy.tests.misc',
                  u'hyperspy.models',
                  u'hyperspy.misc',
                  u'hyperspy.misc.eels',
                  u'hyperspy.misc.eds',
                  u'hyperspy.misc.io',
                  u'hyperspy.misc.machine_learning',
                  u'hyperspy.external',
                  u'hyperspy.external.mpfit',
                  u'hyperspy.external.mpfit.tests',
                  u'hyperspy.external.astroML',
                  ],
        requires=install_req,
        scripts=scripts,
        package_data={
            u'hyperspy':
            [u'bin/*.py',
             u'ipython_profile/*',
             u'data/*.ico',
             u'misc/eds/example_signals/*.hdf5',
             u'tests/io/dm_stackbuilder_plugin/test_stackbuilder_imagestack.dm3',
             u'tests/io/dm3_1D_data/*.dm3',
             u'tests/io/dm3_2D_data/*.dm3',
             u'tests/io/dm3_3D_data/*.dm3',
             u'tests/io/dm4_1D_data/*.dm4',
             u'tests/io/dm4_2D_data/*.dm4',
             u'tests/io/dm4_3D_data/*.dm4',
             u'tests/io/msa_files/*.msa',
             u'tests/io/hdf5_files/*.hdf5',
             u'tests/io/tiff_files/*.tif',
             u'tests/io/npy_files/*.npy',
             u'tests/drawing/*.ipynb',
             ],
        },
        author=Release.authors[u'all'][0],
        author_email=Release.authors[u'all'][1],
        maintainer=u'Francisco de la Peña',
        maintainer_email=u'fjd29@cam.ac.uk',
        description=Release.description,
        long_description=open(u'README.rst').read(),
        license=Release.license,
        platforms=Release.platforms,
        url=Release.url,
        #~ test_suite = 'nose.collector',
        keywords=Release.keywords,
        classifiers=[
            u"Programming Language :: Python :: 2.7",
            u"Development Status :: 4 - Beta",
            u"Environment :: Console",
            u"Intended Audience :: Science/Research",
            u"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            u"Natural Language :: English",
            u"Operating System :: OS Independent",
            u"Topic :: Scientific/Engineering",
            u"Topic :: Scientific/Engineering :: Physics",
        ],
    )
