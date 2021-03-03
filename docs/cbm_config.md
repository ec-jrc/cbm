# Configuration

To configure the main configuration file manually, run in the terminal:

```bash
python3 -c "import cbm"
nano config/main.json
```

The main configuration file for cbm library ‘main.json’ is used in all the subpackages:

```json
{
    "set": {}, // General configurations
    "paths": {}, // The data and temp path are configurable and can be changed globally
    "files": {}, // Location of files used it some functions
    "api": {}, // The RESTful API access information
    "db": {}, // Database access information
    "dataset": {}, // Dataset information and tables configuration
    "obst": {} // the object storage credentials
}
```

## Configuration widget
To configure the config/main.json file interactively, in the jupyterlab environment create a new notebook and run in a cell:

```python
# Import ipycbm
from cbm import ipycbm
# Open the configuration widget
ipycbm.config() 
```
![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_config_01.png)

