u"""Extract reference documentation from the NumPy source tree.

"""

import inspect
import textwrap
import re
import pydoc
from io import StringIO
from warnings import warn
import collections


class Reader(object):

    u"""A line-based string reader.

    """

    def __init__(self, data):
        u"""
        Parameters
        ----------
        data : str
           String with lines separated by '\n'.

        """
        if isinstance(data, list):
            self._str = data
        else:
            self._str = data.split(u'\n')  # store string as list of lines

        self.reset()

    def __getitem__(self, n):
        return self._str[n]

    def reset(self):
        self._l = 0  # current line nr

    def read(self):
        if not self.eof():
            out = self[self._l]
            self._l += 1
            return out
        else:
            return u''

    def seek_next_non_empty_line(self):
        for l in self[self._l:]:
            if l.strip():
                break
            else:
                self._l += 1

    def eof(self):
        return self._l >= len(self._str)

    def read_to_condition(self, condition_func):
        start = self._l
        for line in self[start:]:
            if condition_func(line):
                return self[start:self._l]
            self._l += 1
            if self.eof():
                return self[start:self._l + 1]
        return []

    def read_to_next_empty_line(self):
        self.seek_next_non_empty_line()

        def is_empty(line):
            return not line.strip()
        return self.read_to_condition(is_empty)

    def read_to_next_unindented_line(self):
        def is_unindented(line):
            return (line.strip() and (len(line.lstrip()) == len(line)))
        return self.read_to_condition(is_unindented)

    def peek(self, n=0):
        if self._l + n < len(self._str):
            return self[self._l + n]
        else:
            return u''

    def is_empty(self):
        return not u''.join(self._str).strip()


