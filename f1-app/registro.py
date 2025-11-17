#!/usr/bin/env python3
"""Small static file server + /register endpoint WITHOUT third-party frameworks.

Run with: py -3 registro.py
Then open: http://127.0.0.1:5500/registro.html
"""
import http.server
import socketserver
import json
import os
import re
import sqlite3
import hashlib
import hmac
import binascii
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
PORT = 5500
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'f1_app.db')

# Password hashing using PBKDF2-HMAC-SHA256 (stdlib only)
def hash_password(password, iterations=100_000):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f"pbkdf2_sha256${iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def verify_password(stored, password):
    try:
        algo, iterations, salt_hex, dk_hex = stored.split('$')
        iterations = int(iterations)
        salt = binascii.unhexlify(salt_hex)
        dk = binascii.unhexlify(dk_hex)
        newdk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(newdk, dk)
    except Exception:
        return False

PWD_REGEX = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}')

def ensure_usuarios_table(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            email TEXT UNIQUE,
            contrasena TEXT,
            fecha_nacimiento TEXT,
            monto  REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

def ensure_apuestas_table(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS apuestas_top3 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            top1_driver_id INTEGER NOT NULL,
            top2_driver_id INTEGER NOT NULL,
            top3_driver_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES usuarios(id),
            FOREIGN KEY(top1_driver_id) REFERENCES drivers(id),
            FOREIGN KEY(top2_driver_id) REFERENCES drivers(id),
            FOREIGN KEY(top3_driver_id) REFERENCES drivers(id)
        )
    ''')
    conn.commit()
    _ensure_apuestas_extra_columns(conn)


def _ensure_apuestas_extra_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(apuestas_top3)")
    cols = {row[1] for row in cur.fetchall()}
    if 'status' not in cols:
        cur.execute("ALTER TABLE apuestas_top3 ADD COLUMN status TEXT NOT NULL DEFAULT 'pendiente'")
        conn.commit()

class Handler(http.server.SimpleHTTPRequestHandler):
    # serve files from BASE_DIR
    def translate_path(self, path):
        # adapt to serve files relative to BASE_DIR
        # strip query
        path = urlparse(path).path
        if path == '/':
            path = '/index.html'
        full = os.path.join(BASE_DIR, path.lstrip('/'))
        return full

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/pilotos':
            self._handle_pilotos()
            return
        if parsed.path == '/apuestas/top3':
            self._handle_list_apuestas(parsed)
            return
        if parsed.path == '/apuestas/top3/detalle':
            self._handle_apuesta_detalle(parsed)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == '/register':
            self._handle_register()
        elif self.path == '/login':
            self._handle_login()
        elif self.path == '/apuestas/top3':
            self._handle_create_apuesta()
        elif self.path == '/apuestas/top3/status':
            self._handle_update_apuesta_status()
        else:
            self.send_error(404, 'Not found')

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path == '/apuestas/top3':
            self._handle_delete_apuesta(parsed)
            return
        self.send_error(404, 'Not found')

    def _handle_register(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            self._send_json({'success': False, 'message': 'Invalid JSON'}, status=400)
            return

        nombre = (data.get('nombre') or '').strip()
        apellido = (data.get('apellido') or '').strip()
        email = (data.get('email') or '').strip().lower()
        fecha = data.get('fecha_nacimiento') or None
        password = data.get('password') or ''

        if not nombre or not apellido or not email or not password:
            self._send_json({'success': False, 'message': 'Faltan campos requeridos'}, status=400)
            return
        if not PWD_REGEX.match(password):
            self._send_json({'success': False, 'message': 'La contraseña no cumple los requisitos'}, status=400)
            return

        pwd_hash = hash_password(password)
        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_usuarios_table(conn)
            cur = conn.cursor()
            cur.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
            if cur.fetchone():
                self._send_json({'success': False, 'message': 'El email ya está registrado'}, status=409)
                return
            cur.execute('INSERT INTO usuarios (nombre, apellido, email, contrasena, fecha_nacimiento) VALUES (?, ?, ?, ?, ?)',
                        (nombre, apellido, email, pwd_hash, fecha))
            conn.commit()
            self._send_json({'success': True})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_delete_apuesta(self, parsed):
        params = parse_qs(parsed.query or '')
        bet_id = params.get('bet_id', [None])[0]
        user_id = params.get('user_id', [None])[0]
        try:
            bet_id = int(bet_id)
            user_id = int(user_id)
        except (TypeError, ValueError):
            self._send_json({'success': False, 'message': 'bet_id y user_id inválidos'}, status=400)
            return
        if not bet_id or not user_id:
            self._send_json({'success': False, 'message': 'bet_id y user_id requeridos'}, status=400)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_apuestas_table(conn)
            cur = conn.cursor()
            cur.execute('SELECT id FROM apuestas_top3 WHERE id = ? AND user_id = ?', (bet_id, user_id))
            if not cur.fetchone():
                self._send_json({'success': False, 'message': 'Apuesta no encontrada'}, status=404)
                return
            cur.execute('DELETE FROM apuestas_top3 WHERE id = ?', (bet_id,))
            conn.commit()
            self._send_json({'success': True})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_login(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            self._send_json({'success': False, 'message': 'Invalid JSON'}, status=400)
            return

        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            self._send_json({'success': False, 'message': 'Email y contraseña requeridos'}, status=400)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_usuarios_table(conn)
            cur = conn.cursor()
            cur.execute('SELECT id, nombre, apellido, contrasena FROM usuarios WHERE email = ?', (email,))
            row = cur.fetchone()
            if not row:
                self._send_json({'success': False, 'message': 'Email o contraseña incorrectos'}, status=401)
                return
            
            user_id, nombre, apellido, pwd_hash = row
            # debug: print partial hash and email to help troubleshoot
            try:
                print(f"DEBUG login attempt for {email}; stored_hash_start={pwd_hash[:40]}")
            except Exception:
                pass
            ok = verify_password(pwd_hash, password)
            print(f"DEBUG verify_password returned: {ok}")
            if not ok:
                self._send_json({'success': False, 'message': 'Email o contraseña incorrectos'}, status=401)
                return
            
            # Login exitoso
            self._send_json({
                'success': True,
                'user_id': user_id,
                'user_name': f'{nombre} {apellido}',
                'token': f'token_{user_id}_{email}'
            })
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_pilotos(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                SELECT MIN(id) AS id, name
                FROM drivers
                GROUP BY name
                ORDER BY name COLLATE NOCASE
            """)
            rows = cur.fetchall()
            pilotos = [{'id': r[0], 'name': r[1]} for r in rows]
            self._send_json({'success': True, 'pilotos': pilotos})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_create_apuesta(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            self._send_json({'success': False, 'message': 'JSON inválido'}, status=400)
            return

        try:
            user_id = int(data.get('user_id', 0))
            top1 = int(data.get('top1'))
            top2 = int(data.get('top2'))
            top3 = int(data.get('top3'))
        except (TypeError, ValueError):
            self._send_json({'success': False, 'message': 'Datos inválidos'}, status=400)
            return

        if not user_id or not top1 or not top2 or not top3:
            self._send_json({'success': False, 'message': 'Faltan campos requeridos'}, status=400)
            return
        if len({top1, top2, top3}) < 3:
            self._send_json({'success': False, 'message': 'Los pilotos deben ser distintos'}, status=400)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_usuarios_table(conn)
            ensure_apuestas_table(conn)
            cur = conn.cursor()
            cur.execute('SELECT 1 FROM usuarios WHERE id = ?', (user_id,))
            if not cur.fetchone():
                self._send_json({'success': False, 'message': 'Usuario no encontrado'}, status=404)
                return
            cur.execute('SELECT COUNT(*) FROM drivers WHERE id IN (?, ?, ?)', (top1, top2, top3))
            count = cur.fetchone()[0]
            if count < 3:
                self._send_json({'success': False, 'message': 'Pilotos inválidos'}, status=400)
                return

            cur.execute('''
                INSERT INTO apuestas_top3 (user_id, top1_driver_id, top2_driver_id, top3_driver_id, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, top1, top2, top3, 'pendiente'))
            bet_id = cur.lastrowid
            conn.commit()

            bet = self._fetch_apuesta(cur, bet_id)
            self._send_json({'success': True, 'bet': bet})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_list_apuestas(self, parsed):
        params = parse_qs(parsed.query or '')
        user_id = params.get('user_id', [None])[0]
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            self._send_json({'success': False, 'message': 'user_id requerido'}, status=400)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_apuestas_table(conn)
            cur = conn.cursor()
            apuestas = self._fetch_apuestas_for_user(cur, user_id)
            self._send_json({'success': True, 'apuestas': apuestas})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_apuesta_detalle(self, parsed):
        params = parse_qs(parsed.query or '')
        bet_id = params.get('bet_id', [None])[0]
        if bet_id is None:
            self._send_json({'success': False, 'message': 'bet_id requerido'}, status=400)
            return
        try:
            bet_id = int(bet_id)
        except (TypeError, ValueError):
            self._send_json({'success': False, 'message': 'bet_id inválido'}, status=400)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_apuestas_table(conn)
            cur = conn.cursor()
            bet = self._fetch_apuesta(cur, bet_id)
            if not bet:
                self._send_json({'success': False, 'message': 'Apuesta no encontrada'}, status=404)
                return
            self._send_json({'success': True, 'bet': bet})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _handle_update_apuesta_status(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            self._send_json({'success': False, 'message': 'JSON inválido'}, status=400)
            return

        try:
            bet_id = int(data.get('bet_id', 0))
            user_id = int(data.get('user_id', 0))
        except (TypeError, ValueError):
            self._send_json({'success': False, 'message': 'Datos inválidos'}, status=400)
            return
        status = (data.get('status') or '').strip().lower()
        if status not in ('pendiente', 'rechazada', 'activa'):
            self._send_json({'success': False, 'message': 'Estado inválido'}, status=400)
            return
        if not bet_id or not user_id:
            self._send_json({'success': False, 'message': 'bet_id y user_id requeridos'}, status=400)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            ensure_apuestas_table(conn)
            cur = conn.cursor()
            cur.execute('SELECT id FROM apuestas_top3 WHERE id = ? AND user_id = ?', (bet_id, user_id))
            if not cur.fetchone():
                self._send_json({'success': False, 'message': 'Apuesta no encontrada'}, status=404)
                return
            cur.execute('UPDATE apuestas_top3 SET status = ? WHERE id = ?', (status, bet_id))
            conn.commit()
            bet = self._fetch_apuesta(cur, bet_id)
            self._send_json({'success': True, 'bet': bet})
        except Exception as e:
            self._send_json({'success': False, 'message': str(e)}, status=500)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _fetch_apuestas_for_user(self, cur, user_id):
        cur.execute('''
            SELECT a.id, a.created_at, a.status,
                   d1.name, d2.name, d3.name
            FROM apuestas_top3 a
            JOIN drivers d1 ON d1.id = a.top1_driver_id
            JOIN drivers d2 ON d2.id = a.top2_driver_id
            JOIN drivers d3 ON d3.id = a.top3_driver_id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC, a.id DESC
        ''', (user_id,))
        rows = cur.fetchall()
        return [
            {
                'id': row[0],
                'created_at': row[1],
                'status': row[2],
                'top1': row[3],
                'top2': row[4],
                'top3': row[5],
            } for row in rows
        ]

    def _fetch_apuesta(self, cur, bet_id):
        cur.execute('''
            SELECT a.id, a.created_at,
                   d1.name, d2.name, d3.name, a.user_id, a.status
            FROM apuestas_top3 a
            JOIN drivers d1 ON d1.id = a.top1_driver_id
            JOIN drivers d2 ON d2.id = a.top2_driver_id
            JOIN drivers d3 ON d3.id = a.top3_driver_id
            WHERE a.id = ?
        ''', (bet_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'created_at': row[1],
            'top1': row[2],
            'top2': row[3],
            'top3': row[4],
            'user_id': row[5],
            'status': row[6],
        }

    def _send_json(self, obj, status=200):
        payload = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        # CORS headers to allow requests from the browser (useful if pages are served
        # from a different origin during development)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        # Respond to preflight CORS requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run():
    os.chdir(BASE_DIR)
    with socketserver.ThreadingTCPServer((HOST, PORT), Handler) as httpd:
        print(f"Serving at http://{HOST}:{PORT} (serving files from {BASE_DIR})")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nShutting down')
            httpd.server_close()

if __name__ == '__main__':
    run()
