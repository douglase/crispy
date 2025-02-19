try:
    from astropy.io import fits
except BaseException:
    import pyfits as fits

import numpy as np
from datetime import date
import logging
from crispy.tools.initLogger import getLogger
log = getLogger('crispy')

''' most of this code is due to Tim Brandt '''


class Image:

    """
    Image is the basic class for images

    self.data, self.ivar, and self.header should be numpy ndarrays,
    which can be read from and written to a fits file with the load
    and write methods.  If not ndarrays, they should be None.

    Image may be initialized with the name of the raw file to read,
    through a call to Image.load().
    """

    def __init__(self, filename='', data=None, ivar=None,
                 header=None, extraheader=None):
        self.data = data
        self.ivar = ivar
        if header is None:
            self.header = fits.PrimaryHDU().header
        else:
            self.header = header
        self.filename = filename
        self.extraheader = extraheader

        if data is None and filename != '':
            self.load(filename)

    def load(self, filename, loadbadpixmap=False):
        """
        Image.load(outfilename)

        Read the first HDU with data from filename into self.data, and
        HDU[0].header into self.header.  If there is more than one HDU
        with data, attempt to read the second HDU with data into
        self.ivar.

        """
        try:
            self.filename = filename
            hdulist = fits.open(filename, ignore_missing_end=True)
            self.header = hdulist[0].header
            if hdulist[0].data is not None:
                i_data = 0
            else:
                i_data = 1

            self.data = hdulist[i_data].data.copy()
            log.info("Read data from HDU " + str(i_data) + " of " + filename)

            if len(hdulist) > i_data + 1:
                self.ivar = hdulist[i_data + 1].data.copy()
                if self.ivar.shape != self.data.shape:
                    log.error("Error: data (HDU " +
                              str(i_data) +
                              ") and inverse variance (HDU " +
                              str(i_data +
                                  1) +
                              ") have different shapes in file " +
                              filename)
                    self.ivar = None
                else:
                    log.info("Read inverse variance from HDU " +
                             str(i_data + 1) + " of " + filename)
#            elif loadbadpixmap:
#                self.ivar = fits.open('calibrations/mask.fits')[0].data
            else:
                self.ivar = None
        except BaseException:
            log.error("Unable to read data and header from " + filename)
            self.data = None
            self.header = None
            self.ivar = None

    def write(self, filename, clobber=True):
        """
        Image.write(outfilename, clobber=True)

        Creates a primary HDU using self.data and self.header, and
        attempts to write to outfilename.  If self.ivar is not None,
        append self.ivar as a second HDU before writing to a file.
        clobber is provided as a keyword to fits.HDUList.writeto.
        """

        hdr = fits.PrimaryHDU().header
        today = date.today().timetuple()
        yyyymmdd = '%d%02d%02d' % (today[0], today[1], today[2])
        hdr['date'] = (yyyymmdd, 'File creation date (yyyymmdd)')

        for i, key in enumerate(self.header):
            hdr.append(
                (key,
                 self.header[i],
                 self.header.comments[i]),
                end=True)

        out = fits.HDUList(fits.PrimaryHDU(None, hdr))
        out.append(fits.PrimaryHDU(self.data.astype(np.float32)))
        if self.ivar is not None:
            out.append(fits.PrimaryHDU(self.ivar.astype(np.float32)))

        if self.extraheader is not None:
            try:
                out.append(fits.PrimaryHDU(None, self.extraheader))
            except BaseException:
                log.warn("Extra header in image class must be a FITS header.")

        try:
            out.writeto(filename, clobber=clobber)
            log.info("Writing data to " + filename)

        except BaseException:
            log.error("Unable to write FITS file " + filename)
