=========================
Installation Instructions
=========================

``because`` is an ordinary Python package that can be installed with ``pip``.
But at least for now, ``because`` is in early stages and can only be installed
from the `GitHub repository for because
<https://github.com/harts-boundless/because>`_, e.g. ::

    pip install git+git://github.com/harts-boundless/because.git

Installation methods other than ``pip`` are not really recommended.


Virtualenv
----------

As with any other Python package, it is generally recommended to use
`virtualenv <https://virtualenv.pypa.io/en/stable/userguide/>`_ to control
Python dependencies, and always to avoid running ``sudo pip`` if you have any
choice. (This is likely to dump files in your system installation of Python,
and cause any number of confusing issues at unpredictable times.)

If you would like to make it slightly easier to work with virtualenv, you may
want to try `vex <https://pypi.python.org/pypi/vex>`_.

There is also of course no reason why you could not install the package in a
container or a VM if you wanted to, it's just a bit of a heavyweight solution
if all you are doing is writing some Python.


Diagnosing Problems
-------------------

Once the package is installed, you should immediately be able to import it in
the normal way, e.g. from a Python shell::

    import because

Or from the command line, this should run without error::

    python -c "import because"

If ``because`` is not installed in the Python you are using, it would be normal
to see the following traceback::

    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ImportError: No module named because

If these commands produce this error, it means that the ``python`` command you
are running cannot find the installed package.

This may mean that you did not install the package, that it was deleted, that
you installed it in a different virtualenv, that you installed it on the system
and are running Python in a virtualenv (or vice versa), or that you have not
activated the virtualenv where you installed it.

In case of such problems, there are several diagnostics you can try from the
shell (terminal window).

You may want to see which packages are installed in the current Python
environment using::

    pip freeze

If you can't find a package you expect to be there, you may want to examine the
list of paths that Python checks for packages using::

    python -c `import sys; print(sys.path)`

You may want to know which python binary is running, use::

    which python

Sometimes problems are caused when you aren't sure which program is running
when you run ``pip`` - for example, if you have ``pip`` installed for Python 2
but you are running Python 3. A starting point to identify this problem is::

    which pip
    
