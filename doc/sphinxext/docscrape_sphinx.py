import re
import inspect
import textwrap
import pydoc
import sphinx
from docscrape import NumpyDocString, FunctionDoc, ClassDoc
import collections


class SphinxDocString(NumpyDocString):

    def __init__(self, docstring, config={}):
        self.use_plots = config.get(u'use_plots', False)
        NumpyDocString.__init__(self, docstring, config=config)

    # string conversion routines
    def _str_header(self, name, symbol=u'`'):
        return [u'.. rubric:: ' + name, u'']

    def _str_field_list(self, name):
        return [u':' + name + u':']

    def _str_indent(self, doc, indent=4):
        out = []
        for line in doc:
            out += [u' ' * indent + line]
        return out

    def _str_signature(self):
        return [u'']
        if self[u'Signature']:
            return [u'``%s``' % self[u'Signature']] + [u'']
        else:
            return [u'']

    def _str_summary(self):
        return self[u'Summary'] + [u'']

    def _str_extended_summary(self):
        return self[u'Extended Summary'] + [u'']

    def _str_param_list(self, name):
        out = []
        if self[name]:
            out += self._str_field_list(name)
            out += [u'']
            for param, param_type, desc in self[name]:
                out += self._str_indent([u'**%s** : %s' % (param.strip(),
                                                          param_type)])
                out += [u'']
                out += self._str_indent(desc, 8)
                out += [u'']
        return out

    @property
    def _obj(self):
        if hasattr(self, u'_cls'):
            return self._cls
        elif hasattr(self, u'_f'):
            return self._f
        return None

    def _str_member_list(self, name):
        u"""
        Generate a member listing, autosummary:: table where possible,
        and a table where not.

        """
        out = []
        if self[name]:
            out += [u'.. rubric:: %s' % name, u'']
            prefix = getattr(self, u'_name', u'')

            if prefix:
                prefix = u'~%s.' % prefix

            autosum = []
            others = []
            for param, param_type, desc in self[name]:
                param = param.strip()
                if not self._obj or hasattr(self._obj, param):
                    autosum += [u"   %s%s" % (prefix, param)]
                else:
                    others.append((param, param_type, desc))

            if autosum:
                out += [u'.. autosummary::', u'   :toctree:', u'']
                out += autosum

            if others:
                maxlen_0 = max([len(x[0]) for x in others])
                maxlen_1 = max([len(x[1]) for x in others])
                hdr = u"=" * maxlen_0 + u"  " + u"=" * maxlen_1 + u"  " + u"=" * 10
                fmt = u'%%%ds  %%%ds  ' % (maxlen_0, maxlen_1)
                n_indent = maxlen_0 + maxlen_1 + 4
                out += [hdr]
                for param, param_type, desc in others:
                    out += [fmt % (param.strip(), param_type)]
                    out += self._str_indent(desc, n_indent)
                out += [hdr]
            out += [u'']
        return out

    def _str_section(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            out += [u'']
            content = textwrap.dedent(u"\n".join(self[name])).split(u"\n")
            out += content
            out += [u'']
        return out

    def _str_see_also(self, func_role):
        out = []
        if self[u'See Also']:
            see_also = super(SphinxDocString, self)._str_see_also(func_role)
            out = [u'.. seealso::', u'']
            out += self._str_indent(see_also[2:])
        return out

    def _str_warnings(self):
        out = []
        if self[u'Warnings']:
            out = [u'.. warning::', u'']
            out += self._str_indent(self[u'Warnings'])
        return out

    def _str_index(self):
        idx = self[u'index']
        out = []
        if len(idx) == 0:
            return out

        out += [u'.. index:: %s' % idx.get(u'default', u'')]
        for section, references in idx.items():
            if section == u'default':
                continue
            elif section == u'refguide':
                out += [u'   single: %s' % (u', '.join(references))]
            else:
                out += [u'   %s: %s' % (section, u','.join(references))]
        return out

    def _str_references(self):
        out = []
        if self[u'References']:
            out += self._str_header(u'References')
            if isinstance(self[u'References'], unicode):
                self[u'References'] = [self[u'References']]
            out.extend(self[u'References'])
            out += [u'']
            # Latex collects all references to a separate bibliography,
            # so we need to insert links to it
            if sphinx.__version__ >= u"0.6":
                out += [u'.. only:: latex', u'']
            else:
                out += [u'.. latexonly::', u'']
            items = []
            for line in self[u'References']:
                m = re.match(ur'.. \[([a-z0-9._-]+)\]', line, re.I)
                if m:
                    items.append(m.group(1))
            out += [u'   ' + u", ".join([u"[%s]_" % item for item in items]), u'']
        return out

    def _str_examples(self):
        examples_str = u"\n".join(self[u'Examples'])

        if (self.use_plots and u'import matplotlib' in examples_str
                and u'plot::' not in examples_str):
            out = []
            out += self._str_header(u'Examples')
            out += [u'.. plot::', u'']
            out += self._str_indent(self[u'Examples'])
            out += [u'']
            return out
        else:
            return self._str_section(u'Examples')

    def __str__(self, indent=0, func_role=u"obj"):
        out = []
        out += self._str_signature()
        out += self._str_index() + [u'']
        out += self._str_summary()
        out += self._str_extended_summary()
        for param_list in (u'Parameters', u'Returns', u'Other Parameters',
                           u'Raises', u'Warns'):
            out += self._str_param_list(param_list)
        out += self._str_warnings()
        out += self._str_see_also(func_role)
        out += self._str_section(u'Notes')
        out += self._str_references()
        out += self._str_examples()
        for param_list in (u'Attributes', u'Methods'):
            out += self._str_member_list(param_list)
        out = self._str_indent(out, indent)
        return u'\n'.join(out)


class SphinxFunctionDoc(SphinxDocString, FunctionDoc):

    def __init__(self, obj, doc=None, config={}):
        self.use_plots = config.get(u'use_plots', False)
        FunctionDoc.__init__(self, obj, doc=doc, config=config)


class SphinxClassDoc(SphinxDocString, ClassDoc):

    def __init__(self, obj, doc=None, func_doc=None, config={}):
        self.use_plots = config.get(u'use_plots', False)
        ClassDoc.__init__(self, obj, doc=doc, func_doc=None, config=config)


class SphinxObjDoc(SphinxDocString):

    def __init__(self, obj, doc=None, config={}):
        self._f = obj
        SphinxDocString.__init__(self, doc, config=config)


def get_doc_object(obj, what=None, doc=None, config={}):
    if what is None:
        if inspect.isclass(obj):
            what = u'class'
        elif inspect.ismodule(obj):
            what = u'module'
        elif isinstance(obj, collections.Callable):
            what = u'function'
        else:
            what = u'object'
    if what == u'class':
        return SphinxClassDoc(obj, func_doc=SphinxFunctionDoc, doc=doc,
                              config=config)
    elif what in (u'function', u'method'):
        return SphinxFunctionDoc(obj, doc=doc, config=config)
    else:
        if doc is None:
            doc = pydoc.getdoc(obj)
        return SphinxObjDoc(obj, doc, config=config)
