#!/usr/bin/env python3
"""
API server para apuestas (sin HTML) usado por apuestas.html

Endpoints:
 - GET /api/pilotos
 - POST /api/apuestas/create
 - GET /api/apuestas/<user>
"""

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

HOST = '127.0.0.1'
PORT = 8001
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'f1_app.db')


# ---------------------------------------------------------
# Handler principal
# ---------------------------------------------------------
class APIHandler(BaseHTTPRequestHandler):

    # ------------------------------
    # Respuesta JSON + CORS
    # ------------------------------
    def _set_json_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_json_headers(200)

    # ------------------------------
    # GET
    # ------------------------------
    def do_GET(self):

        # ------------------------------
        # GET: /api/pilotos
        # ------------------------------
        if self.path == '/api/pilotos':
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM drivers ORDER BY name COLLATE NOCASE")
                rows = cur.fetchall()

                pilotos = [{'id': r[0], 'name': r[1]} for r in rows]

                self._set_json_headers(200)
                self.wfile.write(json.dumps({
                    'success': True,
                    'pilotos': pilotos
                }).encode('utf-8'))

            except Exception as e:
                self._set_json_headers(500)
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': str(e)
                }).encode('utf-8'))

            finally:
                try: conn.close()
                except: pass

            return

        # ------------------------------
        # GET: /api/apuestas/<user>
        # ------------------------------
        if self.path.startswith('/api/apuestas/'):
            try:
                user = self.path.split('/')[-1]

                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, piloto1, piloto2, piloto3, fecha
                    FROM apuestas
                    WHERE user = ?
                """, (user,))
                rows = cur.fetchall()

                apuestas = [
                    {
                        'id': r[0],
                        'piloto1': r[1],
                        'piloto2': r[2],
                        'piloto3': r[3],
                        'fecha': r[4]
                    }
                    for r in rows
                ]

                self._set_json_headers(200)
                self.wfile.write(json.dumps({
                    'success': True,
                    'apuestas': apuestas
                }).encode('utf-8'))

            except Exception as e:
                self._set_json_headers(500)
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': str(e)
                }).encode('utf-8'))

            finally:
                try: conn.close()
                except: pass

            return

        # ------------------------------
        # RUTA NO EXISTE
        # ------------------------------
        self._set_json_headers(404)
        self.wfile.write(json.dumps({
            'success': False,
            'message': 'Not found'
        }).encode('utf-8'))


    # ------------------------------
    # POST
    # ------------------------------
    def do_POST(self):

        # ------------------------------
        # POST: /api/apuestas/create
        # ------------------------------
        if self.path == '/api/apuestas/create':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)

            try:
                data = json.loads(body)

                user = data.get("user")
                p1 = data.get("piloto1")
                p2 = data.get("piloto2")
                p3 = data.get("piloto3")

                if not user or not p1 or not p2 or not p3:
                    raise ValueError("Faltan datos para crear la apuesta")

                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO apuestas (user, piloto1, piloto2, piloto3, fecha)
                    VALUES (?, ?, ?, ?, ?)
                """, (user, p1, p2, p3, datetime.now().isoformat()))

                conn.commit()

                self._set_json_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Apuesta creada exitosamente"
                }).encode('utf-8'))

            except Exception as e:
                self._set_json_headers(400)
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": str(e)
                }).encode('utf-8'))

            finally:
                try: conn.close()
                except: pass

            return

        # ------------------------------
        # RUTA NO EXISTE
        # ------------------------------
        self._set_json_headers(404)
        self.wfile.write(json.dumps({
            'success': False,
            'message': 'Not found'
        }).encode('utf-8'))


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
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
