"""
SecureAssess Frontend Server.
Starts a local web server and prints clean, clickable URLs in the terminal.
Usage:
    python serve.py
"""

import http.server
import socketserver
import webbrowser
import sys
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    # Disable noisy log messages for every asset request, or keep simple
    def log_message(self, format, *args):
        # Keep clean console output
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]}\n")

def run():
    # Allow port reuse immediately
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("\n" + "=" * 55)
            print("  🚀 SecureAssess Frontend Server is RUNNING")
            print("=" * 55)
            print(f"\n  Clickable Links (Ctrl + Click in terminal):")
            print(f"  👉 http://localhost:{PORT}")
            print(f"  👉 http://127.0.0.1:{PORT}")
            print("\n  Press Ctrl + C to stop the server.")
            print("=" * 55 + "\n")
            
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 10048 or "Address already in use" in str(e):
            print(f"\n⚠️  Port {PORT} is already in use by another process.")
            print(f"👉 You can access it directly at: http://localhost:{PORT}\n")
        else:
            raise e
    except KeyboardInterrupt:
        print("\n\nServer stopped.")

if __name__ == "__main__":
    run()
