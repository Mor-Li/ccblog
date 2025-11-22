#!/usr/bin/env python3
"""
Collect public IP addresses by making repeated requests over 1 minute.
This helps identify all possible egress IPs used by this machine.
"""

import requests
import time
from collections import Counter
from datetime import datetime, timedelta

# List of IP detection services to use
IP_SERVICES = [
    'https://api.ipify.org',
    'https://ifconfig.me/ip',
    'https://icanhazip.com',
    'https://ipecho.net/plain',
    'https://checkip.amazonaws.com',
    'https://ident.me',
    'https://ipinfo.io/ip',
]

def get_public_ip(service_url):
    """Fetch public IP from a given service."""
    try:
        response = requests.get(service_url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        pass
    return None

def main():
    print("🔍 Starting public IP collection for 1 minute...")
    print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S')}\n")

    ip_counter = Counter()
    total_requests = 0
    service_index = 0

    start_time = time.time()
    end_time = start_time + 60  # Run for 60 seconds

    while time.time() < end_time:
        # Rotate through different services
        service_url = IP_SERVICES[service_index % len(IP_SERVICES)]
        service_index += 1

        ip = get_public_ip(service_url)
        total_requests += 1

        if ip:
            ip_counter[ip] += 1
            print(f"[{total_requests:3d}] {ip:15s} (via {service_url.split('/')[2]})")
        else:
            print(f"[{total_requests:3d}] Failed to get IP from {service_url}")

        # Small delay to avoid overwhelming services
        time.sleep(0.5)

    # Print summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"⏱️  Collection completed in {elapsed:.1f} seconds")
    print(f"📊 Total requests: {total_requests}")
    print(f"🌐 Unique IPs found: {len(ip_counter)}")
    print(f"\n{'='*60}")
    print("IP Address Distribution:")
    print(f"{'='*60}")

    for ip, count in ip_counter.most_common():
        percentage = (count / total_requests) * 100
        bar = '█' * int(percentage / 2)
        print(f"{ip:15s} | {count:3d} times ({percentage:5.1f}%) {bar}")

    print(f"\n{'='*60}")
    print("📋 Complete IP list for whitelist:")
    print(f"{'='*60}")
    for ip in sorted(ip_counter.keys()):
        print(ip)

    print(f"\n💡 Add these {len(ip_counter)} IP(s) to WeChat whitelist")

if __name__ == '__main__':
    main()
