import logging
import re
import threading
import time
import traceback

from ping3 import ping, errors


class PingMonitor:
    def __init__(self, ip_address, callback, icmp_packet_size=32, interval=1000, ping_timeout_sec=2):
        self.thread = None
        self.ip_address = ip_address
        self.success_count = 0
        self.failure_count = 0
        self.stop_event = threading.Event()
        self.callback = callback  # Callback function for UI updates
        self.icmp_packet_size = icmp_packet_size
        self.interval = interval / 1000.0
        self.ping_timeout_sec = ping_timeout_sec

    def _ping_ip(self):
        try:
            logging.info(f"Start to ping {self.ip_address} with packet size {self.icmp_packet_size}"
                         f" bytes and interval {self.interval * 1000} ms.")
            next_ping_time = time.perf_counter()
            while not self.stop_event.is_set():
                current_time = time.perf_counter()
                if current_time >= next_ping_time:
                    # Check if missed the scheduled ping time
                    if current_time > next_ping_time + self.interval:
                        missed_intervals = int((current_time - next_ping_time) / self.interval)
                        time_difference_ms = (current_time - next_ping_time) * 1000
                        logging.info(
                            f"\033[31mWarning: {self.ip_address} missed the scheduled ping time by {time_difference_ms:.3f} ms, missed {missed_intervals} intervals.\033[0m")

                    try:
                        start_time = current_time  # Record the start time
                        logging.info(f"Start pinging {self.ip_address}")
                        latency = ping(self.ip_address, unit='ms', size=self.icmp_packet_size,
                                       timeout=self.ping_timeout_sec)
                        logging.info(f"Ping {self.ip_address} latency {latency} ms")
                        if self.stop_event.is_set():
                            return

                        if latency is not None:
                            #logging.info(f"Ping latency {latency}")
                            self.success_count += 1
                            self.callback(self.ip_address, "Success", latency, None, self.success_count,
                                          self.failure_count,
                                          start_time)
                        else:
                            self.failure_count += 1
                            self.callback(self.ip_address, "Failed", None, None, self.success_count, self.failure_count,
                                          start_time)
                    except errors.Timeout:
                        logging.error(f"Ping {self.ip_address} timeout")
                        if self.stop_event.is_set():
                            return
                        self.failure_count += 1
                        self.callback(self.ip_address, "Failed", None, None, self.success_count, self.failure_count,
                                      start_time)
                    except Exception as e:
                        logging.error(f"Error occurred during pinging {self.ip_address}: {str(e)}")
                        if self.stop_event.is_set():
                            return
                        self.failure_count += 1
                        self.callback(self.ip_address, f"Error: {str(e)}", None, None, self.success_count,
                                      self.failure_count,
                                      start_time)

                    # Align next_ping_time with the interval from the last scheduled time
                    next_ping_time += self.interval

                    # Adjust next_ping_time if still behind(missed several times)
                    while current_time > next_ping_time:
                        next_ping_time += self.interval

                time.sleep(0.001)
        except Exception as e:
            traceback.print_exc()
        finally:
            logging.info(f"Stop pinging {self.ip_address}")

    def start(self):
        """
        Start the ping monitoring
        """
        self.stop_event.clear()
        ip_pattern = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        ip_addresses = re.findall(ip_pattern, self.ip_address)
        if len(ip_addresses) > 0:
            self.thread = threading.Thread(target=self._ping_ip)
            self.thread.start()
        else:
            raise ValueError(f"Invalid IP Address {self.ip_address}.")

    def stop(self):
        """
        Stop the ping monitoring.
        """
        self.stop_event.set()
        self.thread = None

    def clear(self):
        self.success_count = 0
        self.failure_count = 0
