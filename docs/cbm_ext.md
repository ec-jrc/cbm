# Extraction



If not configured already, the database and object storage credentials can be set with:
```python
# Import the cbm python library
import cbm

# Add the databse credentials
db_host = 'http://0.0.0.0'
db_port = '5432'
db_name = 'postgres'
db_user = 'postgres'
db_pass = ''
cbm.config.set_value(['db', 'main', 'host'], db_host)
cbm.config.set_value(['db', 'main', 'port'], db_port)
cbm.config.set_value(['db', 'main', 'name'], db_name)
cbm.config.set_value(['db', 'main', 'user'], db_user)
cbm.config.set_value(['db', 'main', 'pass'], db_pass)

# Add the object store credentials. Should be given from the DIAS provider.
osdias = ''     # The name of the dias provider
oshost = ''     # The host address
bucket = ''     # The bucket name
access_key = '' # The access key of the object store
secret_key = '' # The secret key of the object store
cbm.config.set_value(['obst', 'osdias'], osdias)
cbm.config.set_value(['obst', 'oshost'], oshost)
cbm.config.set_value(['obst', 'bucket'], bucket)
cbm.config.set_value(['obst', 'access_key'], access_key)
cbm.config.set_value(['obst', 'secret_key'], secret_key)
```

This can be done manually as well by opening the config/main.json file.


If the credentials are set properly the extractions can be done with:
```python
import cbm

start_date = '2019-06-01'
end_date = '2019-06-30'
dias_catalogue = 'aoi2019_dias_catalogue'
parcels_table = 'aoi2019'
results_table = 'aoi2019_s2_signatures'
dias = 'dias'

cbm.extract.s2(startdate, enddate, dias_catalogue, parcels_table, results_table, dias)
```


## Extract widget

This widget provides the credentials configuration widget as well

```python
from cbm import ipycbm
ipycbm.extract()
```

![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_extract_01.png)
