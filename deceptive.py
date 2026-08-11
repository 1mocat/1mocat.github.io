#!/usr/bin/env python3
"""
Chrome Password Decryptor
This script decrypts saved passwords from Chrome browser.
For Chrome 80+: Uses AES-GCM decryption
For Chrome <80: Uses DPAPI decryption (Windows only)

WARNING: This script is for educational and authorized security testing purposes only.
Only use on your own Chrome profile or with explicit authorization.
"""

import os
import json
import base64
import sqlite3
import shutil
from datetime import datetime, timedelta
import sys

# Platform-specific imports
if sys.platform == "win32":
    import win32crypt  # pip install pywin32
from Crypto.Cipher import AES  # pip install pycryptodome


def get_chrome_datetime(chromedate):
    """Convert Chrome timestamp to datetime object."""
    if chromedate != 86400000000 and chromedate:
        try:
            return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
        except:
            return chromedate
    else:
        return ""


def get_encryption_key():
    """
    Retrieve the encryption key used by Chrome to encrypt passwords.
    The key is stored in the 'Local State' file.
    """
    if sys.platform == "win32":
        local_state_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData", "Local", "Google", "Chrome", "User Data", "Local State"
        )
    elif sys.platform == "darwin":  # macOS
        local_state_path = os.path.join(
            os.path.expanduser("~"),
            "Library", "Application Support", "Google", "Chrome", "Local State"
        )
    elif sys.platform.startswith("linux"):
        local_state_path = os.path.join(
            os.path.expanduser("~"),
            ".config", "google-chrome", "Local State"
        )
    else:
        raise Exception(f"Unsupported platform: {sys.platform}")

    if not os.path.exists(local_state_path):
        raise FileNotFoundError(f"Chrome Local State file not found at: {local_state_path}")

    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    # Decode the encryption key from Base64
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])

    # Remove 'DPAPI' prefix (first 5 bytes)
    encrypted_key = encrypted_key[5:]

    # Decrypt the key using platform-specific method
    if sys.platform == "win32":
        # Use DPAPI on Windows
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    elif sys.platform == "darwin":  # macOS
        # On macOS, use keychain (requires keyring library or security command)
        import subprocess
        # For macOS, we need to use the security command or keyring
        # This is a simplified version - full implementation requires keychain access
        import keyring
        try:
            # Chrome stores the key in the keychain with service name 'Chrome Safe Storage'
            chrome_key = keyring.get_password("Chrome Safe Storage", "Chrome")
            if chrome_key:
                from Crypto.Protocol.KDF import PBKDF2
                # Derive key from keychain password
                key = PBKDF2(chrome_key.encode(), b'saltysalt', dkLen=16, count=1003)
            else:
                # Fallback to default salt method
                key = PBKDF2(b'peanuts', b'saltysalt', dkLen=16, count=1003)
        except:
            # Fallback to default password
            from Crypto.Protocol.KDF import PBKDF2
            key = PBKDF2(b'peanuts', b'saltysalt', dkLen=16, count=1003)
    elif sys.platform.startswith("linux"):
        # On Linux, use the default password 'peanuts'
        from Crypto.Protocol.KDF import PBKDF2
        key = PBKDF2(b'peanuts', b'saltysalt', dkLen=16, count=1003)

    return key


def decrypt_password(password, key):
    """
    Decrypt a Chrome password.
    For Chrome 80+: Uses AES-GCM decryption
    For older Chrome: Uses DPAPI (Windows only)
    """
    try:
        # Check if password starts with 'v10' or 'v11' (Chrome 80+)
        if password[:3] == b'v10' or password[:3] == b'v11':
            # AES-GCM decryption (Chrome 80+)
            # Extract initialization vector (IV) - bytes 3 to 15 (12 bytes)
            iv = password[3:15]
            # Extract encrypted password - from byte 15 onwards
            encrypted_password = password[15:]

            # Create AES-GCM cipher
            cipher = AES.new(key, AES.MODE_GCM, iv)

            # Decrypt and verify
            # The last 16 bytes are the authentication tag
            decrypted_password = cipher.decrypt(encrypted_password[:-16])

            return decrypted_password.decode('utf-8')
        else:
            # DPAPI decryption (older Chrome versions, Windows only)
            if sys.platform == "win32":
                decrypted_password = win32crypt.CryptUnprotectData(
                    password, None, None, None, 0
                )[1]
                return decrypted_password.decode('utf-8')
            else:
                # For non-Windows platforms with old Chrome format
                return ""
    except Exception as e:
        print(f"Error decrypting password: {e}")
        return ""


