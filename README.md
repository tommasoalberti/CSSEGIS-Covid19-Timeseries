# CSSEGIS-Covid19-Timeseries

Minimum Requirements:

    Python 3.5.2
    
    --> numpy==1.15.0
    
    --> matplotlib==2.2.2

**Synopsis:**

The 2019-2020 Coronavirus Pandemic is an ongoing global pandemic. The data, which was made publically available by [JHU CSSE](https://github.com/CSSEGISandData/COVID-19) and is updated daily, consists of multiple daily timeseries by case (confirmed, death, and recovery). 

Counterintuitively, the ordering of the rows of each file do not necessarily correspond to the ordering of the rows in the other files; this ordering also changes with each daily update. To make matters more confusing, one can find find multiple representations of the same locations in these files. For example, each of the publically provided files contains a row pertaining to `State/Province: California` and `County: ''`, yet the `State/Province` will be `CA` for every non-empty `county`. 

The purpose of this code is to simplify the structure of the provided data to be less counterintuitive; it may evolve into an exploratory analysis in the future. 

**Example:**

Make sure to specify `directory` that contains the folders `Data` and `PyCodes`. The methods in the constructor of `DataBase` are used to load data from each of the files into dictionaries such that all key-value pairs match by row index. Data corresponding to empty fields are replaced with `'N/A'` or `'NaN'` where appropriate. 

    from data_processing import *

    directory = '/Users/.../'
    DB = DataBase(directory)

Then, one can obtain data that corresponds to input search criteria. For example, say we want to obtain all timeseries data about Japan.

    regions, timeseries = DB.select_regions(parameters='country', conditions='equal', values='Japan')

One can generate a plot that compares frequencies by case type (`'confirmed'`, `'dead'`, and `'recovered'`) for each location that specifies the search criteria. Since only one row of each file corresponds to Japan, the functions below will only output one figure. If not specified, `scale` is assumed to be linear.

    DB.view_case_comparison(regions, timeseries)
![Example: Japan via linear scale](https://images2.imgbox.com/e7/e7/MQCvHXav_o.png)
    
We can also view the same data using semi-log scaling.

    DB.view_case_comparison(regions, timeseries, scale='log')

![Example: Japan via semi-log scale](https://images2.imgbox.com/6b/b3/SGiBZzqV_o.png)


One can insert multiple search criteria. It should be noted that an error will be raised if the search criteria is not satisfied.

    regions, timeseries = DB.select_regions(parameters='country', conditions='equal', values=('Japan', 'Italy'))
    ValueError: no matches found

This can be accounted for by specifying `apply_to='any'` (default is `'all'`).

    regions, timeseries = DB.select_regions(parameters='country', conditions='equal', values=('Japan', 'Italy'), apply_to='any')

Note that `parameters='country'` and `conditions='equal'` are applied to both `'Japan'` and `'Italy'` in `values`; alternatively, one could obtain the same output by:

    regions, timeseries = DB.select_regions(parameters=('country', 'country'), conditions=('equal', 'equal'), values=('Japan', 'Italy'), apply_to='any')

The calls to `DB.view_case_comparison` shown below will output a separate figure for Japan and Italy, respectively.

    DB.view_case_comparison(regions, timeseries)

![Example: Italy via linear scale](https://images2.imgbox.com/78/e8/W67OS1YL_o.png)

    DB.view_case_comparison(regions, timeseries, scale='log')

![Example: Italy via semi-log scale](https://images2.imgbox.com/1b/33/0LrPnAqg_o.png)

This logic can be also be applied to other regional parameters; I plan to implement a search-by-timeseries functionality. These regional parameters are: `'country'`, `'province'` (do not use `'state'`), `'county'`, `'longitude'`, and `'latitude'`. 

