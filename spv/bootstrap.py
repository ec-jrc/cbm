import urllib.request
import os
from pathlib import Path
import sys
import subprocess

def ensure_correct_workdir():
    current_dir = Path.cwd()

    # Only run the notebook-dir detection logic
    # if we are in the default Jupyter root
    if current_dir == Path("/home/jovyan"):
        print("Detected default Jupyter root. Resolving real notebook directory...")

        # ---- your existing function ----
        import json
        import urllib.request
        import ipykernel

        def notebook_dir_jupyterhub() -> Path:
            connection_file = Path(ipykernel.get_connection_file()).name
            kernel_id = connection_file.split("-", 1)[1].split(".", 1)[0]

            server_url = os.environ["JUPYTERHUB_SERVICE_URL"].rstrip("/")
            token = os.environ["JUPYTERHUB_API_TOKEN"]

            sessions_url = f"{server_url}/api/sessions"

            req = urllib.request.Request(sessions_url)
            req.add_header("Authorization", f"token {token}")

            with urllib.request.urlopen(req) as resp:
                sessions = json.loads(resp.read().decode("utf-8"))

            for s in sessions:
                if s.get("kernel", {}).get("id") == kernel_id:
                    nb_path = (s.get("notebook") or {}).get("path") or s.get("path")
                    nb_path = nb_path[4:]
                    return Path(nb_path).parent

            raise RuntimeError("Could not match current kernel id to session.")

        new_dir = notebook_dir_jupyterhub()
        os.chdir(new_dir)
        print(f"Working directory set to: {new_dir}")

    else:
        print(f"Working directory already correct: {current_dir}")
        

def download_if_missing(filename, url):
    file_path = Path(filename)

    if file_path.exists():
        return

    try:
        urllib.request.urlretrieve(url, filename)
    except Exception as e:
        print(f"❌ Failed to download {filename}")
        print(e)

ensure_correct_workdir()

# FILE LIST TO DOWNLOAD
# https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/SentinelParcelViewer/

FILES = {
    #"bootstrap.py": "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/bootstrap.py",
    "csv_graphs_utils.py" : "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/csv_graphs_utils.py",
    "ncdf_graph_utils.py" : "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/ncdf_graph_utils.py",
    "netcdf_utils.py" : "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/netcdf_utils.py",
    "openeo_utils.py" : "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/openeo_utils.py",
    "plot_utils.py" : "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/plot_utils.py",
    "requirements.txt" : "https://raw.githubusercontent.com/ec-jrc/cbm/refs/heads/main/spv/requirements.txt",
}

print("Downloading files...")

for fname, url in FILES.items():
    download_if_missing(fname, url)

print("Downloads completed.")

print("Checking and installing dependencies...")

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
    check=True
)

print("Installs completed. You can now run the next cell to authenticate.")