def get_chrome_passwords(profile="Default"):
    """
    Extract and decrypt all saved passwords from Chrome.

    Args:
        profile: Chrome profile name (default: "Default")
    """
    # Get the encryption key
    try:
        key = get_encryption_key()
    except Exception as e:
        print(f"Error getting encryption key: {e}")
        return []

    # Get the path to Chrome's Login Data database
    if sys.platform == "win32":
        db_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData", "Local", "Google", "Chrome", "User Data", profile, "Login Data"
        )
    elif sys.platform == "darwin":  # macOS
        db_path = os.path.join(
            os.path.expanduser("~"),
            "Library", "Application Support", "Google", "Chrome", profile, "Login Data"
        )
    elif sys.platform.startswith("linux"):
        db_path = os.path.join(
            os.path.expanduser("~"),
            ".config", "google-chrome", profile, "Login Data"
        )
    else:
        print(f"Unsupported platform: {sys.platform}")
        return []

    if not os.path.exists(db_path):
        print(f"Chrome Login Data database not found at: {db_path}")
        return []

    # Copy the database to a temporary location (Chrome locks the file)
    temp_db_path = "chrome_passwords_temp.db"
    shutil.copyfile(db_path, temp_db_path)

    # Connect to the database
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Query to get all login credentials
    cursor.execute(
        "SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used "
        "FROM logins ORDER BY date_created"
    )

    passwords = []

    # Iterate through all saved passwords
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        encrypted_password = row[3]
        date_created = row[4]
        date_last_used = row[5]

        # Decrypt the password
        decrypted_password = decrypt_password(encrypted_password, key)

        if username or decrypted_password:
            passwords.append({
                "origin_url": origin_url,
                "action_url": action_url,
                "username": username,
                "password": decrypted_password,
                "date_created": get_chrome_datetime(date_created),
                "date_last_used": get_chrome_datetime(date_last_used)
            })

    # Close database connection
    cursor.close()
    conn.close()

    # Remove temporary database
    try:
        os.remove(temp_db_path)
    except:
        pass

    return passwords


def main():
    """Main function to extract and display Chrome passwords."""
    print("=" * 80)
    print("Chrome Password Decryptor")
    print("=" * 80)
    print()

    # Check platform compatibility
    if sys.platform not in ["win32", "darwin", "linux"]:
        print(f"Error: Unsupported platform '{sys.platform}'")
        return

    # Get passwords
    print("Extracting passwords from Chrome...")
    passwords = get_chrome_passwords()

    if not passwords:
        print("No passwords found or unable to decrypt.")
        return

    print(f"\nFound {len(passwords)} saved password(s):\n")
    print("-" * 80)

    # Display all passwords
    for index, password_data in enumerate(passwords, start=1):
        print(f"\n[{index}] Website: {password_data['origin_url']}")
        print(f"    Username: {password_data['username']}")
        print(f"    Password: {password_data['password']}")
        print(f"    Created:  {password_data['date_created']}")
        print(f"    Last Used: {password_data['date_last_used']}")
        print("-" * 80)

    # Optional: Save to file
    save_option = input("\nDo you want to save the passwords to a file? (y/n): ")
    if save_option.lower() == 'y':
        output_file = "chrome_passwords.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Chrome Saved Passwords\n")
            f.write("=" * 80 + "\n\n")
            for index, password_data in enumerate(passwords, start=1):
                f.write(f"[{index}] Website: {password_data['origin_url']}\n")
                f.write(f"    Username: {password_data['username']}\n")
                f.write(f"    Password: {password_data['password']}\n")
                f.write(f"    Created:  {password_data['date_created']}\n")
                f.write(f"    Last Used: {password_data['date_last_used']}\n")
                f.write("-" * 80 + "\n\n")
        print(f"\nPasswords saved to: {output_file}")


if __name__ == "__main__":
    main()
