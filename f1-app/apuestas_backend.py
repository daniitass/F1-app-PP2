#!/usr/bin/env python3
"""
Backend exclusivo para:
 - Exportar apuestas TOP 3 para Power BI
 - Consultar apuestas desde cualquier dashboard o servicio

CORRER CON:
    py -3 apuestas_backend.py

Endpoints:
 - GET /api/apuestas/all
 - GET /api/apuestas/dashboard    (para Power BI)
"""

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = '127.0.0.1'
PORT = 8010      # puerto exclusivo para Power BI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'f1_app.db')


class DashboardHandler(BaseHTTPRequestHandler):

    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):

        # -------------------------------------------------------
        # LISTAR TODAS LAS APUESTAS (uso general)
        # -------------------------------------------------------
        if self.path == "/api/apuestas/all":
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, user, piloto1, piloto2, piloto3, fecha
                    FROM apuestas
                    ORDER BY fecha DESC
                """)

                rows = cursor.fetchall()

                apuestas = [
                    {
                        "id": r[0],
                        "user": r[1],
                        "piloto1": r[2],
                        "piloto2": r[3],
                        "piloto3": r[4],
                        "fecha": r[5]
                    }
                    for r in rows
                ]

                conn.close()

                self._set_headers(200)
                self.wfile.write(json.dumps(apuestas).encode('utf-8'))
                return

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        # -------------------------------------------------------
        # ENDPOINT EXCLUSIVO PARA POWER BI
        # -------------------------------------------------------
        if self.path == "/api/apuestas/dashboard":
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT user, piloto1, piloto2, piloto3, fecha
                    FROM apuestas
                """)

                rows = cursor.fetchall()

                data = [
                    {
                        "user": r[0],
                        "piloto1": r[1],
                        "piloto2": r[2],
                        "piloto3": r[3],
                        "fecha": r[4]
                    }
                    for r in rows
                ]

                conn.close()

                self._set_headers(200)
                self.wfile.write(json.dumps(data).encode('utf-8'))
                return

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        # -------------------------------------------------------
        # Ruta desconocida
        # -------------------------------------------------------
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))


def run():
    print(f"Dashboard backend activo en http://{HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando backend...")
        server.server_close()


if __name__ == "__main__":
    run()
