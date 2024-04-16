import ipywidgets as widgets
import time
from IPython.display import display

def print_progress(buckets):
    strtoprint = ""
    for bucket_id, bucket in buckets.items():
        total = bucket["target"]
        current = len(bucket["parcels"])
        if current >= total:  # 100% done, use green color
            strtoprint += "\033[92m" + str(bucket_id) + ": " + str(current) + "/" + str(total) + "\033[0m | "
        else:  # Not done, use yellow color
            strtoprint += "\033[93m" + str(bucket_id) + ": " + str(current) + "/" + str(total) + "\033[0m | "
    max_line_length = 300
    print(strtoprint.ljust(max_line_length) + "\r", end="", flush=True)


def show_progress_bars(buckets):
    all_progress_bars = []
    for bucket_id, bucket in buckets.items():
        total = bucket["target"]
        current = len(bucket["parcels"])
        progress = widgets.FloatProgress(value=current, min=0, max=total, description=str(bucket_id))
        all_progress_bars.append(progress)
    display(*all_progress_bars)
    return all_progress_bars


def update_progress_bars(buckets, progress_bars):
    print(buckets)
    print(progress_bars)
    for progress_bar in progress_bars:
        pb_id = int(progress_bar.description)
        current = len(buckets[pb_id]["parcels"])
        progress_bar.value = current
