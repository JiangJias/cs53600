import subprocess
import re
import requests
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import json
import time
import os

# --- Configuration ---
# Ensure you have installed requirements: pip install requests matplotlib geopy
# Assignment: CS 536 Assignment 1

def get_my_info():
    """Fetches local IP and geolocation coordinates using ipapi.co."""
    try:
        response = requests.get('https://ipapi.co/json/').json()
        return response['ip'], (response['latitude'], response['longitude'])
    except Exception as e:
        print(f"Error fetching local info: {e}")
        return "127.0.0.1", (0, 0)

def run_ping(ip):
    """
    Executes a ping test and parses min, max, and average RTT.
    Returns (min, avg, max) in ms.
    """
    # Use -c for Unix-like systems and -n for Windows
    param = "-c" if os.name != 'nt' else "-n"
    cmd = ["ping", param, "4", ip]
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        # Regex to capture the min/avg/max values from the ping summary line
        stats = re.findall(r"(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/", output)
        if stats:
            return float(stats[0][0]), float(stats[0][1]), float(stats[0][2])
        
        # Windows-specific parsing if needed
        win_stats = re.findall(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)
        if win_stats:
            return float(win_stats[0][0]), float(win_stats[0][2]), float(win_stats[0][1])
    except Exception:
        print(f"Ping failed for {ip}")
    return None, None, None

def get_geo(ip):
    """Finds geolocation coordinates from publicly available data."""
    try:
        res = requests.get(f'https://ipapi.co/{ip}/json/').json()
        if 'latitude' in res:
            return res['latitude'], res['longitude']
    except Exception:
        pass
    return None, None

def run_traceroute(ip):
    """
    Finds RTT to each intermediate hop using traceroute.
    Filters out non-responsive hops.
    """
    # 'traceroute' for Linux/Mac, 'tracert' for Windows
    cmd = ["traceroute", "-q", "1", ip] if os.name != 'nt' else ["tracert", "-d", ip]
    hops_latencies = []
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().splitlines()
        for line in output[1:]:
            # Clean and filter non-responsive hops (*)
            if "*" in line or not line.strip():
                continue
            
            # Extract the first latency found in the line
            ms_match = re.search(r"(\d+\.?\d*)\s*ms", line)
            if ms_match:
                hops_latencies.append(float(ms_match.group(1)))
    except Exception as e:
        print(f"Traceroute failed for {ip}: {e}")
        
    return hops_latencies

def main(input_file):
    """Main execution flow: Data collection -> Plotting -> PDF output."""
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        target_ips = [line.strip() for line in f if line.strip()]
    
    my_ip, my_coords = get_my_info()
    # Add local IP to the test list as per requirements
    target_ips.append(my_ip)
    
    ping_results = []
    traceroute_results = []

    print(f"Starting experiments for {len(target_ips)} addresses...")

    for ip in target_ips:
        print(f"Processing: {ip}")
        # Task 1: Ping & Geolocation
        min_rtt, avg_rtt, max_rtt = run_ping(ip)
        lat, lon = get_geo(ip)
        
        if avg_rtt is not None and lat is not None:
            dist = geodesic(my_coords, (lat, lon)).km
            ping_results.append({
                'ip': ip, 'dist': dist, 'avg': avg_rtt, 
                'min': min_rtt, 'max': max_rtt
            })
        
        # Task 2: Traceroute (Pick 5 random or first 5 responsive)
        if len(traceroute_results) < 5 and ip != my_ip:
            hops = run_traceroute(ip)
            if hops:
                traceroute_results.append({'ip': ip, 'hops': hops})

    # --- Plotting Section ---
    
    # 1. Distance vs RTT Scatter Plot
    plt.figure(figsize=(8, 5))
    dists = [p['dist'] for p in ping_results]
    rtts = [p['avg'] for p in ping_results]
    plt.scatter(dists, rtts, color='blue', alpha=0.6)
    plt.title('Distance vs Round-Trip Time (RTT)')
    plt.xlabel('Geographical Distance (km)')
    plt.ylabel('Average RTT (ms)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('distance_vs_rtt.pdf')
    print("Generated: distance_vs_rtt.pdf")

    # 2. Hop Count vs RTT Scatter Plot
    plt.figure(figsize=(8, 5))
    h_counts = [len(t['hops']) for t in traceroute_results]
    h_total_rtt = [t['hops'][-1] for t in traceroute_results]
    plt.scatter(h_counts, h_total_rtt, color='green', marker='s')
    plt.title('Hop Count vs RTT')
    plt.xlabel('Number of Hops')
    plt.ylabel('Total RTT to Destination (ms)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('hop_vs_rtt.pdf')
    print("Generated: hop_vs_rtt.pdf")

    # 3. Stacked Bar Chart: Latency Breakdown 
    plt.figure(figsize=(10, 6))
    for i, t in enumerate(traceroute_results):
        hops = t['hops']
        # Calculate incremental latency (current hop RTT - previous hop RTT)
        incremental = [hops[0]] + [max(0, hops[j] - hops[j-1]) for j in range(1, len(hops))]
        
        bottom = 0
        for segment in incremental:
            plt.bar(f"Dest {i+1}\n({t['ip']})", segment, bottom=bottom)
            bottom += segment
            
    plt.title('Latency Breakdown per Hop (Stacked)')
    plt.ylabel('Cumulative Latency (ms)')
    plt.savefig('latency_breakdown.pdf')
    print("Generated: latency_breakdown.pdf")

if __name__ == "__main__":
    # Create a dummy input file if it doesn't exist for demonstration
    filename = "ips.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("8.8.8.8\n1.1.1.1\nwww.google.com\n")
    
    main(filename)