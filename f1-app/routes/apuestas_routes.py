#!/usr/bin/env python3
"""
Blueprint para manejar rutas relacionadas a apuestas.

Este módulo se integra dentro de apuestas_api.py y permite mantener las rutas
organizadas y escalables.
"""

import sqlite3
import os
from flask import Blueprint, jsonify, request

# Blueprint
apuestas_bp = Blueprint('apuestas_bp', __name__)

# Ruta al archivo de base de datos (usado por createDB.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'f1_app.db')


# -----------------------------
# Helpers
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Rutas públicas del Blueprint
# -----------------------------

@apuestas_bp.route('/api/pilotos', methods=['GET'])
def api_get_pilotos():
    """Devuelve lista de pilotos para apuestas."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM drivers ORDER BY name COLLATE NOCASE")
        rows = cur.fetchall()

        pilotos = [{'id': r['id'], 'name': r['name']} for r in rows]

        return jsonify({'success': True, 'pilotos': pilotos})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        conn.close()


@apuestas_bp.route('/api/apostar', methods=['POST'])
def api_apostar():
    """
    Guarda una apuesta enviada desde apuestas.html.
    Espera JSON:
    {
        "user_id": 1,
        "piloto_id": 5,
        "monto": 100
    }
    """
    data = request.get_json()

    required = ["user_id", "piloto_id", "monto"]
    if not all(k in data for k in required):
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO apuestas (user_id, piloto_id, monto)
            VALUES (?, ?, ?)
        """, (data['user_id'], data['piloto_id'], data['monto']))

        conn.commit()

        return jsonify({'success': True, 'message': 'Apuesta registrada'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        conn.close()


@apuestas_bp.route('/api/apuestas/<int:user_id>', methods=['GET'])
def api_get_apuestas(user_id):
    """Devuelve todas las apuestas del usuario."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT A.id, D.name AS piloto, A.monto
            FROM apuestas A
            JOIN drivers D ON A.piloto_id = D.id
            WHERE A.user_id = ?
        """, (user_id,))
        rows = cur.fetchall()

        apuestas = [
            {
                'id': r['id'],
                'piloto': r['piloto'],
                'monto': r['monto']
            }
            for r in rows
        ]

        return jsonify({'success': True, 'apuestas': apuestas})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        conn.close()
