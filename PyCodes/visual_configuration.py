import numpy as np
import itertools
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, YearLocator, MonthLocator, DayLocator, DateFormatter
import matplotlib.ticker as ticker
from matplotlib.colors import Normalize, LogNorm

class CustomTicker(ticker.LogFormatterSciNotation):

    def __call__(self, x, pos=None):
        """
        https://stackoverflow.com/questions/43923966/logformatter-tickmarks-scientific-format-limits/43926354#43926354
        """
        if x not in [0.1,1,10]:
            return ticker.LogFormatterSciNotation.__call__(self,x, pos=None)
        else:
            return "{x:g}".format(x=x)

class VisualConfiguration():

    def __init__(self, directory, ticksize=7, labelsize=8, textsize=5, titlesize=9, headersize=10, cellsize=15):
        super().__init__()
        self.directory = directory
        self.ticksize = ticksize
        self.labelsize = labelsize
        self.textsize = textsize
        self.titlesize = titlesize
        self.headersize = headersize
        self.cellsize = cellsize
        self.empty_label = '  '
        self.locators = {'year' : YearLocator, 'month' : MonthLocator, 'day' : DayLocator}

    @staticmethod
    def generate_linestyle_cycle(linestyles):
        """

        """
        return itertools.cycle((linestyles))

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
    def update_y_scaling(ax, scale):
        """

        """
        if scale == 'linear':
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ','))) # '{:,}'
        elif scale == 'log':
            # ax.yaxis.set_major_locator(ticker.LogLocator(base=10))
            # ax.yaxis.set_minor_locator(ticker.LogLocator(base=10, subs=np.arange(2, 10)*.1))
            ax.set_yscale('log', basey=10)
            ax.yaxis.set_major_formatter(CustomTicker())
            # ax.yaxis.set_major_formatter(ticker.LogFormatter(base=10))
            ax.yaxis.set_minor_formatter(ticker.NullFormatter())
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
            # leg.get_title().set_ha("center")
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

    def display_image(self, fig, savename=None, dpi=800, bbox_inches='tight', pad_inches=0.1, extension='.png', **kwargs):
        """

        """
        if savename is None:
            plt.show()
        elif isinstance(savename, str):
            savepath = '{}Figures/{}{}'.format(self.directory, savename, extension)
            fig.savefig(savepath, dpi=dpi, bbox_inches=bbox_inches, pad_inches=pad_inches, **kwargs)
        else:
            raise ValueError("invalid type(savename): {}".format(type(savename)))
        plt.close(fig)
