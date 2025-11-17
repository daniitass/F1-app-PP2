import csv
import os
import sqlite3
from sqlite3 import Error

CSV_FILE = "Pilotos_2023_2024 (1).csv"
RESULTS_CSV = "resultado_races.csv"
CONSTRUCTORS_CSV = "Constructores_2023_2024.csv"
ALLSEASONS_CSV = "Formula1_AllSeasons_RaceResults_withSeason.csv"
SEASON2025_CSV = "Formula1_2025Season_RaceResults.csv"

def create_connection(db_file):
    """Crea una conexión a la base de datos SQLite (crea el archivo si no existe)."""
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print("Error al conectar:", e)
        return None

def create_table_drivers(conn):
    """Crea la tabla drivers si no existe."""
    sql = """
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pos INTEGER,
        name TEXT NOT NULL,
        nationality TEXT,
        team TEXT,
        pts INTEGER,
        season INTEGER,
        UNIQUE(name, season)
    );
    """

    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        print("Error al crear la tabla:", e)

def normalize_key(s):
    if s is None:
        return ''
    return s.strip().lower().replace('.', '').replace(' ', '')

def import_from_csv(conn, csv_path):
    """Importa filas desde el CSV a la tabla drivers.

    Devuelve (inserted_count, updated_count).
    """
    inserted = 0
    updated = 0
    if not os.path.exists(csv_path):
        print(f"CSV no encontrado: {csv_path}")
        return inserted, updated

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # map normalized header -> original header name
        key_map = {normalize_key(k): k for k in reader.fieldnames}

        cur = conn.cursor()
        for row in reader:
            # helper to get value by normalized key
            def g(k):
                key = key_map.get(k)
                return row.get(key) if key else None

            pos_raw = g('pos')
            name = g('driver') or g('name')
            nationality = g('nationality')
            team = g('team')
            pts_raw = g('pts') or g('pts')
            season_raw = g('season')

            # normalize values
            if name:
                name = name.replace('\xa0', ' ').strip()
            try:
                pos = int(pos_raw) if pos_raw and pos_raw.strip() != '' else None
            except Exception:
                pos = None
            try:
                pts = int(pts_raw) if pts_raw and pts_raw.strip() != '' else None
            except Exception:
                pts = None
            try:
                season = int(season_raw) if season_raw and season_raw.strip() != '' else None
            except Exception:
                season = None

            if not name:
                # skip rows without a name
                continue

            # first try to update an existing row for the same name+season
            cur.execute(
                """
                UPDATE drivers
                SET pos = ?, nationality = ?, team = ?, pts = ?
                WHERE name = ? AND season = ?
                """,
                (pos, nationality, team, pts, name, season),
            )
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO drivers (pos, name, nationality, team, pts, season) VALUES (?, ?, ?, ?, ?, ?)",
                    (pos, name, nationality, team, pts, season),
                )
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated

def create_results_table(conn):
    """Crea la tabla resultados si no existe."""
    sql = """
    CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grand_prix TEXT NOT NULL,
        winner TEXT,
        team TEXT,
        laps INTEGER,
        time TEXT,
        season INTEGER,
        UNIQUE(grand_prix, season)
    );
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        print("Error al crear la tabla resultados:", e)

def create_constructors_table(conn):
    """Crea la tabla constructors si no existe."""
    sql = """
    CREATE TABLE IF NOT EXISTS constructors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pos INTEGER,
        team TEXT NOT NULL,
        pts INTEGER,
        season INTEGER,
        UNIQUE(team, season)
    );
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        print("Error al crear la tabla constructors:", e)

def create_usuarios_table(conn):
    """Crea la tabla usuarios si no existe."""
    sql = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        apellido TEXT,
        email TEXT,
        contrasena TEXT,
        fecha_nacimiento TEXT,
        monto REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(email)
    );
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        print("Error al crear la tabla usuarios:", e)


def ensure_usuarios_monto_column(conn):
    """Asegura que la columna 'monto' exista en la tabla usuarios. Si no, la añade."""
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(usuarios)")
        cols = [r[1] for r in cur.fetchall()]
        if 'monto' not in cols:
            print("Añadiendo columna 'monto' a usuarios...")
            cur.execute("ALTER TABLE usuarios ADD COLUMN monto REAL DEFAULT 0.0")
            conn.commit()
    except Error as e:
        print("Error asegurando columna monto:", e)

