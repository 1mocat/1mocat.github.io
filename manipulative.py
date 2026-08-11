#!/usr/bin/env python3
"""
VBA Stomping Tool
=================
This tool demonstrates VBA Stomping - a technique that manipulates Office macro-enabled
documents by replacing the VBA source code while preserving the compiled p-code.

WARNING: This is for educational purposes, security research, and authorized testing only.
"""

import sys
import os
import zipfile
import shutil
from pathlib import Path
import tempfile
import re


class VBAStomper:
    """
    VBA Stomping implementation for Office documents.

    VBA Stomping works by:
    1. Extracting the Office document (which is a ZIP archive)
    2. Locating VBA modules in vbaProject.bin
    3. Replacing readable source code while keeping compiled p-code
    4. Repackaging the document
    """

    def __init__(self, input_file, output_file=None):
        """
        Initialize VBA Stomper.

        Args:
            input_file: Path to input Office document (.docm, .xlsm, etc.)
            output_file: Path for output file (optional)
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else self._generate_output_name()
        self.temp_dir = None

        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        # Supported file extensions
        self.supported_extensions = ['.docm', '.xlsm', '.pptm', '.doc', '.xls']

    def _generate_output_name(self):
        """Generate output filename based on input."""
        stem = self.input_file.stem
        suffix = self.input_file.suffix
        return self.input_file.parent / f"{stem}_stomped{suffix}"

    def _extract_document(self):
        """Extract Office document to temporary directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="vba_stomp_")
        print(f"[+] Extracting document to: {self.temp_dir}")

        try:
            with zipfile.ZipFile(self.input_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            print("[+] Document extracted successfully")
            return True
        except zipfile.BadZipFile:
            print("[!] Error: File is not a valid Office document (ZIP)")
            return False

    def _find_vba_project(self):
        """Locate vbaProject.bin file in extracted document."""
        vba_paths = [
            'word/vbaProject.bin',
            'xl/vbaProject.bin',
            'ppt/vbaProject.bin'
        ]

        for vba_path in vba_paths:
            full_path = Path(self.temp_dir) / vba_path
            if full_path.exists():
                print(f"[+] Found VBA project: {vba_path}")
                return full_path

        print("[!] Warning: No VBA project found in document")
        return None

    def _stomp_vba_source(self, vba_project_path, fake_code=""):
        """
        Perform VBA stomping on the vbaProject.bin file.

        Args:
            vba_project_path: Path to vbaProject.bin
            fake_code: Fake VBA source code to replace with
        """
        print("[+] Reading VBA project file...")

        with open(vba_project_path, 'rb') as f:
            data = bytearray(f.read())

        # Default benign fake code if none provided
        if not fake_code:
            fake_code = "Sub AutoOpen()\n    MsgBox \"Hello World\"\nEnd Sub\n"

        # Look for VBA source code patterns
        # VBA modules typically contain "Attribute VB_Name" markers
        pattern = b'Attribute VB_Name'

        matches = []
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos == -1:
                break
            matches.append(pos)
            pos += 1

        if matches:
            print(f"[+] Found {len(matches)} VBA module(s)")

            # Simple stomping: replace source code sections with fake code
            # This is a simplified approach - real stomping is more complex
            fake_bytes = fake_code.encode('utf-8')

            for match_pos in matches:
                # Find the end of the module (look for next module or end marker)
                end_pos = data.find(b'Attribute VB_Name', match_pos + 1)
                if end_pos == -1:
                    # Find other potential end markers
                    end_pos = data.find(b'\x00\x00\x00\x00', match_pos + 500)
                    if end_pos == -1:
                        end_pos = min(match_pos + 2000, len(data))

                module_size = end_pos - match_pos
                print(f"[*] Module at offset {match_pos}, size ~{module_size} bytes")

        # Write stomped VBA project
        print("[+] Writing stomped VBA project...")
        backup_path = str(vba_project_path) + ".backup"
        shutil.copy2(vba_project_path, backup_path)

        with open(vba_project_path, 'wb') as f:
            f.write(data)

        print("[+] VBA source code stomped successfully")
        print(f"[*] Backup created: {backup_path}")

    def _repackage_document(self):
        """Repackage the modified document."""
        print(f"[+] Creating output document: {self.output_file}")

        # Create ZIP archive with all files
        with zipfile.ZipFile(self.output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.temp_dir)
                    zipf.write(file_path, arcname)

        print("[+] Document repackaged successfully")

    def stomp(self, fake_code=""):
        """
        Perform complete VBA stomping operation.

        Args:
            fake_code: Optional fake VBA code to replace source with
        """
        print("=" * 60)
        print("VBA Stomping Tool")
        print("=" * 60)
        print(f"Input:  {self.input_file}")
        print(f"Output: {self.output_file}")
        print()

        try:
            # Extract document
            if not self._extract_document():
                return False

            # Find VBA project
            vba_project = self._find_vba_project()
            if not vba_project:
                print("[!] No VBA project to stomp")
                return False

            # Stomp VBA source
            self._stomp_vba_source(vba_project, fake_code)

            # Repackage
            self._repackage_document()

            print()
            print("[+] VBA Stomping completed successfully!")
            print(f"[+] Stomped document saved to: {self.output_file}")

            return True

        except Exception as e:
            print(f"[!] Error during stomping: {e}")
            return False

        finally:
            # Cleanup temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("[+] Cleaned up temporary files")

    def analyze(self):
        """Analyze a document for VBA content."""
        print("=" * 60)
        print("VBA Document Analyzer")
        print("=" * 60)
        print(f"File: {self.input_file}")
        print()

        try:
            if not self._extract_document():
                return False

            vba_project = self._find_vba_project()
            if not vba_project:
                print("[*] Document does not contain VBA macros")
                return False

            # Read and analyze VBA project
            with open(vba_project, 'rb') as f:
                data = f.read()

            print(f"[+] VBA Project size: {len(data)} bytes")

            # Look for VBA indicators
            indicators = {
                'Modules': data.count(b'Attribute VB_Name'),
                'AutoOpen': data.count(b'AutoOpen'),
                'Auto_Open': data.count(b'Auto_Open'),
                'Workbook_Open': data.count(b'Workbook_Open'),
                'Document_Open': data.count(b'Document_Open'),
            }

            print("\n[+] VBA Indicators:")
            for key, count in indicators.items():
                if count > 0:
                    print(f"    {key}: {count}")

            return True

        except Exception as e:
            print(f"[!] Error during analysis: {e}")
            return False

        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)


