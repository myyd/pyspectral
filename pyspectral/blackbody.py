#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014, 2015 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <adam.dybbroe@smhi.se>
#   Panu Lahtinen <panu.lahtinen@fmi.fi>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Planck radiation equation"""

import numpy as np

import logging
LOG = logging.getLogger(__name__)

H_PLANCK = 6.62606957 * 1e-34  # SI-unit = [J*s]
K_BOLTZMANN = 1.3806488 * 1e-23  # SI-unit = [J/K]
C_SPEED = 2.99792458 * 1e8  # SI-unit = [m/s]

EPSILON = 0.000001

# -------------------------------------------------------------------


def blackbody_wn(wavenumber, temp):
    """The Planck radiation or Blackbody radiation as a function of wavenumber
    SI units!
    blackbody_wn(wavnum, temperature)
    wavenumber = A wavenumber (scalar) or a sequence of wave numbers (m-1)
    temp = A temperatfure (scalar) or a sequence of temperatures (K)


    Output: The spectral radiance in Watts per square meter per steradian
            per m-1:
            Unit = W/m^2 sr^-1 (m^-1)^-1 = W/m sr^-1

            Converting from SI units to mW/m^2 sr^-1 (cm^-1)^-1:
            1.0 W/m^2 sr^-1 (m^-1)^-1 = 0.1 mW/m^2 sr^-1 (cm^-1)^-1
    """
    LOG.debug("Using wave numbers when calculating the Blackbody temp...")
    if np.isscalar(temp):
        temperature = np.array([temp, ], dtype='float64')
    else:
        temperature = np.array(temp, dtype='float64')
    shape = temperature.shape
    if np.isscalar(wavenumber):
        wavnum = np.array([wavenumber, ], dtype='float64')
    else:
        wavnum = np.array(wavenumber, dtype='float64')

    #print("mid wavenumber: " + str(wavnum[wavnum.shape[0] / 2]))

    nom = 2 * H_PLANCK * (C_SPEED ** 2) * (wavnum ** 3)
    arg1 = H_PLANCK * C_SPEED * wavnum / K_BOLTZMANN
    arg2 = np.where(np.greater(np.abs(temperature), EPSILON),
                    np.array(1. / temperature), -9).reshape(-1, 1)

    arg2 = np.ma.masked_array(arg2, mask=arg2 == -9)
    exp_arg = np.multiply(arg1.astype('float32'), arg2.astype('float32'))
    denom = np.exp(exp_arg) - 1

    rad = nom / denom
    radshape = rad.shape
    if wavnum.shape[0] == 1:
        if temperature.shape[0] == 1:
            return rad[0, 0]
        else:
            return rad[:, 0].reshape(shape)
    else:
        if temperature.shape[0] == 1:
            return rad[0, :]
        else:
            if len(shape) == 1:
                return np.reshape(rad, (shape[0], radshape[1]))
            else:
                return np.reshape(rad, (shape[0], shape[1], radshape[1]))


def blackbody(wavel, temp):
    """The Planck radiation or Blackbody radiation as a function of wavelength
    SI units.
    blackbody(wavelength, temperature)
    wavel = Wavelength or a sequence of wavelengths (m)
    temp = Temperature (scalar) or a sequence of temperatures (K)


    Output: The spectral radiance per meter (not micron!)
            Unit = W/m^2 sr^-1 m^-1
    """
    LOG.debug("Using wavelengths when calculating the Blackbody temp...")

    if np.isscalar(temp):
        temperature = np.array([temp, ], dtype='float64')
    else:
        temperature = np.array(temp, dtype='float64')

    shape = temperature.shape
    # print("temperature min and max = " + str(temperature.min()) +
    #      " " + str(temperature.max()))
    if np.isscalar(wavel):
        wavelength = np.array([wavel, ], dtype='float64')
    else:
        wavelength = np.array(wavel, dtype='float64')

    #print("mid wavelength: " + str(wavelength[wavelength.shape[0] / 2]))

    const = 2 * H_PLANCK * C_SPEED ** 2
    nom = const / wavelength ** 5
    arg1 = H_PLANCK * C_SPEED / (K_BOLTZMANN * wavelength)
    arg2 = np.where(np.greater(np.abs(temperature), EPSILON),
                    np.array(1. / temperature), -9).reshape(-1, 1)
    arg2 = np.ma.masked_array(arg2, mask=arg2 == -9)
    LOG.debug("Max and min - arg1: %s  %s", str(arg1.max()), str(arg1.min()))
    LOG.debug("Max and min - arg2: %s  %s", str(arg2.max()), str(arg2.min()))
    try:
        exp_arg = np.multiply(arg1.astype('float32'), arg2.astype('float32'))
    except MemoryError:
        LOG.warning(("Dimensions used in numpy.multiply probably reached "
                     "limit!\n"
                     "Make sure the Radiance<->Tb table has been created "
                     "and try running again"))
        raise

    LOG.debug("Max and min before exp: %s  %s", str(exp_arg.max()),
              str(exp_arg.min()))
    if exp_arg.min() < 0:
        LOG.warning("Something is fishy: \n" +
                    "\tDenominator might be zero or negative in radiance derivation:")
        dubious = np.where(exp_arg < 0)[0]
        LOG.warning(
            "Number of items having dubious values: " + str(dubious.shape[0]))

    denom = np.exp(exp_arg) - 1
    rad = nom / denom
    # print "rad.shape = ", rad.shape
    radshape = rad.shape
    if wavelength.shape[0] == 1:
        if temperature.shape[0] == 1:
            return rad[0, 0]
        else:
            return rad[:, 0].reshape(shape)
    else:
        if temperature.shape[0] == 1:
            return rad[0, :]
        else:
            if len(shape) == 1:
                return np.reshape(rad, (shape[0], radshape[1]))
            else:
                return np.reshape(rad, (shape[0], shape[1], radshape[1]))
