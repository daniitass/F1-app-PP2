#!/usr/bin/env python3
"""Small API server for apuestas (no HTML) exposing endpoints used by apuestas.html

Run with: py -3 apuestas_api.py
API endpoints:
 - GET /api/pilotos -> { success: true, pilotos: [ {id, name}, ... ] }

This server listens on 127.0.0.1:8001 and enables CORS so the frontend served
from another origin (e.g. 127.0.0.1:8000) can call it.
"""
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = '127.0.0.1'
PORT = 8001
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'f1_app.db')


class APIHandler(BaseHTTPRequestHandler):
    def _set_json_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/pilotos':
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM drivers ORDER BY name COLLATE NOCASE")
                rows = cur.fetchall()
                pilotos = [{'id': r[0], 'name': r[1]} for r in rows]
                payload = json.dumps({'success': True, 'pilotos': pilotos}).encode('utf-8')
                self._set_json_headers(200)
                self.wfile.write(payload)
            except Exception as e:
                payload = json.dumps({'success': False, 'message': str(e)}).encode('utf-8')
                self._set_json_headers(500)
                self.wfile.write(payload)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            return

        # unknown path
        payload = json.dumps({'success': False, 'message': 'Not found'}).encode('utf-8')
        self._set_json_headers(404)
        self.wfile.write(payload)


def run():
    server = HTTPServer((HOST, PORT), APIHandler)
    print(f"Apuestas API serving at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down API')
        server.server_close()


if __name__ == '__main__':
    run()
