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
from urllib.parse import urlparse

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

    def do_POST(self):
        if self.path == '/register':
            self._handle_register()
        elif self.path == '/login':
            self._handle_login()
        else:
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

    def _send_json(self, obj, status=200):
        payload = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        # CORS headers to allow requests from the browser (useful if pages are served
        # from a different origin during development)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        # Respond to preflight CORS requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
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
