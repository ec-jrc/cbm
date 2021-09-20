# Configuration

The main configurations for cbm are stored in the config/main.json file

To easily set the RESTful API account use:
```python
cbm.set_api_account('http://0.0.0.0/', 'YOUR_USERNAME', 'YOUR_PASSWORD')
```
The account credentials will be stored automatically in the config/main.json file

You can configure the main configuration file (config/main.json) with a text editor of your choice. e.g.:
```bash
python3 -c "import cbm"
nano config/main.json
```

The main json configuration file has different sectors to store the settings for cbm:
```json
{
    "set": {}, // General configurations
    "paths": {}, // The data and temp path are configurable and can be changed globally
    "files": {}, // Location of files used it some functions
    "api": {}, // The RESTful API credentials
    "db": {}, // Database access information (only if direct access is available)
    "s3": {} // the object storage credentials (only if direct access is available)
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

