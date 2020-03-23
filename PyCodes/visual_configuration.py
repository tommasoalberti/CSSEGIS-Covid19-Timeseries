import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, YearLocator, MonthLocator, DayLocator, DateFormatter
import matplotlib.ticker as ticker
from matplotlib.colors import Normalize, LogNorm


class VisualConfiguration():

    def __init__(self):
        super().__init__()
        self.ticksize = 7
        self.labelsize = 8
        self.textsize = 5
        self.titlesize = 9
        self.headersize = 10
        self.cellsize = 15
        self.empty_label = '  '
        self.locators = {'year' : YearLocator, 'month' : MonthLocator, 'day' : DayLocator}

    @staticmethod
    def autocorrect_transparency(alpha):
        """

        """
        if alpha < 0.4:
            alpha = 0.4765
        return alpha

    @staticmethod
    def get_empty_scatter_handle(ax):
        """

        """
        handle = ax.scatter([np.nan], [np.nan], color='none', alpha=0)
        return handle

    @staticmethod
    def get_facecolors_from_cmap(cmap, norm, vector):
        """

        """
        _cmap = plt.cm.get_cmap(cmap)
        facecolors = _cmap(norm(vector))
        return facecolors

    @staticmethod
    def update_y_scaling(ax, scale, base):
        """

        """
        ylim = list(ax.get_ylim())
        if ylim[1] <= 0:
            top = base
        else:
            top = None
        if scale == 'linear':
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax.set_ylim(bottom=0, top=top)
        elif scale == 'log':
            ax.set_yscale('log', basey=base)
            if ((top is not None) and (top >= base)):
                bottom = 0.2
                ax.set_ylim(bottom=bottom, top=top)
        else:
            raise ValueError("invalid scale: {}".format(scale))
        return ax

    def transform_x_as_datetime(self, ax, xmajor='year', xminor='month', xfmt="%Y-%m-%d", xrotation=None):
        """

        """
        f_xmaj, f_xmin = self.locators[xmajor], self.locators[xminor]
        ax.xaxis.set_major_locator(f_xmaj())
        ax.xaxis.set_minor_locator(f_xmin())
        ax.xaxis.set_major_formatter(DateFormatter(xfmt))
        if xrotation is not None:
            ax.tick_params(axis='x', rotation=xrotation)
        return ax

    def autocorrect_legend_entries(self, ax, handles, labels):
        """

        """
        n = len(labels)
        if n == 0:
            raise ValueError("no legend handles/labels to autocorrect")
        if n == 1:
            empty_handle = self.get_empty_scatter_handle(ax)
            handles = [empty_handle, handles[0], empty_handle]
            labels = [self.empty_label, labels[0], self.empty_label]
            ncol = 3
        elif n in (2, 3):
            ncol = n
        else:
            ncol = int(np.sqrt(len(handles)))
        return handles, labels, ncol

    def update_legend_design(self, leg, title=None, textcolor=None, facecolor=None, edgecolor=None, borderaxespad=None):
        """

        """
        if title:
            leg.set_title(title, prop={'size': self.labelsize, 'weight' : 'semibold'})
            if textcolor:
                leg.get_title().set_color(textcolor)
        leg._legend_box.align = "center"
        frame = leg.get_frame()
        if facecolor:
            frame.set_facecolor(facecolor)
        if edgecolor:
            frame.set_edgecolor(edgecolor)
        if textcolor:
            for text in leg.get_texts():
                text.set_color(textcolor)
        return leg
