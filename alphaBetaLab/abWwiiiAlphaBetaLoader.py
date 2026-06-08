import re
import numpy as np


class abAlphaBetaLoadObj:
  def __init__(self):
    self.coords = []
    self.geoCoords = []
    self.alphaList = []
    self.betaList = []
    self.sizeKm = []


class abWwiiiAlphaBetaLoader():

  def __init__(self, nfreq = 25):
    """
    abWwiiiAlphaBetaLoader: utility class to load alpha and beta from files saved by abWwiiiObstrFileSaver
    """
    self.nfreq = nfreq

  def _isInsideBbox(self, lon, lat, lonlims, latlims):
    """
    Check if (lon, lat) is within the bounding box.
    """
    if lonlims is not None:
      if lon < lonlims[0] or lon > lonlims[1]:
        return False
    if latlims is not None:
      if lat < latlims[0] or lat > latlims[1]:
        return False
    return True

  def load(self, abFilePath, lonlims=None, latlims=None):
    """
    Load alpha/beta from a WAVEWATCH III obstruction file.

    Parameters
    ----------
    abFilePath  : str
    lonlims      : sequence [lon_min, lon_max] or None
    latlims      : sequence [lat_min, lat_max] or None
    """
    o = abAlphaBetaLoadObj()
    nfreq = self.nfreq

    # per-cell line count (excluding the two header lines)
    LINES_PER_CELL = 8 + 2 * nfreq

    with open(abFilePath) as fl:
      fl.readline()                                 # L1: header
      npt = int(fl.readline().strip(' \n\r\t'))     # L2: npt

      for ipt in range(npt):
        # --- coordinate comment line ---
        ln = fl.readline().strip(' \n\r\t')
        mtch = re.match('^\$ ilon ilat of the cell\. lon: (-?\d+\.\d+), (lat: )?(-?\d+\.\d+).*', ln)
        if not mtch:
          raise RuntimeError(f'Cannot parse coordinate comment at cell #{ipt + 1}:\n{ln}')

        lon = float(mtch.group(1))
        lat = float(mtch.group(3))

        # --- ilon/ilat line ---
        ln = fl.readline().strip(' \n\r\t')
        vls = [int(v) for v in ln.split() if v != '']
        ilon = vls[0]
        ilat = vls[1]

        # --- bbox filter ---
        if not self._isInsideBbox(lon, lat, lonlims, latlims):
          # advance LINES_PER_CELL-2 lines
          for _ in range(LINES_PER_CELL - 2):
            fl.readline()
          continue

        # --- read cell data ---
        o.geoCoords.append((lon, lat))
        o.coords.append((ilon, ilat))

        fl.readline()                               # $ sizes of the cell in km
        szln = fl.readline().strip(' \n\r\t')
        sizes = np.array([float(v) for v in szln.split() if v != ''])
        o.sizeKm.append(sizes)

        fl.readline()                               # $ mean alpha: ...
        fl.readline()                               # $ mean beta: ...
        fl.readline()                               # $alpha by ik, ith
        alpha = []
        for _ in range(nfreq):
          ln = fl.readline().strip(' \n\r\t')
          a = [float(v) for v in ln.split() if v != '']
          alpha.append(a)
        alpha = np.array(alpha)
        o.alphaList.append(alpha)

        fl.readline()                               # $beta by ik, ith
        beta = []
        for _ in range(nfreq):
          ln = fl.readline().strip(' \n\r\t')
          b = [float(v) for v in ln.split() if v != '']
          beta.append(b)
        beta = np.array(beta)
        o.betaList.append(beta)

    return o