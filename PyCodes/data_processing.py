from condition_mapping import *
from visual_configuration import *

import datetime
import csv

class DataBase(VisualConfiguration):

    def __init__(self, directory):
        """

        """
        super().__init__()
        self.directory = directory
        self.path_confirmed = '{}Data/time_series_19-covid-Confirmed.csv'.format(directory)
        self.path_dead = '{}Data/time_series_19-covid-Deaths.csv'.format(directory)
        self.path_recovered = '{}Data/time_series_19-covid-Recovered.csv'.format(directory)
        self.source = dict(CSSE='https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data')
        self._raw_data = None
        self._headers = None
        self._datetimes = None
        self._x = None
        self._counties = None
        self._provinces = None
        self._countries = None
        self._longitudes = None
        self._latitudes = None
        self._confirmed = None
        self._dead = None
        self._recovered = None
        self._regions = dict()
        self._timeseries = dict()
        self._searchers = dict()
        self.load_raw_data()
        self.load_datetimes()
        self.load_data()
        self.load_regions()
        self.load_timeseries()

    @property
    def raw_data(self):
        return self._raw_data

    @property
    def headers(self):
        return self._headers

    @property
    def datetimes(self):
        return self._datetimes

    @property
    def x(self):
        return self._x

    @property
    def counties(self):
        return self._counties

    @property
    def provinces(self):
        return self._provinces

    @property
    def countries(self):
        return self._countries

    @property
    def longitudes(self):
        return self._longitudes

    @property
    def latitudes(self):
        return self._latitudes

    @property
    def confirmed(self):
        return self._confirmed

    @property
    def dead(self):
        return self._dead

    @property
    def recovered(self):
        return self._recovered

    @property
    def regions(self):
        return self._regions

    @property
    def timeseries(self):
        return self._timeseries

    @property
    def searchers(self):
        return self._searchers

    @staticmethod
    def get_data_from_file(path):
        """

        """
        with open(path, 'r') as data_file:
            _data = csv.reader(data_file, delimiter=',', quotechar='"')
            return np.array([data for data in _data], dtype=str)

    def load_raw_data(self):
        _confirmed = self.get_data_from_file(self.path_confirmed)
        _dead = self.get_data_from_file(self.path_dead)
        _recovered = self.get_data_from_file(self.path_recovered)
        if not np.all((_confirmed[0, :] == _dead[0, :]) & (_dead[0, :] == _recovered[0, :])):
            raise ValueError("headers for confirmed/dead/recovered do not match")
        self._raw_data = {'confirmed' : _confirmed, 'dead' : _dead, 'recovered' : _recovered}
        self._headers = {'identifier' : _confirmed[0, :4], 'timeseries' : _confirmed[0, 4:]}

    def load_datetimes(self):
        _datetimes = []
        dts = np.core.defchararray.split(self.headers['timeseries'], sep='/')
        for dt in dts:
            _datetimes.append(datetime.datetime(month=int(dt[0]), day=int(dt[1]), year=int('20' + dt[2])))
        self._datetimes = np.array(_datetimes)
        self._x = np.unique(_datetimes)

    @staticmethod
    def autocorrect_row_ordering_by_province(data_a, data_b):
        """

        """
        conditions = ((data_a[:, 1] != data_b[:, 1]) | (data_a[:, 0] != data_b[:, 0]))
        if np.any(conditions):
            loc = np.where(conditions)[0]
            mapping = dict(zip(np.arange(loc.size).astype(int), loc))
            for row in loc:
                swap_conditions = ((data_b[:, 1][loc] == data_a[:, 1][row]) & (data_b[:, 0][loc] == data_a[:, 0][row]))
                mapping_key = np.where(swap_conditions)[0]
                if len(mapping_key) != 0:
                    _row = mapping[mapping_key[0]]
                    data_b[[_row, row]] = data_b[[row, _row]]
        return data_a, data_b

    def load_data(self):
        _confirmed, _dead = self.autocorrect_row_ordering_by_province(self.raw_data['confirmed'], self.raw_data['dead'])
        _dead, _recovered = self.autocorrect_row_ordering_by_province(self.raw_data['dead'], self.raw_data['recovered'])
        _recovered, _confirmed = self.autocorrect_row_ordering_by_province(self.raw_data['recovered'], self.raw_data['confirmed'])
        self._countries = _confirmed[1:, 1]
        _provinces = _confirmed[1:, 0]
        _provinces[_provinces == ''] = 'N/A'
        county_indices = np.core.defchararray.find(_provinces, ',')
        _counties = ['N/A'] * county_indices.size
        US = UnitedStatesMapping()
        for i, (county_index, province) in enumerate(zip(county_indices, _provinces)):
            if county_index >= 0:
                try:
                    abbreviation = province[county_index+2:].strip()
                    _provinces[i] = US.abbreviation_to_name[abbreviation]
                    _counties[i] = province[:county_index]
                except:
                    if 'D.C.' in province:
                        _provinces[i] = 'District of Columbia'
                        _counties[i] = 'Washington'
                    else:
                        raise ValueError("not yet implemented")
        self._provinces = _provinces
        self._counties = np.array(_counties)
        self._longitudes = _confirmed[1:, 2].astype(float)
        self._latitudes = _confirmed[1:, 3].astype(float)
        self._confirmed = _confirmed[1:, 4:].astype(int)
        self._dead = _dead[1:, 4:].astype(int)
        self._recovered = _recovered[1:, 4:].astype(int)

    def load_regions(self):
        regions = dict()
        regions['country'] = self.countries
        regions['province'] = self.provinces
        regions['county'] = self.counties
        regions['longitude'] = self.longitudes
        regions['latitude'] = self.latitudes
        self._regions.update(regions)
        self._searchers['region'] = Searcher(regions)

    def load_timeseries(self):
        timeseries = dict()
        timeseries['confirmed'] = self.confirmed
        timeseries['dead'] = self.dead
        timeseries['recovered'] = self.recovered
        self._timeseries.update(timeseries)
        self._searchers['timeseries'] = Searcher(timeseries)

    def select_regions(self, parameters=None, conditions=None, values=None, apply_to='all', modifiers=None):
        """

        """
        S = self.searchers['region']
        indices = S.search_indices(parameters, conditions, values, apply_to, modifiers, axis=0)
        regions = {key : value[indices] for key, value in self.regions.items()}
        timeseries = {key : value[indices] for key, value in self.timeseries.items()}
        return regions, timeseries

    # def select_timeseries(self, parameters=None, conditions=None, values=None, apply_to='all', modifiers=None):
    #     """
    #
    #     """
    #     S = self.searchers['timeseries']
    #     raise ValueError("not yet implemented")

    def view_case_comparison(self, regions, timeseries, scale='linear', xmajor='month', xminor='day', xfmt="%Y-%m-%d", xrotation=15, facecolors='rgb', save=False, **kwargs):
        """

        """
        nc = len(facecolors)
        if nc != 3:
            raise ValueError("invalid number of facecolors: {}".format(nc))
        alpha = 1/nc
        for country, province, county, confirmed, dead, recovered in zip(regions['country'], regions['province'], regions['county'], timeseries['confirmed'], timeseries['dead'], timeseries['recovered']):
            fig, ax = plt.subplots(**kwargs)
            if county == 'N/A':
                if province == 'N/A':
                    title = '{}'.format(country)
                else:
                    title = '{}, {}'.format(province, country)
            else:
                title = '{}: {}, {}'.format(country, county, province)
            for y, label, facecolor, linestyle in zip((confirmed, dead, recovered), ('cofirmed', 'dead', 'recovered'), facecolors, ('-', '-.', '--')):
                ax.plot(self.x, y, color=facecolor, label=label, alpha=alpha, linestyle=linestyle)
            ax = self.transform_x_as_datetime(ax, xmajor, xminor, xfmt, xrotation)
            ax.set_xlabel('Date', fontsize=self.labelsize)
            ax.set_ylabel('Frequency of Cases', fontsize=self.labelsize)
            ax = self.update_y_scaling(ax, scale, base=10)
            ax.tick_params(axis='both', which='both', labelsize=self.ticksize)
            ax.grid(color='k', linestyle=':', alpha=0.3)
            ax.set_title(title, fontsize=self.titlesize)
            handles, labels = ax.get_legend_handles_labels()
            handles, labels, ncol = self.autocorrect_legend_entries(ax, handles, labels)
            kws = dict(handles=handles, labels=labels, ncol=ncol, mode='expand', loc='lower center', fontsize=self.labelsize, borderaxespad=0.1) #, scatterpoints=1)
            fig.subplots_adjust(bottom=0.325)
            leg = fig.legend(**kws)
            leg = self.update_legend_design(leg, title='Cases via CSSEGIS', textcolor='darkorange', facecolor='k', edgecolor='steelblue')
            plt.show()
            plt.close(fig)





#





















##