def import_constructors_from_csv(conn, csv_path):
    """Importa Constructores desde CSV a la tabla constructors.

    Devuelve (inserted_count, updated_count).
    """
    inserted = 0
    updated = 0
    if not os.path.exists(csv_path):
        print(f"CSV de constructores no encontrado: {csv_path}")
        return inserted, updated

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        key_map = {normalize_key(k): k for k in reader.fieldnames}
        cur = conn.cursor()
        for row in reader:
            def g(k):
                key = key_map.get(k)
                return row.get(key) if key else None

            pos_raw = g('pos')
            team = g('team') or g('team')
            pts_raw = g('pts') or g('pts')
            season_raw = g('season')

            if team:
                team = team.replace('\xa0', ' ').strip()
            try:
                pos = int(pos_raw) if pos_raw and pos_raw.strip() != '' else None
            except Exception:
                pos = None
            try:
                pts = int(pts_raw) if pts_raw and pts_raw.strip() != '' else None
            except Exception:
                pts = None
            try:
                season = int(season_raw) if season_raw and season_raw.strip() != '' else None
            except Exception:
                season = None

            if not team:
                continue

            cur.execute(
                "UPDATE constructors SET pos = ?, pts = ? WHERE team = ? AND season = ?",
                (pos, pts, team, season),
            )
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO constructors (pos, team, pts, season) VALUES (?, ?, ?, ?)",
                    (pos, team, pts, season),
                )
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated

