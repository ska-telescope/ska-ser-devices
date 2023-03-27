Guide
=====

Usage
-----
Releases of the ``ska_ser_devices`` python package are published to the
`SKAO Artefact Repository`_. This is a library package only; it is used
by adding it to your project as a dependency.

Development
-----------
The development toolchain is provided by the `ska-cicd-makefile`_ project,
which is added to this project as a git submodule. Therefore when cloning
this repo, be sure to use the ``--recurse-submodules`` argument when
cloning and pulling. For efficiency reasons, it is also a good idea to
clone with the ``--shallow-submodules`` argument:

.. code-block:: shell-session

    me@local:~$ git clone --recurse-submodules --shallow-submodules https://gitlab.com/ska-telescope/ska-ser-devices.git
    Cloning into 'ska-ser-devices'...
    remote: Enumerating objects: 73, done.
    remote: Counting objects: 100% (73/73), done.
    remote: Compressing objects: 100% (57/57), done.
    remote: Total 73 (delta 6), reused 0 (delta 0), pack-reused 0
    Unpacking objects: 100% (73/73), 63.48 KiB | 1.71 MiB/s, done.
    Submodule '.make' (https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile.git) registered for path '.make'
    Cloning into '/home/dev065/foo/ska-ser-devices/.make'...
    remote: Enumerating objects: 231, done.        
    remote: Counting objects: 100% (231/231), done.        
    remote: Compressing objects: 100% (190/190), done.        
    remote: Total 231 (delta 21), reused 201 (delta 20), pack-reused 0        
    Receiving objects: 100% (231/231), 6.08 MiB | 4.16 MiB/s, done.
    Resolving deltas: 100% (21/21), done.
    Submodule path '.make': checked out '93828e42b0b1415b674281257d09df04c8b87a8b'
    me@local:~$ 

A Visual Studio Code devcontainer specification is provided,
so if using Visual Studio Code with the Dev Containers plugin,
you will be provided with a suitable development environment.

If developing on your local machine (not in a container),
then setting up a development environment is still quite easy.
You need to install poetry (if not already installed),
tell it not to use a virtual environment,
and then tell it to install the `ska_ser_devices` package.
For a linux machine:

.. code-block:: shell-session

    me@local:/ska-ser-devices$ curl -sSL https://install.python-poetry.org | python3 -
    Retrieving Poetry metadata

    # Welcome to Poetry!

    This will download and install the latest version of Poetry,
    a dependency and package manager for Python.

    It will add the `poetry` command to Poetry's bin directory, located at:

    /root/.local/bin

    You can uninstall at any time by executing this script with the --uninstall option,
    and these changes will be reverted.

    Installing Poetry (1.4.1): Done

    Poetry (1.4.1) is installed now. Great!

    To get started you need Poetry's bin directory (/root/.local/bin) in your `PATH`
    environment variable.

    Add `export PATH="/root/.local/bin:$PATH"` to your shell configuration file.

    Alternatively, you can call Poetry explicitly with `/root/.local/bin/poetry`.

    You can test that everything is set up by executing:

    `poetry --version`

    me@local:/ska-ser-devices$ poetry config virtualenvs.create false
    me@local:/ska-ser-devices$ poetry install

    Skipping virtualenv creation, as specified in config file.
    Installing dependencies from lock file

    Package operations: 43 installs, 6 updates, 0 removals

    • Updating charset-normalizer (3.0.1 -> 3.1.0)
    • Updating urllib3 (1.26.14 -> 1.26.15)
    • Installing alabaster (0.7.13)
    • Installing babel (2.12.1)
    • Updating docutils (0.19 -> 0.17.1)
    • Installing imagesize (1.4.1)
    • Installing lazy-object-proxy (1.9.0)
    • Installing snowballstemmer (2.2.0)
    • Installing sphinxcontrib-applehelp (1.0.4)
    • Installing sphinxcontrib-devhelp (1.0.2)
    • Installing sphinxcontrib-htmlhelp (2.0.1)
    • Installing sphinxcontrib-jsmath (1.0.1)
    • Installing sphinxcontrib-qthelp (1.0.3)
    • Installing sphinxcontrib-serializinghtml (1.1.5)
    • Updating typing-extensions (4.4.0 -> 4.5.0)
    • Installing wrapt (1.15.0)
    • Installing astroid (2.15.0)
    • Installing dill (0.3.6)
    • Installing exceptiongroup (1.1.1)
    • Installing iniconfig (2.0.0)
    • Installing isort (5.12.0)
    • Installing mccabe (0.7.0)
    • Installing platformdirs (3.1.1)
    • Installing pluggy (1.0.0)
    • Installing pycodestyle (2.10.0)
    • Installing pyflakes (3.0.1)
    • Updating six (1.16.0 /usr/lib/python3/dist-packages -> 1.16.0)
    • Installing sphinx (5.3.0)
    • Installing tomlkit (0.11.6)
    • Installing click (8.1.3)
    • Installing coverage (7.2.2)
    • Installing flake8 (6.0.0)
    • Installing junit-xml-2 (1.9)
    • Installing mypy-extensions (1.0.0)
    • Updating pathspec (0.9.0 /usr/lib/python3/dist-packages -> 0.11.1)
    • Installing pydocstyle (6.3.0)
    • Installing pylint (2.17.0)
    • Installing pytest (7.2.2)
    • Installing restructuredtext-lint (1.4.0)
    • Installing sphinxcontrib-jquery (4.1)
    • Installing black (23.1.0)
    • Installing darglint (1.8.1)
    • Installing flake8-docstrings (1.7.0)
    • Installing flake8-rst-docstrings (0.3.0)
    • Installing mypy (1.1.1)
    • Installing pylint-junit (0.3.2)
    • Installing pytest-cov (4.0.0)
    • Installing sphinx-autodoc-typehints (1.22)
    • Installing sphinx-rtd-theme (1.2.0)

    Installing the current project: ska-ser-devices (0.0.1)
    me@local:/ska-ser-devices$

You can now use the ``ska-cicd-makefile`` make targets to test your code:

* ``make python-format``
* ``make python-lint``
* ``make python-test``
* ``make docs-build html``

.. _SKAO Artefact Repository: https://artefact.skao.int/
.. _ska-cicd-makefile: https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile
