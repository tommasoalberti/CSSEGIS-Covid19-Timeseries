# CSSEGIS-Covid19-Timeseries

Minimum Requirements:

    Python 3.5.2
    
    --> numpy==1.15.0
    
    --> matplotlib==2.2.2

**Synopsis:**

The 2019-2020 Coronavirus Pandemic is an ongoing global pandemic. The data, which was made publically available by [JHU CSSE](https://github.com/CSSEGISandData/COVID-19) and is updated daily, consists of multiple daily timeseries by case (confirmed, death, and recovery). One way to pass some time while staying home during this outbreak is to play with some data.

**Example:**

Make sure to specify `directory` that contains the folders `Data`, `PyCodes`, and `Figures`. The methods in the constructor of `DataBase` are used to load data from each of the files into dictionaries such that all key-value pairs match by row index. Data corresponding to empty fields are replaced with `'N/A'` or `'NaN'` where appropriate. 

    from data_processing import *

    directory = '/Users/.../'
    DB = DataBase(directory)

Then, one can obtain data that corresponds to input search criteria. For example, say we want to obtain all timeseries data about Japan.

    regions, timeseries = DB.select_regions(parameters='country', conditions='equal', values='Japan')

One can generate a plot that compares frequencies by case type (`'confirmed'`, `'dead'`, and `'recovered'`) for each location that specifies the search criteria. Since only one row of each file corresponds to Japan, the functions below will only output one figure. If not specified, `scale` is assumed to be linear. The default value of `save` is `False`; if `True`, this will save each figure in the `Figures` directory.

    DB.view_case_comparisons_by_location(regions, timeseries)
    
![Example: Japan via linear scale](https://i.imgur.com/sA7o8si.png)

One can insert multiple search criteria such that multiple regions are selected. It should be noted that an error will be raised if the search criteria is not satisfied.

    regions, timeseries = DB.select_regions(parameters='country', conditions='equal', values=('Armenia', 'Iceland', 'Greece', 'Egypt', 'Italy', 'Japan', 'Germany', 'Turkey'))
    > ValueError: no matches found

This can be accounted for by specifying `apply_to='any'` (default is `'all'`).

    regions, timeseries = DB.select_regions(parameters='country', conditions='equal', values=('Armenia', 'Iceland', 'Greece', 'Egypt', 'Italy', 'Japan', 'Germany', 'Turkey'), apply_to='any')
    
    ## same as
    # values = ('Armenia', 'Iceland', 'Greece', 'Egypt', 'Italy', 'Japan', 'Germany', 'Turkey')
    # parameters = ['country' for v in values]
    # conditions = ['equal' for v in values]
    # regions, timeseries = DB.select_regions(parameters=parameters, conditions=conditions, values=values, apply_to='any')
    ##
    
    # print("\n ** REGIONS **\n")
    # for k,v in regions.items():
    #     print("\n .. {} (dtype={}, shape={}):\n{}\n".format(k, v.dtype, v.shape, v))
    # 
    # print("\n ** TIMESERIES **\n")
    # for k,v in regions.items():
    #     print("\n .. {} (dtype={}, shape={}):\n{}\n".format(k, v.dtype, v.shape, v))


The plot routine above will create a separate figure for each location. We can also view all selected regions simultaneously. The default value of `save` is `False`; if `True`, this will save each figure in the `Figures` directory.

    # DB.view_case_comparisons_by_location(regions, timeseries, save=True)
    DB.view_case_comparisons_by_location(regions, timeseries, scale='log', save=True)

![Example: Multiple countries via log scale](https://i.imgur.com/NoPDaYv.png)

Similar logic can be applied to search for other locations using other parameters. These regional parameters are: `'country'`, `'province'` (do not use `'state'`), `'county'`, `'longitude'`, and `'latitude'`; the timeseries search methods are not yet implemented. One can also combine `regions` and `timeseries` with other `regions` and `timeseries`. 

    r1, t1 = DB.select_regions(parameters=('longitude', 'longitude', 'latitude', 'latitude', 'county'), conditions=('greater than', 'less than', 'greater than', 'less than or equal', 'equal'), values=(30, 45, -145, -115, 'N/A'))
    r2, t2 = DB.select_regions(parameters=('province', 'county'), conditions='equal', values=('New York', 'N/A'))
    r3, t3 = DB.select_regions(parameters=('province', 'county'), conditions='equal', values=('Colorado', 'N/A'))
    r4, t4 = DB.select_regions(parameters=('province', 'county'), conditions='equal', values=('Texas', 'N/A'))
    r5, t5 = DB.select_regions(parameters=('province', 'county'), conditions='equal', values=('Washington', 'N/A'))
    r6, t6 = DB.select_regions(parameters=('province', 'county'), conditions='equal', values=('Oregon', 'N/A'))
    regions, timeseries = DB.combine_data([r1, r2, r3, r4, r5, r6], [t1, t2, t3, t4, t5, t6])

    # DB.view_case_comparisons_by_location(regions, timeseries, save=True)
    DB.view_case_comparisons_by_location(regions, timeseries, scale='log', save=True)
    # DB.view_case_comparisons_per_location(regions, timeseries, save=True)
    # DB.view_case_comparisons_per_location(regions, timeseries, scale='log', save=True)
    
![Example: Multiple states and bottom of Canada via log scale](https://i.imgur.com/QVWd0zc.png)





