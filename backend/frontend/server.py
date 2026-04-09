import http.server
import socketserver
import webbrowser
import os

PORT = 5500

# Change directory to frontend folder
os.chdir(os.path.dirname(__file__))

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend running at http://127.0.0.1:{PORT}")
    
    # Auto open browser
    webbrowser.open(f"http://127.0.0.1:{PORT}")

    httpd.serve_forever()