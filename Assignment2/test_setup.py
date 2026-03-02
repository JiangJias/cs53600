#!/usr/bin/env python3
"""
Test script to verify setup and dependencies
"""

import sys
import socket


def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...")
    packages = [
        'numpy',
        'pandas',
        'matplotlib',
        'sklearn',
        'scipy',
        'json',
        'csv',
    ]

    failed = []
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError as e:
            print(f"  ✗ {package}: {e}")
            failed.append(package)

    if failed:
        print(f"\nFailed to import: {', '.join(failed)}")
        print("Install missing packages: pip install -r requirements.txt")
        return False

    print("All packages imported successfully!")
    return True


def test_tcp_info():
    """Test if TCP_INFO is available"""
    print("\nTesting TCP_INFO availability...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, 'TCP_INFO'):
            print("  ✓ TCP_INFO is available")
            sock.close()
            return True
        else:
            print("  ✗ TCP_INFO not available (may not work on this platform)")
            sock.close()
            return False
    except Exception as e:
        print(f"  ✗ Error testing TCP_INFO: {e}")
        return False


def test_network():
    """Test basic network connectivity"""
    print("\nTesting network connectivity...")

    test_hosts = [
        ('8.8.8.8', 53),  # Google DNS
        ('1.1.1.1', 53),  # Cloudflare DNS
    ]

    success = False
    for host, port in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            sock.close()
            print(f"  ✓ Connected to {host}:{port}")
            success = True
            break
        except Exception as e:
            print(f"  ✗ Failed to connect to {host}:{port}: {e}")

    if success:
        print("Network connectivity OK!")
    else:
        print("Network connectivity issues - check your internet connection")

    return success


def test_file_structure():
    """Test if all required files are present"""
    print("\nTesting file structure...")

    from pathlib import Path

    required_files = [
        'iperf_client.py',
        'data_collector.py',
        'visualization.py',
        'ml_model.py',
        'run_experiment.py',
        'requirements.txt',
        'Dockerfile',
        'README.md',
        'servers.txt',
    ]

    missing = []
    for filename in required_files:
        if Path(filename).exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - MISSING")
            missing.append(filename)

    if missing:
        print(f"\nMissing files: {', '.join(missing)}")
        return False

    print("All required files present!")
    return True


def main():
    print("=" * 80)
    print("Assignment 2 Setup Test")
    print("=" * 80)

    results = []

    results.append(("Package imports", test_imports()))
    results.append(("TCP_INFO availability", test_tcp_info()))
    results.append(("Network connectivity", test_network()))
    results.append(("File structure", test_file_structure()))

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n✓ All tests passed! Setup is complete.")
        print("\nYou can now run the experiment:")
        print("  python3 run_experiment.py servers.txt")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
