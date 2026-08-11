#!/usr/bin/env python3
"""
VBA Stomp Template Server
Provides VBA stomp templates over HTTP for authorized security testing and research.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
from datetime import datetime
import io
import struct

class VBAStompTemplates:
    """VBA Stomp template generator for security research and authorized testing."""

    @staticmethod
    def generate_basic_template():
        """Generate a basic VBA stomped document template."""
        return {
            "name": "Basic VBA Stomp",
            "description": "Simple VBA stomp template with benign code replaced",
            "original_code": 'Sub AutoOpen()\n    MsgBox "Hello World"\nEnd Sub',
            "stomped_code": 'Sub AutoOpen()\n    MsgBox "Legitimate Macro"\nEnd Sub',
            "technique": "P-code manipulation",
            "detection_notes": "May evade signature-based detection"
        }

    @staticmethod
    def generate_empty_module_template():
        """Generate empty module VBA stomp template."""
        return {
            "name": "Empty Module Stomp",
            "description": "VBA stomp with empty visible module",
            "original_code": 'Sub Document_Open()\n    ' + "' Malicious code here\n" + 'End Sub',
            "stomped_code": '',
            "technique": "Module stream clearing while preserving P-code",
            "detection_notes": "P-code still executes despite empty source"
        }

    @staticmethod
    def generate_benign_template():
        """Generate benign-looking VBA stomp template."""
        return {
            "name": "Benign Comment Stomp",
            "description": "Replace actual code with benign comments",
            "original_code": 'Sub Workbook_Open()\n    ' + "' Execute payload\n" + 'End Sub',
            "stomped_code": 'Sub Workbook_Open()\n    ' + "' This macro does nothing\n    ' Just comments here\n" + 'End Sub',
            "technique": "Source replacement with comments, P-code intact",
            "detection_notes": "Source appears harmless but P-code executes original"
        }

    @staticmethod
    def generate_dirstream_template():
        """Generate _VBA_PROJECT stream manipulation template."""
        return {
            "name": "DIR Stream Manipulation",
            "description": "Modify _VBA_PROJECT DIR stream",
            "technique": "Manipulate module offsets in DIR stream",
            "steps": [
                "1. Parse _VBA_PROJECT stream",
                "2. Locate MODULESTREAMNAME record",
                "3. Modify text offset to point to fake code",
                "4. Keep compiled P-code offset unchanged",
                "5. Recompress stream"
            ],
            "detection_notes": "Requires parsing DIR stream structure"
        }

    @staticmethod
    def get_all_templates():
        """Get all available VBA stomp templates."""
        return [
            VBAStompTemplates.generate_basic_template(),
            VBAStompTemplates.generate_empty_module_template(),
            VBAStompTemplates.generate_benign_template(),
            VBAStompTemplates.generate_dirstream_template()
        ]


class VBAStompHandler(BaseHTTPRequestHandler):
    """HTTP request handler for VBA stomp template server."""

    def _set_headers(self, content_type='application/json', status=200):
        """Set HTTP response headers."""
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _send_json(self, data, status=200):
        """Send JSON response."""
        self._set_headers('application/json', status)
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self._send_homepage()
        elif self.path == '/templates':
            self._send_all_templates()
        elif self.path == '/templates/basic':
            self._send_json(VBAStompTemplates.generate_basic_template())
        elif self.path == '/templates/empty':
            self._send_json(VBAStompTemplates.generate_empty_module_template())
        elif self.path == '/templates/benign':
            self._send_json(VBAStompTemplates.generate_benign_template())
        elif self.path == '/templates/dirstream':
            self._send_json(VBAStompTemplates.generate_dirstream_template())
        elif self.path == '/info':
            self._send_info()
        else:
            self._send_json({'error': 'Not found'}, 404)

    def _send_homepage(self):
        """Send HTML homepage with API documentation."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>VBA Stomp Template Server</title>
            <style>
                body { font-family: monospace; max-width: 900px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-left: 4px solid #007acc; }
                .warning { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }
                code { background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>VBA Stomp Template Server</h1>

            <div class="warning">
                <strong>⚠️ AUTHORIZED USE ONLY</strong><br>
                This server provides VBA stomping templates for:<br>
                • Authorized security testing and penetration testing<br>
                • Red team exercises with proper authorization<br>
                • Security research and education<br>
                • Defensive security analysis
            </div>

            <h2>Available Endpoints</h2>

            <div class="endpoint">
                <strong>GET /</strong><br>
                This page - API documentation
            </div>

            <div class="endpoint">
                <strong>GET /templates</strong><br>
                Get all available VBA stomp templates
            </div>

            <div class="endpoint">
                <strong>GET /templates/basic</strong><br>
                Basic VBA stomp template with P-code manipulation
            </div>

            <div class="endpoint">
                <strong>GET /templates/empty</strong><br>
                Empty module VBA stomp template
            </div>

            <div class="endpoint">
                <strong>GET /templates/benign</strong><br>
                Benign-looking VBA stomp with comments
            </div>

            <div class="endpoint">
                <strong>GET /templates/dirstream</strong><br>
                DIR stream manipulation template
            </div>

            <div class="endpoint">
                <strong>GET /info</strong><br>
                Server information and VBA stomp technique overview
            </div>

            <h2>Example Usage</h2>
            <pre>
# Get all templates
curl http://localhost:8080/templates

# Get specific template
curl http://localhost:8080/templates/basic

# Get server info
curl http://localhost:8080/info
            </pre>

            <h2>About VBA Stomping</h2>
            <p>
                VBA stomping is a technique where the visible VBA source code in an Office document
                is modified to appear benign, while the compiled P-code (which actually executes)
                remains malicious. This can evade signature-based detection that only inspects
                the source code.
            </p>

            <p><strong>Server started:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </body>
        </html>
        """
        self._set_headers('text/html')
        self.wfile.write(html.encode('utf-8'))

    def _send_all_templates(self):
        """Send all available templates."""
        templates = VBAStompTemplates.get_all_templates()
        self._send_json({
            'templates': templates,
            'count': len(templates),
            'timestamp': datetime.now().isoformat()
        })

    def _send_info(self):
        """Send server information."""
        info = {
            'name': 'VBA Stomp Template Server',
            'version': '1.0.0',
            'description': 'Provides VBA stomp templates for authorized security testing',
            'timestamp': datetime.now().isoformat(),
            'techniques': [
                {
                    'name': 'P-code Preservation',
                    'description': 'Modify source while keeping compiled P-code intact'
                },
                {
                    'name': 'Source Replacement',
                    'description': 'Replace VBA source with benign code or comments'
                },
                {
                    'name': 'Module Stream Clearing',
                    'description': 'Empty the module stream while P-code remains'
                },
                {
                    'name': 'DIR Stream Manipulation',
                    'description': 'Modify _VBA_PROJECT DIR stream offsets'
                }
            ],
            'use_cases': [
                'Authorized penetration testing',
                'Red team exercises',
                'Security research',
                'Defensive analysis',
                'Detection capability testing'
            ],
            'warnings': [
                'Requires proper authorization',
                'For educational and defensive purposes',
                'Not for malicious use'
            ]
        }
        self._send_json(info)

    def log_message(self, format, *args):
        """Override to customize logging."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.address_string()} - {format % args}")


def run_server(port=8080, host='localhost'):
    """Run the VBA stomp template server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, VBAStompHandler)

    print("=" * 70)
    print("VBA Stomp Template Server")
    print("=" * 70)
    print(f"\n⚠️  AUTHORIZED USE ONLY")
    print("This server is for authorized security testing and research.\n")
    print(f"Server running on: http://{host}:{port}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("Available endpoints:")
    print(f"  • http://{host}:{port}/")
    print(f"  • http://{host}:{port}/templates")
    print(f"  • http://{host}:{port}/templates/basic")
    print(f"  • http://{host}:{port}/templates/empty")
    print(f"  • http://{host}:{port}/templates/benign")
    print(f"  • http://{host}:{port}/templates/dirstream")
    print(f"  • http://{host}:{port}/info")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 70)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()
        print("Server stopped.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='VBA Stomp Template Server for authorized security testing'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Port to run the server on (default: 8080)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host to bind to (default: localhost)'
    )

    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
