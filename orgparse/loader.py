# Import README.rst using cog
# [[[cog
# from cog import out
# out('"""\n{0}\n"""'.format(open('../README.rst').read()))
# ]]]
"""
===========================================================
  orgparse - Python module for reading Emacs org-mode files
===========================================================


* `Documentation (Read the Docs) <https://orgparse.readthedocs.org>`_
* `Repository (at GitHub) <https://github.com/karlicoss/orgparse>`_
* `PyPI <https://pypi.python.org/pypi/orgparse>`_
* `Travis CI <https://travis-ci.org/karlicoss/orgparse>`_  |build-status|

.. |build-status|
   image:: https://travis-ci.org/karlicoss/orgparse.svg?branch=master
   :target: https://travis-ci.org/karlicoss/orgparse

Install
-------

  pip install orgparse


Usage
-----

There are pretty extensive doctests if you're interested in some specific method. Otherwise here are some example snippets:


Load org node
^^^^^^^^^^^^^
::

    from orgparse import load, loads

    load('PATH/TO/FILE.org')
    load(file_like_object)

    loads('''
    * This is org-mode contents
      You can load org object from string.
    ** Second header
    ''')


Traverse org tree
^^^^^^^^^^^^^^^^^

>>> root = loads('''
... * Heading 1
... ** Heading 2
... *** Heading 3
... ''')
>>> for node in root[1:]:  # [1:] for skipping root itself
...     print(node)
* Heading 1
** Heading 2
*** Heading 3
>>> h1 = root.children[0]
>>> h2 = h1.children[0]
>>> h3 = h2.children[0]
>>> print(h1)
* Heading 1
>>> print(h2)
** Heading 2
>>> print(h3)
*** Heading 3
>>> print(h2.get_parent())
* Heading 1
>>> print(h3.get_parent(max_level=1))
* Heading 1


Accessing node attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

>>> root = loads('''
... * DONE Heading          :TAG:
...   CLOSED: [2012-02-26 Sun 21:15] SCHEDULED: <2012-02-26 Sun>
...   CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] =>  0:05
...   :PROPERTIES:
...   :Effort:   1:00
...   :OtherProperty:   some text
...   :END:
...   Body texts...
... ''')
>>> node = root.children[0]
>>> node.heading
'Heading'
>>> node.scheduled
OrgDateScheduled((2012, 2, 26))
>>> node.closed
OrgDateClosed((2012, 2, 26, 21, 15, 0))
>>> node.clock
[OrgDateClock((2012, 2, 26, 21, 10, 0), (2012, 2, 26, 21, 15, 0))]
>>> bool(node.deadline)   # it is not specified
False
>>> node.tags == set(['TAG'])
True
>>> node.get_property('Effort')
60
>>> node.get_property('UndefinedProperty')  # returns None
>>> node.get_property('OtherProperty')
'some text'
>>> node.body
'  Body texts...'

"""
# [[[end]]]

import codecs

import OrgExtended.orgparse.node as node
import OrgExtended.orgparse.utils.py3compat as bs
#from .node import parse_lines
#from .utils.py3compat import basestring
import OrgExtended.asettings as sets


def bomType(file):
    """
    returns file encoding string for open() function

    EXAMPLE:
        bom = bomtype(file)
        open(file, encoding=bom, errors='ignore')
    """

    f = open(file, 'rb')
    b = f.read(4)
    f.close()

    if (b[0:3] == b'\xef\xbb\xbf'):
        return "utf8"

    # Python automatically detects endianess if utf-16 bom is present
    # write endianess generally determined by endianess of CPU
    if ((b[0:2] == b'\xfe\xff') or (b[0:2] == b'\xff\xfe')):
        return "utf16"

    if ((b[0:5] == b'\xfe\xff\x00\x00') 
              or (b[0:5] == b'\x00\x00\xff\xfe')):
        return "utf32"

    # If BOM is not provided, then assume its the codepage
    #     used by your operating system
    return "cp1252"
    # For the United States its: cp1252

def load(path):
    """
    Load org-mode document from a file.

    :type path: str or file-like
    :arg  path: Path to org file or file-like object of a org document.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    try:

        if isinstance(path, bs.basestring):
            orgfile = codecs.open(path, encoding='utf-8-sig')
            filename = path
        else:
            orgfile = path
            filename = path.name if hasattr(path, 'name') else '<file-like>'
        return loadi((l.rstrip('\n') for l in orgfile.readlines()),filename=filename)
    except:
        bom = bomType(path)
        if isinstance(path, bs.basestring):
            orgfile = codecs.open(path, encoding=bom)
            filename = path
        else:
            orgfile = path
            filename = path.name if hasattr(path, 'name') else '<file-like>'
        return loadi((l.rstrip('\n') for l in orgfile.readlines()),filename=filename)


def loads(string, filename='<string>'):
    """
    Load org-mode document from a string.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return loadi(string.splitlines(), filename=filename)


def loadi(lines, filename='<lines>'):
    """
    Load org-mode document from an iterative object.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    # Push our default system wide todo states into the file parser
    todoStates = sets.Get("todoStates", sets.defaultTodoStates)
    todos = []
    dones = []
    found = False
    for i in todoStates:
        if i == "|":
            found = True
            continue
        if found:
            dones.append(i)
        else:
            todos.append(i)
    return node.parse_lines(lines, filename=filename, todos=todos, dones=dones)
