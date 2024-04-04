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