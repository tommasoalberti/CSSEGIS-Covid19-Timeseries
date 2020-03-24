from condition_mapping import *
from visual_configuration import *

import os
import datetime
import csv

class DataBase(VisualConfiguration):

    def __init__(self, directory, ticksize=7, labelsize=8, textsize=5, titlesize=9, headersize=10, cellsize=15):
        """

        """
        super().__init__(directory, ticksize, labelsize, textsize, titlesize, headersize, cellsize)
        self.source = dict(CSSE='https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data')
        self.path_confirmed = '{}Data/time_series_19-covid-Confirmed.csv'.format(directory)
        self.path_dead = '{}Data/time_series_19-covid-Deaths.csv'.format(directory)
        self.path_recovered = '{}Data/time_series_19-covid-Recovered.csv'.format(directory)
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

    @staticmethod
    def autocorrect_timeseries(timeseries):
        condition = (timeseries == '')
        timeseries[condition] = 'NaN'
        return timeseries.astype(float)

    @staticmethod
    def get_region_name(country, province, county):
        """

        """
        if county == 'N/A':
            if province == 'N/A':
                s = '{}'.format(country)
            else:
                s = '{}, {}'.format(province, country)
        else:
            s = '{}: {}, {}'.format(country, county, province)
        return s

    @staticmethod
    def get_file_modification_timestamp(path):
        """

        """
        t = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(t)

    def get_consolidated_file_timestamps(self, max_seconds=120):
        """

        """
        if max_seconds < 0:
            raise ValueError("max_seconds must be greater than or equal to zero")
        dt_confirmed = self.get_file_modification_timestamp(self.path_confirmed)
        dt_dead = self.get_file_modification_timestamp(self.path_dead)
        dt_recovered = self.get_file_modification_timestamp(self.path_recovered)
        deltas = np.array([dt.total_seconds() for dt in np.diff([dt_confirmed, dt_dead, dt_recovered])])
        # 'updated' -->? 'modified'
        if np.all(deltas == 0):
            s = 'last updated: {}'.format(dt_confirmed)
        elif np.all(deltas <= max_seconds):
            s = 'last updated: {}, {}, {}'.format(dt_confirmed, dt_dead, dt_recovered)
        else:
            raise ValueError("files were last updated more than {} seconds apart".format(max_seconds))
        return s

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
        self._confirmed = self.autocorrect_timeseries(_confirmed[1:, 4:])
        self._dead = self.autocorrect_timeseries(_dead[1:, 4:])
        self._recovered = self.autocorrect_timeseries(_recovered[1:, 4:])

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

    def select_timeseries(self, parameters=None, conditions=None, values=None, apply_to='all', modifiers=None):
        """

        """
        S = self.searchers['timeseries']
        raise ValueError("not yet implemented")

    def combine_data(self, regions, timeseries):
        """

        """
        _regions = {key : [] for key in list(self.regions.keys())}
        _timeseries = {key : [] for key in list(self.timeseries.keys())}
        for region in regions:
            for key, value in region.items():
                _regions[key].extend(value.tolist())
        for series in timeseries:
            for key, value in series.items():
                _timeseries[key].extend(value.tolist())
        _regions = {key : np.array(value) for key, value in _regions.items()}
        _timeseries = {key : np.array(value) for key, value in _timeseries.items()}
        return _regions, _timeseries

    def view_case_comparisons_per_location(self, regions, timeseries, scale='linear', xmajor='month', xminor='day', xfmt="%Y-%m-%d", xrotation=15, facecolors='rgb', save=False, **kwargs):
        """

        """
        nc = len(facecolors)
        if nc != 3:
            raise ValueError("invalid number of facecolors: {}".format(nc))
        alpha = 1/nc
        for country, province, county, confirmed, dead, recovered in zip(regions['country'], regions['province'], regions['county'], timeseries['confirmed'], timeseries['dead'], timeseries['recovered']):
            fig, ax = plt.subplots(**kwargs)
            title = self.get_region_name(country, province, county)
            for y, label, facecolor, linestyle in zip((confirmed, dead, recovered), ('Confirmed', 'Dead', 'Recovered'), facecolors, ('-', '-.', '--')):
                condition = (y > 0)
                if scale == 'linear':
                    ax.plot(self.x[condition], y[condition], color=facecolor, label=label, alpha=alpha, linestyle=linestyle)
                else:
                    # ax.semilogy(self.x[condition], y[condition], color=facecolor, label=label, alpha=alpha, linestyle=linestyle)
                    ax.plot(self.x[condition], y[condition], color=facecolor, label=label, alpha=alpha, linestyle=linestyle)
            ax = self.transform_x_as_datetime(ax, xmajor, xminor, xfmt, xrotation)
            ax.set_xlabel('Date', fontsize=self.labelsize)
            ax.set_ylabel('Frequency of Cases', fontsize=self.labelsize)
            ax = self.update_y_scaling(ax, scale)
            ax.tick_params(axis='both', which='both', labelsize=self.ticksize)
            ax.grid(color='k', linestyle=':', alpha=0.3)
            ax.set_xlim([self.x[0], self.x[-1]])
            ax.set_title(title, fontsize=self.titlesize)
            handles, labels = ax.get_legend_handles_labels()
            handles, labels, ncol = self.autocorrect_legend_entries(ax, handles, labels)
            suffix = self.get_consolidated_file_timestamps(max_seconds=120)
            kws = dict(handles=handles, labels=labels, ncol=ncol, mode='expand', loc='lower center', fontsize=self.labelsize, borderaxespad=0.1)
            fig.subplots_adjust(bottom=0.325)
            leg = fig.legend(**kws)
            leg = self.update_legend_design(leg, title='Cases via CSSEGIS/JHU ({})'.format(suffix), textcolor='darkorange', facecolor='k', edgecolor='steelblue')
            if save:
                savename = 'per_{}'.format(title.title().replace(' ', '')) + '__{}'.format(scale)
            else:
                savename = None
            self.display_image(fig, savename)

    def view_case_comparisons_by_location(self, regions, timeseries, scale='linear', xmajor='month', xminor='day', xfmt="%Y-%m-%d", xrotation=15, cmap='jet_r', linestyles=(['-', ':']), save=False, **kwargs):
        """

        """
        norm = Normalize(vmin=0, vmax=regions['province'].size)
        vector = np.arange(regions['province'].size).astype(int)
        facecolors = self.get_facecolors_from_cmap(cmap, norm, vector)
        linestyles = self.generate_linestyle_cycle(linestyles)
        alpha = self.autocorrect_transparency(1/vector.size)
        location_labels = []
        fig, axes = plt.subplots(nrows=4, ncols=1, **kwargs)
        axes[-1].axis('off')
        for country, province, county, confirmed, dead, recovered, facecolor in zip(regions['country'], regions['province'], regions['county'], timeseries['confirmed'], timeseries['dead'], timeseries['recovered'], facecolors):
            location_label = self.get_region_name(country, province, county)
            location_labels.append(location_label)
            linestyle = next(linestyles)
            for i, (ax, y) in enumerate(zip(axes.ravel(), (confirmed, dead, recovered))):
                condition = (y > 0)
                label = location_label if i == 0 else None
                if scale == 'linear':
                    ax.plot(self.x[condition], y[condition], color=facecolor, alpha=alpha, linestyle=linestyle, label=label)
                else:
                    # ax.semilogy(self.x[condition], y[condition], color=facecolor, alpha=alpha, linestyle=linestyle, label=label)
                    ax.plot(self.x[condition], y[condition], color=facecolor, alpha=alpha, linestyle=linestyle, label=label)
        for i, (ax, title) in enumerate(zip(axes[:-1].ravel(), ('Confirmed', 'Dead', 'Recovered'))):
            ax = self.transform_x_as_datetime(ax, xmajor, xminor, xfmt, xrotation)
            if i in (0, 1):
                ax.set_xticklabels([], fontsize=self.ticksize)
            ax = self.update_y_scaling(ax, scale)
            ax.tick_params(axis='both', which='both', labelsize=self.ticksize)
            ax.grid(color='k', linestyle=':', alpha=0.3)
            ax.set_xlim([self.x[0], self.x[-1]])
            ax.set_title(title, fontsize=self.titlesize)
        axes[2].set_xlabel('Date', fontsize=self.labelsize)
        axes[1].set_ylabel('Frequency of Cases', fontsize=self.labelsize)
        handles, labels, ncol = self.autocorrect_legend_entries(axes[-1], *axes[0].get_legend_handles_labels())
        suffix = self.get_consolidated_file_timestamps(max_seconds=120)
        kws = dict(handles=handles, labels=labels, ncol=ncol, mode='expand', loc='lower center', fontsize=self.labelsize, borderaxespad=0.1)
        fig.subplots_adjust(hspace=0.375)
        leg = fig.legend(**kws)
        leg = self.update_legend_design(leg, title='Cases via CSSEGIS/JHU ({})'.format(suffix), textcolor='darkorange', facecolor='k', edgecolor='steelblue')
        fig.align_ylabels()
        if save:
            savename = "_".join(sorted(location_labels)).title().replace(' ', '') + '__{}'.format(scale)
        else:
            savename = None
        self.display_image(fig, savename)
        # try:
        #     self.display_image(fig, savename)
        # except OSError as e:
        #     savename = 'multiple_locations__{}'.format(scale)
        #     self.display_image(fig, savename)
        # else:
        #     raise ValueError("see VisualConfiguration.display_image")

    # def view_case_comparisons_by_location(self, regions, timeseries, scale='linear', xmajor='month', xminor='day', xfmt="%Y-%m-%d", xrotation=15, cmap='jet_r', linestyles=(['-', ':']), save=False, **kwargs):
    #     """
    #
    #     """
    #     norm = Normalize(vmin=0, vmax=regions['province'].size)
    #     vector = np.arange(regions['province'].size).astype(int)
    #     facecolors = self.get_facecolors_from_cmap(cmap, norm, vector)
    #     linestyles = self.generate_linestyle_cycle(linestyles)
    #     alpha = self.autocorrect_transparency(1/vector.size)
    #     location_labels = []
    #     fig, axes = plt.subplots(nrows=4, ncols=1, **kwargs)
    #     for country, province, county, confirmed, dead, recovered, facecolor in zip(regions['country'], regions['province'], regions['county'], timeseries['confirmed'], timeseries['dead'], timeseries['recovered'], facecolors):
    #         location_label = self.get_region_name(country, province, county)
    #         location_labels.append(location_label)
    #         linestyle = next(linestyles)
    #         for i, (ax, y) in enumerate(zip(axes.ravel(), (confirmed, dead, recovered))):
    #             condition = (y > 0)
    #             if i == 0:
    #                 ax.plot(self.x[condition], y[condition], color=facecolor, alpha=alpha, linestyle=linestyle, label=location_label)
    #             else:
    #                 ax.plot(self.x[condition], y[condition], color=facecolor, alpha=alpha, linestyle=linestyle)
    #     for i, (ax, title) in enumerate(zip(axes[:-1].ravel(), ('Confirmed', 'Dead', 'Recovered'))):
    #         ax = self.transform_x_as_datetime(ax, xmajor, xminor, xfmt, xrotation)
    #         ax = self.update_y_scaling(ax, scale)
    #         if i in (0, 1):
    #             ax.set_xticklabels([], fontsize=self.ticksize)
    #         ax.tick_params(axis='both', which='both', labelsize=self.ticksize)
    #         ax.set_xlim([self.x[0], self.x[-1]])
    #         ax.grid(color='k', linestyle=':', alpha=0.3)
    #         ax.set_title(title, fontsize=self.titlesize)
    #     axes[2].set_xlabel('Date', fontsize=self.labelsize)
    #     axes[1].set_ylabel('Frequency of Cases', fontsize=self.labelsize)
    #     axes[-1].axis('off')
    #     handles, labels, ncol = self.autocorrect_legend_entries(axes[-1], *axes[0].get_legend_handles_labels())
    #     suffix = self.get_consolidated_file_timestamps(max_seconds=120)
    #     kws = dict(handles=handles, labels=labels, ncol=ncol, mode='expand', loc='lower center', fontsize=self.labelsize, borderaxespad=0.1)
    #     fig.subplots_adjust(hspace=0.4)
    #     leg = fig.legend(**kws)
    #     leg = self.update_legend_design(leg, title='Cases via CSSEGIS/JHU ({})'.format(suffix), textcolor='darkorange', facecolor='k', edgecolor='steelblue')
    #     fig.align_ylabels()
    #     if save:
    #         savename = "_".join(sorted(location_labels)).title().replace(' ', '') + '__{}'.format(scale)
    #     else:
    #         savename = None
    #     self.display_image(fig, savename)

    # def view_case_comparisons_per_location(self, regions, timeseries, scale='linear', xmajor='month', xminor='day', xfmt="%Y-%m-%d", xrotation=15, facecolors='rgb', save=False, **kwargs):
    #     """
    #
    #     """
    #     nc = len(facecolors)
    #     if nc != 3:
    #         raise ValueError("invalid number of facecolors: {}".format(nc))
    #     alpha = 1/nc
    #     for country, province, county, confirmed, dead, recovered in zip(regions['country'], regions['province'], regions['county'], timeseries['confirmed'], timeseries['dead'], timeseries['recovered']):
    #         fig, ax = plt.subplots(**kwargs)
    #         title = self.get_region_name(country, province, county)
    #         for y, label, facecolor, linestyle in zip((confirmed, dead, recovered), ('Confirmed', 'Dead', 'Recovered'), facecolors, ('-', '-.', '--')):
    #             condition = (y > 0)
    #             ax.plot(self.x[condition], y[condition], color=facecolor, label=label, alpha=alpha, linestyle=linestyle)
    #         ax = self.transform_x_as_datetime(ax, xmajor, xminor, xfmt, xrotation)
    #         ax.set_xlabel('Date', fontsize=self.labelsize)
    #         ax.set_ylabel('Frequency of Cases', fontsize=self.labelsize)
    #         ax = self.update_y_scaling(ax, scale)
    #         ax.tick_params(axis='both', which='both', labelsize=self.ticksize)
    #         ax.grid(color='k', linestyle=':', alpha=0.3)
    #         ax.set_title(title, fontsize=self.titlesize)
    #         handles, labels = ax.get_legend_handles_labels()
    #         handles, labels, ncol = self.autocorrect_legend_entries(ax, handles, labels)
    #         suffix = self.get_consolidated_file_timestamps(max_seconds=120)
    #         kws = dict(handles=handles, labels=labels, ncol=ncol, mode='expand', loc='lower center', fontsize=self.labelsize, borderaxespad=0.1)
    #         fig.subplots_adjust(bottom=0.325)
    #         leg = fig.legend(**kws)
    #         leg = self.update_legend_design(leg, title='Cases via CSSEGIS/JHU ({})'.format(suffix), textcolor='darkorange', facecolor='k', edgecolor='steelblue')
    #         if save:
    #             savename = 'per_{}'.format(title.title().replace(' ', '')) + '__{}'.format(scale)
    #         else:
    #             savename = None
    #         self.display_image(fig, savename)


















#
