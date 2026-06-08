import sys
import numpy as np
from matplotlib import pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator as il
from matplotlib.projections import get_projection_class
from matplotlib import gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from .. import abWwiiiAlphaBetaLoader


class abAlphaBetaSingleCellPlotter:

  def __init__(self, directions, dirmeasure='rad', alphaColor='red', betaColor=[.3, .3, 1]):
    self.directions = directions
    self.dirmeasure = dirmeasure # can be deg
    self.alphaColor = alphaColor
    self.betaColor = betaColor
    self.refLineWidth = 1

  def plotCell(self, cellPoly, ax, color='darkgreen', linewidth=1.5):
    bnd = cellPoly.boundary.coords[:]
    x = [p[0] for p in bnd]
    y = [p[1] for p in bnd]
    if hasattr(ax, "projection"):
      ax.plot(x, y, color = color, linewidth=linewidth, transform=ccrs.PlateCarree())
    else:
      ax.plot(x, y, color=color, linewidth=linewidth)

  def plot(self, alphaByDir, betaByDir, ax=None, axesPosition=(0, 0, 1, 1)):
    assert len(alphaByDir.shape) == 1, 'abAlphaBetaPlotter: only direction-varying alpha and beta are supported'

    drs = self.directions
    a = alphaByDir
    b = betaByDir
    if ax is None:
      ax = plt.axes(axesPosition, polar=True)

    if drs[0] != drs[-1]:
      drs = np.concatenate([drs, [drs[0]]])
      a = np.concatenate([a, [a[0]]])
      b = np.concatenate([b, [b[0]]])
   
    drsRad = np.deg2rad(drs) if self.dirmeasure == 'deg' else drs
    ddr = drsRad[1] - drsRad[0]
    drsRad = drsRad - ddr

    ax.bar(drsRad, b, color=self.betaColor, linewidth=0)
    ax.bar(drsRad, a, color=self.alphaColor, linewidth=0)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_ylim([0, 1])
    ax.axis('off')
    ax.plot(0, 0, color='k', marker='.', markersize=1)
    ax.plot(drsRad, np.ones(drsRad.shape), linewidth=self.refLineWidth, color='k')


