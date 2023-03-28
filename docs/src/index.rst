ska-ser-devices
===============

The ``ska-ser-devices`` repository supports low-level interfacing of software with hardware,
within `Square Kilometre Array Observatory`_ control system software.

It is the home of the :py:mod:`ska_ser_devices` python package.
The ``ska_ser_devices`` python package is currently under development;
at present it contains only a :py:mod:`~ska_ser_devices.client_server` subpackage,
which provides classes for writing application-layer interfaces
on top of connection-oriented transport-layer interfaces
(mainly TCP, but a Telnet client is also provided for debugging purposes).
For details, see the :doc:`API docs <api/index>`.`

.. _Square Kilometre Array Observatory: https://skao.int/

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/index
   guide/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
