def get_era5(dataset_name='reanalysis-era5-single-levels',
             format="netcdf",
             product_type="reanalysis",
             var=['2m_temperature'],
             year=[
                 '2021'
             ],
             month=[
                 '01', '02', '03',
                 '04', '05', '06',
                 '07', '08', '09',
                 '10', '11', '12',
             ],
             day=[
                 '01', '02', '03',
                 '04', '05', '06',
                 '07', '08', '09',
                 '10', '11', '12',
                 '13', '14', '15',
                 '16', '17', '18',
                 '19', '20', '21',
                 '22', '23', '24',
                 '25', '26', '27',
                 '28', '29', '30',
                 '31'
             ],
             time=[
                 '00:00', '01:00', '02:00',
                 '03:00', '04:00', '05:00',
                 '06:00', '07:00', '08:00',
                 '09:00', '10:00', '11:00',
                 '12:00', '13:00', '14:00',
                 '15:00', '16:00', '17:00',
                 '18:00', '19:00', '20:00',
                 '21:00', '22:00', '23:00',
             ],
             grid=[0.25, 0.25],
             area=[71, -25, 33, 40],  # Europe's boundaries
             download_file='output.nc',
             ):
    """
    The Climate Data Store Application Program Interface is a service providing
    programmatic access to CDS data.

    this script grabs ERA5 variables from the web and stores them
    in a xarray dataset.

    the ERA5 CDS API must be installed and configured on the local machine.
    Install and config: https://cds.climate.copernicus.eu/api-how-to

    Parameters
    ==========
    dataset_name: str, default 'reanalysis-era5-single-levels'
        name of dataset.
        Options:
        - 'reanalysis-era5-single-levels'
        - 'reanalysis-era5-single-levels-monthly-means'
        - 'reanalysis-era5-pressure-levels' <-- asks pressure as parameter,
        - 'reanalysis-era5-pressure-levels-monthly-means' <-- asks pressure as parameter
        - 'reanalysis-era5-land'
        - 'reanalysis-era5-land-monthly-means'
    format: str, default 'netcdf'
        format of files to be downloaded.
        Available formats: 'grib', 'netcdf'
    product_type: str, default 'reanalysis'
        product type to be downloaded.
        available product types catalog :
            'reanalysis', 'ensemble_members', 'ensemble_mean', 'ensemble_catalog'
    var: list of str, default ['2m_temperature']
        name of variable to be downloaded
        example ['2m_temperature' ,'total_precipitation']
    year: list of str, default ['2021']
    month: list of str, default ['01', '02', ..., '12']
    day: list of str, default ['01', '02', ..., '31']
    time list of str, default ['00:00', '01:00', ... , '23:00']
    grid: list of float, default [0.25, 0.25]
        spatial lat lon grid resolution in deg
    area: list, default [71, -25, 33, 40]
        area extent download [N, W, S, E] default is Europe boundaries
        [90,-180,-90, 180] for planet earth
    download_file= str, default './output.nc'
        path to where data should be downloaded to.
    read_file= bool, default False
        mark as true if you want to read the file directly after download
    ============
    Example
    ============
    ds = get_era5(dataset_name='reanalysis-era5-single-levels',
                 var='2m_temperature',
                 year='2020',
                 month='01',
                 grid=[0.25, 0.25])
    ==========
    Notes
    ==========
    # cdsapi code is here
    https://github.com/ecmwf/cdsapi/tree/master/cdsapi
    # information on api is here
    https://confluence.ecmwf.int/display/CKB/Climate+Data+Store+%28CDS%29+API+Keywords
    # era5 dataset information is here
    https://confluence.ecmwf.int/display/CKB/The+family+of+ERA5+datasets
    https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation
    """

    import cdsapi
    import xarray as xr

    # start the cdsapi client
    c = cdsapi.Client()

    # parameters
    params = dict(
        format=format,
        product_type=product_type,
        variable=var,
        grid=grid,
        area=area,
        year=year,
        month=month,
        day=day,
        time=time,
    )

    # file object
    c.retrieve(dataset_name, params, download_file)
