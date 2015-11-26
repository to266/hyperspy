#!/usr/bin/env python
u"""Script to commit the doc build outputs into the github-pages repo.

Use:

  gh-pages.py [tag]

If no tag is given, the current output of 'git describe' is used.  If given,
that is how the resulting directory will be named.

In practice, you should use either actual clean tags from a current build or
something like 'current' as a stable URL for the most current version of the """

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import os
import shutil
import sys
from os import chdir as cd
from os.path import join as pjoin

from subprocess import Popen, PIPE, CalledProcessError, check_call

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

pages_dir = u'gh-pages'
html_dir = u'_build/html'
pdf_dir = u'_build/latex'
pages_repo = u'git@github.com:hyperspy/hyperspy-doc.git'

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------


def sh(cmd):
    u"""Execute command in a subshell, return status code."""
    return check_call(cmd, shell=True)


def sh2(cmd):
    u"""Execute command in a subshell, return stdout.

    Stderr is unbuffered from the subshell.x"""
    p = Popen(cmd, stdout=PIPE, shell=True)
    out = p.communicate()[0]
    retcode = p.returncode
    if retcode:
        raise CalledProcessError(retcode, cmd)
    else:
        return out.rstrip()


def sh3(cmd):
    u"""Execute command in a subshell, return stdout, stderr

    If anything appears in stderr, print it out to sys.stderr"""
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    retcode = p.returncode
    if retcode:
        raise CalledProcessError(retcode, cmd)
    else:
        return out.rstrip(), err.rstrip()


def init_repo(path):
    u"""clone the gh-pages repo if we haven't already."""
    sh(u"git clone %s %s" % (pages_repo, path))
    here = os.getcwdu()
    cd(path)
    sh(u'git checkout gh-pages')
    cd(here)

#-----------------------------------------------------------------------------
# Script starts
#-----------------------------------------------------------------------------
if __name__ == u'__main__':
    sh(u'./generate_api_doc.sh')
    # The tag can be given as a positional argument
    try:
        tag = sys.argv[1]
    except IndexError:
        tag = u"dev"

    startdir = os.getcwdu()
    if not os.path.exists(pages_dir):
        # init the repo
        init_repo(pages_dir)
    else:
        # ensure up-to-date before operating
        cd(pages_dir)
        sh(u'git checkout gh-pages')
        sh(u'git pull')
        cd(startdir)

    dest = pjoin(pages_dir, tag)

    # don't `make html` here, because gh-pages already depends on html in Makefile
    # sh('make html')
    if tag != u'dev':
        # only build pdf for non-dev targets
        #sh2('make pdf')
        pass

    # This is pretty unforgiving: we unconditionally nuke the destination
    # directory, and then copy the html tree in there
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(html_dir, dest)
    if tag != u'dev':
        #shutil.copy(pjoin(pdf_dir, 'ipython.pdf'), pjoin(dest, 'ipython.pdf'))
        pass

    try:
        cd(pages_dir)
        branch = sh2(u'git rev-parse --abbrev-ref HEAD').strip()
        if branch != u'gh-pages':
            e = u'On %r, git branch is %r, MUST be "gh-pages"' % (pages_dir,
                                                                 branch)
            raise RuntimeError(e)

        sh(u'git add -A %s' % tag)
        sh(u'git commit -m"Updated doc release: %s"' % tag)
        print
        print u'Most recent 3 commits:'
        sys.stdout.flush()
        sh(u'git --no-pager log --oneline HEAD~3..')
    finally:
        cd(startdir)

    print
    print u'Now verify the build in: %r' % dest
    print u"If everything looks good, 'git push'"
