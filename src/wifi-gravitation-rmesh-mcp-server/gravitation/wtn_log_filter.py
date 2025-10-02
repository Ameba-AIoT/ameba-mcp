import re


def should_drop(log):
    # Check if the log contains "fix_rssi" at the beginning
    if log.startswith("wtn fix_rssi"):
        return True

    # Check for the presence of specific patterns in the log
    score_pattern = r"\[TN\-I\] gravitation show wtn_score:([\d\.\w, -]+)"
    father_mac_pattern = r"\[TN\-I\] gravitation show wtn_father:([\b\w:/]+)"
    heap_pattern = r"\[TN\-I\] wtn free heap:([\b\w:/]+)"

    if re.search(score_pattern, log) or re.search(father_mac_pattern, log) or re.search(heap_pattern, log):
        return True

    return False