class abAlphaBetaMeshPlotter:

  def __init__(self, coords, geoCoords, alphaList, betaList, mesh, dirs, lonlims=None, latlims=None, 
               cstLineRes='auto', polarDiagLatSize=1, margin=1, verbose=True):
    """
    abAlphaBetaMeshPlotter: class to plot a mesh, and on each cell a polar plot of alpha and beta.
    It works only for alpha/beta changing with the sole direction, not with frequency.
    geoCoords: list of tuples with the coordinates of the polar diagrams (the baricenter of each cell)
    alphaList, betaList: list of alpha and beta. Must be of the same length al geoCoords.
    mesh: object representing the mesh, as an abGrid instance.
    dirs: list of directions.
    lonlims/latlims: allow to plot a subset of the grid.
    cstLineRes: resolution of coastline.
    """
    self.coords = coords
    self.geoCoords = geoCoords
    self.alphaList = alphaList
    self.betaList = betaList
    self.mesh = mesh
    self.lonlims = lonlims
    self.latlims = latlims
    self.figsize = [14, 8]
    self.figdpi = 80
    self.polarDiagLatSize = polarDiagLatSize
    self.dirs = dirs
    self.cstLineRes = cstLineRes
    self.dirmeasure = 'rad'
    self.betaColor = [.3, .3, 1]
    self.alphaColor = 'red'
    self.cellColor = 'darkgreen'
    self.mainAxesPosition = [0, 0, 1, 1]
    self.landColor = 'lightgray'
    self.seaColor = 'lightblue'
    self.margin = margin # if centroid is closer than margin(deg) to boundary, pie not plotted
    self.nPlottedCells = None # if != None, only the first cells are plotted
    self.verbose = verbose

  def _print(self, msg):
    if self.verbose:
      print(msg)

  def _wrapLonToCentral(self, lon, clon):
    """Wrap lon to [clon-180, clon+180)."""
    lon = np.asarray(lon, dtype=np.float64)
    return ((lon - clon + 180.0) % 360.0) - 180.0 + clon

  def _getLonLatLims(self):
    if self.lonlims is None:
      lons = [c[0] for c in self.geoCoords]
      lonlims = [min(lons), max(lons)]
    else:
      lonlims = self.lonlims
    if self.latlims is None:
      lats = [c[1] for c in self.geoCoords]
      latlims = [min(lats), max(lats)]
    else:
      latlims = self.latlims
    return lonlims, latlims

  def plotMap(self, ax, lonlims=None, latlims=None):
    if lonlims is None or latlims is None:
      lonlims, latlims = self._getLonLatLims()
    ax.set_extent([lonlims[0], lonlims[1], latlims[0], latlims[1]], crs=ccrs.PlateCarree())

    sea = cfeature.NaturalEarthFeature('physical', 'ocean', '10m', facecolor=self.seaColor, edgecolor='none', zorder=0)
    ax.add_feature(sea)

    lnd = cfeature.NaturalEarthFeature('physical', 'land', '10m', facecolor=self.landColor, edgecolor='none', zorder=1)
    lndmsk = ax.add_feature(lnd)

    ax.coastlines(resolution=self.cstLineRes, linewidth=0.5, zorder=2)
    return lndmsk

  def plot(self, ax=None, plotMap=True, lonlims=None, latlims=None):
    if ax is None:
      fig = plt.figure(figsize=self.figsize, dpi=self.figdpi)
      mainAx = plt.axes(projection=ccrs.PlateCarree())
      axCreated = True
    else:
      mainAx = ax
      fig = mainAx.figure
      axCreated = False

    if lonlims is None or latlims is None:
      lonlims, latlims = self._getLonLatLims()
    else:
      self.lonlims, self.latlims = lonlims, latlims

    if plotMap:
      lndmsk = self.plotMap(mainAx, lonlims, latlims)
    else:
      lndmsk = None

    if axCreated:
      mainAx.set_position(self.mainAxesPosition)

    geo = hasattr(mainAx, "projection")
    if geo:
      mainAx.set_extent([lonlims[0], lonlims[1], latlims[0], latlims[1]], crs=ccrs.PlateCarree())
      clon = float(mainAx.projection.proj4_params["lon_0"])
      lonlims = self._wrapLonToCentral(lonlims, clon)
      if lonlims[0] >= lonlims[1]:
        lonlims[1] += 360
    else:
      mainAx.set_xlim(lonlims)
      mainAx.set_ylim(latlims)

    mesh = self.mesh
    mrgn = self.margin
    nPlottedCells = self.nPlottedCells

    abPlotter = abAlphaBetaSingleCellPlotter(
      directions=self.dirs, 
      dirmeasure=self.dirmeasure, 
      alphaColor=self.alphaColor, 
      betaColor=self.betaColor
    )

    ncl = len(self.coords)
    axs = []
    icl = 0
    self._print(f"Plotting {ncl} cells ...")
    for idx, (crd, geocrd, a, b) in enumerate(zip(self.coords, self.geoCoords, self.alphaList, self.betaList)):
      if (nPlottedCells is not None) and (icl >= nPlottedCells):
        break

      lon, lat = geocrd[0], geocrd[1]
      if geo:
        lon = self._wrapLonToCentral(lon, clon)

      plotPie = (
        (lonlims[0] + mrgn <= lon <= lonlims[1] - mrgn) and 
        (latlims[0] + mrgn <= lat <= latlims[1] - mrgn)
      )
      plotPolygon = (
        (lonlims[0] - 3 <= lon <= lonlims[1] + 3) and 
        (latlims[0] - 3 <= lat <= latlims[1] + 3)
      )
      if (not plotPie) and (not plotPolygon):
        continue

      if self.verbose:
        sys.stdout.write(f"\r    > progress: {float(idx + 1) / ncl * 100.:.1f}%")
        sys.stdout.flush()

      crdii = (crd[0] - 1, crd[1] - 1)
      if crdii in mesh.cellMap:
        cellPoly = mesh.cellMap[crdii]

        if plotPolygon:
          abPlotter.plotCell(cellPoly, mainAx, color=self.cellColor)

        if plotPie:
          _, y0, _, y1 = cellPoly.bounds
          yspan = y1 - y0
          axDiagLatSize = yspan * self.polarDiagLatSize
          axDiagLonSize = axDiagLatSize

          if geo:
            lon, lat = mainAx.projection.transform_point(geocrd[0], geocrd[1], ccrs.PlateCarree())

          bbox = [lon - axDiagLonSize / 2., 
                  lat - axDiagLatSize / 2., 
                  axDiagLonSize, 
                  axDiagLatSize]
          ax_inset = il.inset_axes(
            mainAx, '100%', '100%', 
            bbox_to_anchor=bbox, 
            bbox_transform=mainAx.transData, 
            borderpad=0, 
            axes_class=get_projection_class("polar")
          )
          abPlotter.plot(a, b, ax=ax_inset)
          axs.append(ax_inset)

      icl += 1

    if self.verbose:
      self._print('')

    plt.axes(mainAx)
    return fig, mainAx, axs, lndmsk

  def plotLegend(self, ax, xn, yn, figLegendSize=0.15, fontsize=10):
    bbox = [xn - figLegendSize / 2., 
            yn - figLegendSize / 2., 
            figLegendSize, 
            figLegendSize]

    lgndax = il.inset_axes(
      ax, '100%', '100%', 
      bbox_to_anchor=bbox, 
      bbox_transform=ax.transAxes, 
      borderpad=0, 
      axes_class=get_projection_class("polar")
    )

    abPlotter = abAlphaBetaSingleCellPlotter(
      directions = self.dirs, 
      dirmeasure = self.dirmeasure, 
      alphaColor = self.alphaColor, 
      betaColor = self.betaColor
    )
    lgndB = np.ones(self.dirs.shape)
    lgndA = lgndB / 2.5
    abPlotter.plot(lgndA, lgndB, ax=lgndax)

    lgndax.text(1.5 * np.pi, 0.20, r'$\alpha$', horizontalalignment='center', verticalalignment='center', fontsize=fontsize)
    lgndax.text(1.5 * np.pi, 0.70, r'$\beta$', horizontalalignment='center', verticalalignment='center', fontsize=fontsize)
    lgndax.plot([0.5 * np.pi, 0.5 * np.pi], [0, 1], linewidth=1, color='k')
    lgndax.text(0, 0.17, '0', fontsize=fontsize)
    lgndax.text(np.pi / 2. * (7. / 8.), 0.9, '1', fontsize=fontsize)

    return lgndax