def create_race_results_detailed_table(conn):
    """Crea una tabla para resultados de carrera detallados (all seasons / per-season)."""
    sql = """
    CREATE TABLE IF NOT EXISTS race_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track TEXT,
        position TEXT,
        car_no TEXT,
        driver TEXT,
        team TEXT,
        starting_grid INTEGER,
        laps INTEGER,
        time_retired TEXT,
        points REAL,
        plus1pt TEXT,
        fastest_lap TEXT,
        season INTEGER,
        fastest_lap_time TEXT,
        UNIQUE(track, position, car_no, season)
    );
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        print("Error al crear la tabla race_results:", e)

def import_race_results_from_csv(conn, csv_path):
    """Importa un CSV de race results (varios formatos) a la tabla race_results.

    Devuelve (inserted_count, updated_count).
    """
    inserted = 0
    updated = 0
    if not os.path.exists(csv_path):
        print(f"CSV de race results no encontrado: {csv_path}")
        return inserted, updated

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        key_map = {normalize_key(k): k for k in reader.fieldnames}
        cur = conn.cursor()
        for row in reader:
            def g(k):
                key = key_map.get(k)
                return row.get(key) if key else None

            track = g('track') or g('grandprix') or g('grand_prix')
            position = g('position') or g('pos')
            car_no = g('no') or g('number')
            driver = g('driver')
            team = g('team')
            starting_grid_raw = g('startinggrid') or g('starting_grid') or g('grid')
            laps_raw = g('laps')
            time_retired = g('time/retired') or g('time') or g('time_retired') or g('time/retired')
            points_raw = g('points')
            plus1pt = g('+1pt') or g('plus1pt') or g('plus_1_pt')
            fastest_lap = g('setfastestlap') or g('set fastest lap') or g('set fastest lap') or g('set fastest lap')
            fastest_lap_time = g('fastestlaptime') or g('fastest lap time') or g('fastest_lap_time')
            season_raw = g('season')

            if track:
                track = track.replace('\xa0', ' ').strip()
            if driver:
                driver = driver.replace('\xa0', ' ').strip()

            try:
                starting_grid = int(starting_grid_raw) if starting_grid_raw and starting_grid_raw.strip() != '' else None
            except Exception:
                starting_grid = None
            try:
                laps = int(laps_raw) if laps_raw and laps_raw.strip() != '' else None
            except Exception:
                laps = None
            try:
                points = float(points_raw) if points_raw and points_raw.strip() != '' else None
            except Exception:
                points = None
            try:
                season = int(season_raw) if season_raw and season_raw.strip() != '' else None
            except Exception:
                season = None

            if not track:
                continue

            cur.execute(
                """
                UPDATE race_results
                SET driver = ?, team = ?, starting_grid = ?, laps = ?, time_retired = ?, points = ?, plus1pt = ?, fastest_lap = ?, fastest_lap_time = ?
                WHERE track = ? AND position = ? AND car_no = ? AND season = ?
                """,
                (driver, team, starting_grid, laps, time_retired, points, plus1pt, fastest_lap, fastest_lap_time, track, position, car_no, season),
            )
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO race_results (track, position, car_no, driver, team, starting_grid, laps, time_retired, points, plus1pt, fastest_lap, season, fastest_lap_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (track, position, car_no, driver, team, starting_grid, laps, time_retired, points, plus1pt, fastest_lap, season, fastest_lap_time),
                )
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated

def import_results_from_csv(conn, csv_path):
    """Importa filas desde el CSV de resultados a la tabla resultados.

    Devuelve (inserted_count, updated_count).
    """
    inserted = 0
    updated = 0
    if not os.path.exists(csv_path):
        print(f"CSV de resultados no encontrado: {csv_path}")
        return inserted, updated

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        key_map = {normalize_key(k): k for k in reader.fieldnames}
        cur = conn.cursor()
        for row in reader:
            def g(k):
                key = key_map.get(k)
                return row.get(key) if key else None

            grand_prix = g('grandprix') or g('grand_prix') or g('grand')
            winner = g('winner')
            team = g('team')
            laps_raw = g('laps')
            time = g('time')
            season_raw = g('seson') or g('season')

            if grand_prix:
                grand_prix = grand_prix.replace('\xa0', ' ').strip()
            if winner:
                winner = winner.replace('\xa0', ' ').strip()

            try:
                laps = int(laps_raw) if laps_raw and laps_raw.strip() != '' else None
            except Exception:
                laps = None
            try:
                season = int(season_raw) if season_raw and season_raw.strip() != '' else None
            except Exception:
                season = None

            if not grand_prix:
                continue

            cur.execute(
                """
                UPDATE resultados
                SET winner = ?, team = ?, laps = ?, time = ?
                WHERE grand_prix = ? AND season = ?
                """,
                (winner, team, laps, time, grand_prix, season),
            )
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO resultados (grand_prix, winner, team, laps, time, season) VALUES (?, ?, ?, ?, ?, ?)",
                    (grand_prix, winner, team, laps, time, season),
                )
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated

def main():
    # Use the database file located in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'f1_app.db')
    csv_path = CSV_FILE
    # if a CSV path is passed as argument, use it
    if len(os.sys.argv) > 1:
        csv_path = os.sys.argv[1]

    conn = create_connection(db_path)
    if not conn:
        return

    create_table_drivers(conn)
    inserted, updated = import_from_csv(conn, csv_path)
    print(f"Import finished. Inserted: {inserted}, Updated: {updated}")

    print("Sample rows:")
    cur = conn.cursor()
    for row in cur.execute("SELECT id, pos, name, team, pts, season FROM drivers ORDER BY season DESC, pts DESC LIMIT 20"):
        print(row)
    
    # Crear e importar resultados si existe el CSV correspondiente
    create_results_table(conn)
    results_inserted, results_updated = import_results_from_csv(conn, RESULTS_CSV)
    print(f"Resultados import finished. Inserted: {results_inserted}, Updated: {results_updated}")
    print("Sample resultados:")
    for r in cur.execute("SELECT id, grand_prix, winner, team, laps, time, season FROM resultados ORDER BY season DESC LIMIT 20"):
        print(r)

    # Crear e importar constructores
    create_constructors_table(conn)
    cons_inserted, cons_updated = import_constructors_from_csv(conn, CONSTRUCTORS_CSV)
    print(f"Constructors import finished. Inserted: {cons_inserted}, Updated: {cons_updated}")
    print("Sample constructors:")
    for c in cur.execute("SELECT id, pos, team, pts, season FROM constructors ORDER BY season DESC, pts DESC LIMIT 20"):
        print(c)

    # Crear e importar resultados de carrera detallados (all seasons y season-specific)
    create_race_results_detailed_table(conn)
    rr_inserted_all, rr_updated_all = import_race_results_from_csv(conn, ALLSEASONS_CSV)
    print(f"Race results (all seasons) import finished. Inserted: {rr_inserted_all}, Updated: {rr_updated_all}")
    rr_inserted_2025, rr_updated_2025 = import_race_results_from_csv(conn, SEASON2025_CSV)
    print(f"Race results (2025 season) import finished. Inserted: {rr_inserted_2025}, Updated: {rr_updated_2025}")
    print("Sample race_results:")
    for rr in cur.execute("SELECT id, track, position, driver, team, season FROM race_results ORDER BY season DESC LIMIT 20"):
        print(rr)

    # Crear la tabla de usuarios (si no existe) y mostrar muestra
    create_usuarios_table(conn)
    ensure_usuarios_monto_column(conn)
    try:
        users_count = cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    except Exception:
        users_count = 0
    print(f"Usuarios table present. Rows: {users_count}")
    for u in cur.execute("SELECT id, nombre, apellido, email, fecha_nacimiento, created_at FROM usuarios LIMIT 10"):
        print(u)

    conn.close()

if __name__ == '__main__':
    main()

