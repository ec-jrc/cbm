# DIAS catalog

**Transfer metadata from the DIAS catalog**

Each DIAS maintains a catalog of the Level 1 and Level 2 CARD data sets available in the S3 store. Even with the use of standard catalog APIs (e.g. OpenSearch), the actual metadata served by the catalog may contain different, or differently named, attributes. Thus, in order to minimize portability issues, we implement a metadata transfer step, which makes metadata available in a single, consistent, database table dias_catalogue across the various DIAS instances. (see [data_preparation](https://jrc-cbm.readthedocs.io/en/latest/data_preparation.html#transfer-metadata-from-the-dias-catalog) for more information)

**(Under development)**

```python
import cbm

tb_prefix = 'aoi2019' # The database table prefix
aoi = 'aoi'           # Area of interest e.g.: es, nld (str)
start = '2019-06-01'  # Start date (str)
end = '2019-06-30'    # End date (str)
card = 's2'           # s2, c6 or bs
option = 'LEVEL2A'    # s1 ptype CARD-COH6 or CARD-BS, s2 plevel : LEVEL2A or LEVEL2AP

cbm.card2db.creodias(tb_prefix, aoi, start, end, card, option)
```

Other DIAS options (future implementations):

- CREODIAS
- MUNDI
- SOBLOO
- WEkEO
- ONDA

## Notebook widget

```python
from cbm import ipycbm
ipycbm.card2db()
```

![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_card2db_01.png)
