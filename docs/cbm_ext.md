# Extraction

```python
import cbm

start_date = '2019-06-01'
end_date = '2019-06-30'
dias_catalogue = 'aoi2019_dias_catalogue'
parcels_table = 'aoi2019'
results_table = 'aoi2019_s2_signatures'
dias = 'dias'

cbm.extract.S2(startdate, enddate, dias_catalogue, parcels_table, results_table, dias)
```