def plotLocalShadowFigure(abLocalFileName, abShadowFileName, mesh, dirs, nfreq, pltlonlims, pltlatlims, figsize=[7, 8], ifreq=0, axes=None, **kwargs):
  """
  Plot both local and shadow alphas and betas, on 2 different axes
  """
  if axes is None:
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 1, figure=fig)
    ax0 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree())
    ax1 = fig.add_subplot(gs[1, 0], projection=ccrs.PlateCarree())
    axes = [ax0, ax1]
  else:
    fig = axes[0].figure

  ldr = abWwiiiAlphaBetaLoader.abWwiiiAlphaBetaLoader(nfreq)

  ab = ldr.load(abLocalFileName)
  alphaListLoc = [a[ifreq, :] for a in ab.alphaList] 
  betaListLoc = [b[ifreq, :] for b in ab.betaList] 

  plotter = abAlphaBetaMeshPlotter(ab.coords, ab.geoCoords, alphaListLoc, betaListLoc, mesh, dirs, lonlims=pltlonlims, latlims=pltlatlims, **kwargs)
  _, _, _, lndmskLocal = plotter.plot(ax=axes[0])

  ab = ldr.load(abShadowFileName)
  alphaListShd = [a[ifreq, :] for a in ab.alphaList] 
  betaListShd = [b[ifreq, :] for b in ab.betaList] 

  plotter = abAlphaBetaMeshPlotter(ab.coords, ab.geoCoords, alphaListShd, betaListShd, mesh, dirs, lonlims=pltlonlims, latlims=pltlatlims, **kwargs)
  _, _, _, lndmskShadow = plotter.plot(ax=axes[1])

  return fig, axes, (lndmskLocal, lndmskShadow)


def createMeshPlotterFromFile(abFileName, mesh, dirs, nfreq, ifreq=0, **kwargs):
  """
  Create a mesh plotter from an obstruction file.
  """
  ldr = abWwiiiAlphaBetaLoader.abWwiiiAlphaBetaLoader(nfreq)

  lonlims = kwargs.get('lonlims', None)
  if lonlims is not None:
    lonlims = [lonlims[0] - 3, lonlims[1] + 3]
  latlims = kwargs.get('latlims', None)
  ab = ldr.load(abFileName, lonlims=lonlims, latlims=latlims)
  if not ab.coords:
    raise RuntimeError(f'No cell loaded from file {abFileName}. Check the file content and the provided lonlims/latlims.')

  alphaList = [a[ifreq, :] for a in ab.alphaList] 
  betaList = [b[ifreq, :] for b in ab.betaList] 

  plotter = abAlphaBetaMeshPlotter(ab.coords, ab.geoCoords, alphaList, betaList, mesh, dirs, **kwargs)
  return plotter