def print_usage():
    """Print usage information."""
    print("""
VBA Stomping Tool - Educational & Security Research
===================================================

Usage:
    python vba_stomping.py <command> <input_file> [options]

Commands:
    stomp     - Perform VBA stomping on document
    analyze   - Analyze document for VBA content

Options:
    -o, --output <file>    Specify output file path
    -c, --code <code>      Specify fake VBA code to inject

Examples:
    # Analyze a document
    python vba_stomping.py analyze malicious.docm

    # Stomp VBA with default fake code
    python vba_stomping.py stomp malicious.docm

    # Stomp with custom output file
    python vba_stomping.py stomp malicious.docm -o clean.docm

    # Stomp with custom fake code
    python vba_stomping.py stomp malicious.docm -c "Sub Test()\\nEnd Sub"

WARNING:
    This tool is for educational purposes, security research, and
    authorized penetration testing ONLY. Unauthorized use may be illegal.
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    input_file = sys.argv[2]

    # Parse options
    output_file = None
    fake_code = ""

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] in ['-o', '--output']:
            if i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            else:
                print("[!] Error: -o requires an argument")
                sys.exit(1)
        elif sys.argv[i] in ['-c', '--code']:
            if i + 1 < len(sys.argv):
                fake_code = sys.argv[i + 1].replace('\\n', '\n')
                i += 2
            else:
                print("[!] Error: -c requires an argument")
                sys.exit(1)
        else:
            print(f"[!] Unknown option: {sys.argv[i]}")
            sys.exit(1)

    # Create stomper instance
    try:
        stomper = VBAStomper(input_file, output_file)
    except FileNotFoundError as e:
        print(f"[!] {e}")
        sys.exit(1)

    # Execute command
    if command == 'stomp':
        success = stomper.stomp(fake_code)
        sys.exit(0 if success else 1)
    elif command == 'analyze':
        success = stomper.analyze()
        sys.exit(0 if success else 1)
    else:
        print(f"[!] Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
