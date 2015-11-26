#!/usr/bin/python
u"""Run nosetests after setting ETS toolkit to "null"."""

if __name__ == u'__main__':
    import sys
    from nose import run_exit
    from traits.etsconfig.api import ETSConfig

    ETSConfig.toolkit = u"null"
    sys.exit(run_exit())