class NumpyDocString(object):

    def __init__(self, docstring, config={}):
        docstring = textwrap.dedent(docstring).split(u'\n')

        self._doc = Reader(docstring)
        self._parsed_data = {
            u'Signature': u'',
            u'Summary': [u''],
            u'Extended Summary': [],
            u'Parameters': [],
            u'Returns': [],
            u'Raises': [],
            u'Warns': [],
            u'Other Parameters': [],
            u'Attributes': [],
            u'Methods': [],
            u'See Also': [],
            u'Notes': [],
            u'Warnings': [],
            u'References': u'',
            u'Examples': u'',
            u'index': {}
        }

        self._parse()

    def __getitem__(self, key):
        return self._parsed_data[key]

    def __setitem__(self, key, val):
        if key not in self._parsed_data:
            warn(u"Unknown section %s" % key)
        else:
            self._parsed_data[key] = val

    def _is_at_section(self):
        self._doc.seek_next_non_empty_line()

        if self._doc.eof():
            return False

        l1 = self._doc.peek().strip()  # e.g. Parameters

        if l1.startswith(u'.. index::'):
            return True

        l2 = self._doc.peek(1).strip()  # ---------- or ==========
        return l2.startswith(u'-' * len(l1)) or l2.startswith(u'=' * len(l1))

    def _strip(self, doc):
        i = 0
        j = 0
        for i, line in enumerate(doc):
            if line.strip():
                break

        for j, line in enumerate(doc[::-1]):
            if line.strip():
                break

        return doc[i:len(doc) - j]

    def _read_to_next_section(self):
        section = self._doc.read_to_next_empty_line()

        while not self._is_at_section() and not self._doc.eof():
            if not self._doc.peek(-1).strip():  # previous line was empty
                section += [u'']

            section += self._doc.read_to_next_empty_line()

        return section

    def _read_sections(self):
        while not self._doc.eof():
            data = self._read_to_next_section()
            name = data[0].strip()

            if name.startswith(u'..'):  # index section
                yield name, data[1:]
            elif len(data) < 2:
                yield StopIteration
            else:
                yield name, self._strip(data[2:])

    def _parse_param_list(self, content):
        r = Reader(content)
        params = []
        while not r.eof():
            header = r.read().strip()
            if u' : ' in header:
                arg_name, arg_type = header.split(u' : ')[:2]
            else:
                arg_name, arg_type = header, u''

            desc = r.read_to_next_unindented_line()
            desc = dedent_lines(desc)

            params.append((arg_name, arg_type, desc))

        return params

    _name_rgx = re.compile(ur"^\s*(:(?P<role>\w+):`(?P<name>[a-zA-Z0-9_.-]+)`|"
                           ur" (?P<name2>[a-zA-Z0-9_.-]+))\s*", re.X)

    def _parse_see_also(self, content):
        u"""
        func_name : Descriptive text
            continued text
        another_func_name : Descriptive text
        func_name1, func_name2, :meth:`func_name`, func_name3

        """
        items = []

        def parse_item_name(text):
            u"""Match ':role:`name`' or 'name'"""
            m = self._name_rgx.match(text)
            if m:
                g = m.groups()
                if g[1] is None:
                    return g[3], None
                else:
                    return g[2], g[1]
            raise ValueError(u"%s is not a item name" % text)

        def push_item(name, rest):
            if not name:
                return
            name, role = parse_item_name(name)
            items.append((name, list(rest), role))
            del rest[:]

        current_func = None
        rest = []

        for line in content:
            if not line.strip():
                continue

            m = self._name_rgx.match(line)
            if m and line[m.end():].strip().startswith(u':'):
                push_item(current_func, rest)
                current_func, line = line[:m.end()], line[m.end():]
                rest = [line.split(u':', 1)[1].strip()]
                if not rest[0]:
                    rest = []
            elif not line.startswith(u' '):
                push_item(current_func, rest)
                current_func = None
                if u',' in line:
                    for func in line.split(u','):
                        if func.strip():
                            push_item(func, [])
                elif line.strip():
                    current_func = line
            elif current_func is not None:
                rest.append(line.strip())
        push_item(current_func, rest)
        return items

    def _parse_index(self, section, content):
        u"""
        .. index: default
           :refguide: something, else, and more

        """
        def strip_each_in(lst):
            return [s.strip() for s in lst]

        out = {}
        section = section.split(u'::')
        if len(section) > 1:
            out[u'default'] = strip_each_in(section[1].split(u','))[0]
        for line in content:
            line = line.split(u':')
            if len(line) > 2:
                out[line[1]] = strip_each_in(line[2].split(u','))
        return out

    def _parse_summary(self):
        u"""Grab signature (if given) and summary"""
        if self._is_at_section():
            return

        summary = self._doc.read_to_next_empty_line()
        summary_str = u" ".join([s.strip() for s in summary]).strip()
        if re.compile(u'^([\w., ]+=)?\s*[\w\.]+\(.*\)$').match(summary_str):
            self[u'Signature'] = summary_str
            if not self._is_at_section():
                self[u'Summary'] = self._doc.read_to_next_empty_line()
        else:
            self[u'Summary'] = summary

        if not self._is_at_section():
            self[u'Extended Summary'] = self._read_to_next_section()

    def _parse(self):
        self._doc.reset()
        self._parse_summary()

        for (section, content) in self._read_sections():
            if not section.startswith(u'..'):
                section = u' '.join([s.capitalize()
                                   for s in section.split(u' ')])
            if section in (u'Parameters', u'Returns', u'Raises', u'Warns',
                           u'Other Parameters', u'Attributes', u'Methods'):
                self[section] = self._parse_param_list(content)
            elif section.startswith(u'.. index::'):
                self[u'index'] = self._parse_index(section, content)
            elif section == u'See Also':
                self[u'See Also'] = self._parse_see_also(content)
            else:
                self[section] = content

    # string conversion routines

    def _str_header(self, name, symbol=u'-'):
        return [name, len(name) * symbol]

    def _str_indent(self, doc, indent=4):
        out = []
        for line in doc:
            out += [u' ' * indent + line]
        return out

    def _str_signature(self):
        if self[u'Signature']:
            return [self[u'Signature'].replace(u'*', u'\*')] + [u'']
        else:
            return [u'']

    def _str_summary(self):
        if self[u'Summary']:
            return self[u'Summary'] + [u'']
        else:
            return []

    def _str_extended_summary(self):
        if self[u'Extended Summary']:
            return self[u'Extended Summary'] + [u'']
        else:
            return []

    def _str_param_list(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            for param, param_type, desc in self[name]:
                out += [u'%s : %s' % (param, param_type)]
                out += self._str_indent(desc)
            out += [u'']
        return out

    def _str_section(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            out += self[name]
            out += [u'']
        return out

    def _str_see_also(self, func_role):
        if not self[u'See Also']:
            return []
        out = []
        out += self._str_header(u"See Also")
        last_had_desc = True
        for func, desc, role in self[u'See Also']:
            if role:
                link = u':%s:`%s`' % (role, func)
            elif func_role:
                link = u':%s:`%s`' % (func_role, func)
            else:
                link = u"`%s`_" % func
            if desc or last_had_desc:
                out += [u'']
                out += [link]
            else:
                out[-1] += u", %s" % link
            if desc:
                out += self._str_indent([u' '.join(desc)])
                last_had_desc = True
            else:
                last_had_desc = False
        out += [u'']
        return out

    def _str_index(self):
        idx = self[u'index']
        out = []
        out += [u'.. index:: %s' % idx.get(u'default', u'')]
        for section, references in idx.items():
            if section == u'default':
                continue
            out += [u'   :%s: %s' % (section, u', '.join(references))]
        return out

    def __str__(self, func_role=u''):
        out = []
        out += self._str_signature()
        out += self._str_summary()
        out += self._str_extended_summary()
        for param_list in (u'Parameters', u'Returns', u'Other Parameters',
                           u'Raises', u'Warns'):
            out += self._str_param_list(param_list)
        out += self._str_section(u'Warnings')
        out += self._str_see_also(func_role)
        for s in (u'Notes', u'References', u'Examples'):
            out += self._str_section(s)
        for param_list in (u'Attributes', u'Methods'):
            out += self._str_param_list(param_list)
        out += self._str_index()
        return u'\n'.join(out)


def indent(unicode, indent=4):
    indent_str = u' ' * indent
    if unicode is None:
        return indent_str
    lines = unicode.split(u'\n')
    return u'\n'.join(indent_str + l for l in lines)


def dedent_lines(lines):
    u"""Deindent a list of lines maximally"""
    return textwrap.dedent(u"\n".join(lines)).split(u"\n")


def header(text, style=u'-'):
    return text + u'\n' + style * len(text) + u'\n'


class FunctionDoc(NumpyDocString):

    def __init__(self, func, role=u'func', doc=None, config={}):
        self._f = func
        self._role = role  # e.g. "func" or "meth"

        if doc is None:
            if func is None:
                raise ValueError(u"No function or docstring given")
            doc = inspect.getdoc(func) or u''
        NumpyDocString.__init__(self, doc)

        if not self[u'Signature'] and func is not None:
            func, func_name = self.get_func()
            try:
                # try to read signature
                argspec = inspect.getargspec(func)
                argspec = inspect.formatargspec(*argspec)
                argspec = argspec.replace(u'*', u'\*')
                signature = u'%s%s' % (func_name, argspec)
            except TypeError, e:
                signature = u'%s()' % func_name
            self[u'Signature'] = signature

    def get_func(self):
        func_name = getattr(self._f, u'__name__', self.__class__.__name__)
        if inspect.isclass(self._f):
            func = getattr(self._f, u'__call__', self._f.__init__)
        else:
            func = self._f
        return func, func_name

    def __str__(self):
        out = u''

        func, func_name = self.get_func()
        signature = self[u'Signature'].replace(u'*', u'\*')

        roles = {u'func': u'function',
                 u'meth': u'method'}

        if self._role:
            if self._role not in roles:
                print u"Warning: invalid role %s" % self._role
            out += u'.. %s:: %s\n    \n\n' % (roles.get(self._role, u''),
                                             func_name)

        out += super(FunctionDoc, self).__str__(func_role=self._role)
        return out


class ClassDoc(NumpyDocString):

    extra_public_methods = [u'__call__']

    def __init__(self, cls, doc=None, modulename=u'', func_doc=FunctionDoc,
                 config={}):
        if not inspect.isclass(cls) and cls is not None:
            raise ValueError(u"Expected a class or None, but got %r" % cls)
        self._cls = cls

        if modulename and not modulename.endswith(u'.'):
            modulename += u'.'
        self._mod = modulename

        if doc is None:
            if cls is None:
                raise ValueError(u"No class or documentation string given")
            doc = pydoc.getdoc(cls)

        NumpyDocString.__init__(self, doc)

        if config.get(u'show_class_members', True):
            if not self[u'Methods']:
                self[u'Methods'] = [(name, u'', u'')
                                   for name in sorted(self.methods)]
            if not self[u'Attributes']:
                self[u'Attributes'] = [(name, u'', u'')
                                      for name in sorted(self.properties)]

    @property
    def methods(self):
        if self._cls is None:
            return []
        return [name for name, func in inspect.getmembers(self._cls)
                if ((not name.startswith(u'_')
                     or name in self.extra_public_methods)
                    and isinstance(func, collections.Callable))]

    @property
    def properties(self):
        if self._cls is None:
            return []
        return [name for name, func in inspect.getmembers(self._cls)
                if not name.startswith(u'_') and func is None]
