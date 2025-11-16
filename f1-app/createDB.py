import csv
import os
import sqlite3
from sqlite3 import Error

# CSV files
CSV_FILE = "Pilotos_2023_2024 (1).csv"
RESULTS_CSV = "resultado_races.csv"
CONSTRUCTORS_CSV = "Constructores_2023_2024.csv"
ALLSEASONS_CSV = "Formula1_AllSeasons_RaceResults_withSeason.csv"
SEASON2025_CSV = "Formula1_2025Season_RaceResults.csv"


# ----------------------------------------------
# CONEXIÓN
# ----------------------------------------------
def create_connection(db_file):
    """Crea una conexión a la base de datos SQLite (crea el archivo si no existe)."""
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print("Error al conectar:", e)
        return None


# ----------------------------------------------
# TABLA DRIVERS
# ----------------------------------------------
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
        print("Error al crear la tabla drivers:", e)


def normalize_key(s):
    if s is None:
        return ''
    return s.strip().lower().replace('.', '').replace(' ', '')


def import_from_csv(conn, csv_path):
    """Importa filas desde el CSV a la tabla drivers. Devuelve (inserted_count, updated_count)."""
    inserted = 0
    updated = 0
    if not os.path.exists(csv_path):
        print(f"CSV no encontrado: {csv_path}")
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
            name = g('driver') or g('name')
            nationality = g('nationality')
            team = g('team')
            pts_raw = g('pts')
            season_raw = g('season')

            # Normalización
            if name:
                name = name.replace('\xa0', ' ').strip()

            try: pos = int(pos_raw) if pos_raw else None
            except: pos = None
            try: pts = int(pts_raw) if pts_raw else None
            except: pts = None
            try: season = int(season_raw) if season_raw else None
            except: season = None

            if not name:
                continue

            cur.execute("""
                UPDATE drivers
                SET pos=?, nationality=?, team=?, pts=?
                WHERE name=? AND season=?
            """, (pos, nationality, team, pts, name, season))

            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO drivers (pos, name, nationality, team, pts, season)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pos, name, nationality, team, pts, season))
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated


# ----------------------------------------------
# TABLA RESULTADOS
# ----------------------------------------------
def create_results_table(conn):
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
        conn.execute(sql)
        conn.commit()
    except Error as e:
        print("Error al crear tabla resultados:", e)


# ----------------------------------------------
# TABLA CONSTRUCTORS
# ----------------------------------------------
def create_constructors_table(conn):
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
        conn.execute(sql)
        conn.commit()
    except:
        pass


# ----------------------------------------------
# TABLA USUARIOS
# ----------------------------------------------
def create_usuarios_table(conn):
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
        conn.execute(sql)
        conn.commit()
    except:
        pass


def ensure_usuarios_monto_column(conn):
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(usuarios)")
        cols = [r[1] for r in cur.fetchall()]
        if 'monto' not in cols:
            print("Añadiendo columna 'monto' a usuarios...")
            cur.execute("ALTER TABLE usuarios ADD COLUMN monto REAL DEFAULT 0.0")
            conn.commit()
    except:
        pass


# ----------------------------------------------
# TABLA APUESTAS (NUEVA)
# ----------------------------------------------
def create_apuestas_table(conn):
    """Crea la tabla apuestas si no existe."""
    sql = """
    CREATE TABLE IF NOT EXISTS apuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        piloto1 TEXT NOT NULL,
        piloto2 TEXT NOT NULL,
        piloto3 TEXT NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn.execute(sql)
        conn.commit()
        print("Tabla 'apuestas' verificada/creada correctamente.")
    except Error as e:
        print("Error al crear tabla apuestas:", e)


# ----------------------------------------------
# CONSTRUCTORES Y RACE RESULTS
# (no modifico nada de tu código original)
# ----------------------------------------------
def import_constructors_from_csv(conn, csv_path):
    inserted = updated = 0
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
            team = g('team')
            pts_raw = g('pts')
            season_raw = g('season')

            if team:
                team = team.replace('\xa0', ' ')

            try: pos = int(pos_raw) if pos_raw else None
            except: pos = None
            try: pts = int(pts_raw) if pts_raw else None
            except: pts = None
            try: season = int(season_raw) if season_raw else None
            except: season = None

            cur.execute(
                "UPDATE constructors SET pos=?, pts=? WHERE team=? AND season=?",
                (pos, pts, team, season)
            )
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO constructors (pos, team, pts, season) VALUES (?, ?, ?, ?)",
                    (pos, team, pts, season)
                )
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated


def create_race_results_detailed_table(conn):
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
        conn.execute(sql)
        conn.commit()
    except:
        pass


def import_race_results_from_csv(conn, csv_path):
    inserted = updated = 0
    if not os.path.exists(csv_path):
        print(f"CSV no encontrado: {csv_path}")
        return inserted, updated

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        key_map = {normalize_key(k): k for k in reader.fieldnames}
        cur = conn.cursor()

        for row in reader:
            def g(k):
                key = key_map.get(k)
                return row.get(key) if key else None

            track = g('track') or g('grandprix')
            position = g('position')
            car_no = g('carno') or g('no')
            driver = g('driver')
            team = g('team')
            starting_grid_raw = g('startinggrid')
            laps_raw = g('laps')
            time_retired = g('time') or g('retired')
            points_raw = g('points')
            plus1pt = g('plus1pt')
            fastest_lap = g('fastestlap')
            fastest_lap_time = g('fastestlaptime')
            season_raw = g('season')

            if track:
                track = track.replace('\xa0', ' ').strip()
            if driver:
                driver = driver.replace('\xa0', ' ').strip()

            try: starting_grid = int(starting_grid_raw) if starting_grid_raw else None
            except: starting_grid = None
            try: laps = int(laps_raw) if laps_raw else None
            except: laps = None
            try: points = float(points_raw) if points_raw else None
            except: points = None
            try: season = int(season_raw) if season_raw else None
            except: season = None

            if not track:
                continue

            cur.execute("""
                UPDATE race_results SET driver=?, team=?, starting_grid=?, laps=?, time_retired=?, points=?, 
                    plus1pt=?, fastest_lap=?, fastest_lap_time=?
                WHERE track=? AND position=? AND car_no=? AND season=?
            """, (driver, team, starting_grid, laps, time_retired, points, plus1pt, fastest_lap, fastest_lap_time,
                  track, position, car_no, season))

            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO race_results (
                        track, position, car_no, driver, team, starting_grid, laps, time_retired, 
                        points, plus1pt, fastest_lap, season, fastest_lap_time
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (track, position, car_no, driver, team, starting_grid, laps, time_retired,
                      points, plus1pt, fastest_lap, season, fastest_lap_time))

                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated


# ----------------------------------------------
# IMPORTAR RESULTADOS
# ----------------------------------------------
def import_results_from_csv(conn, csv_path):
    inserted = updated = 0
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

            grand_prix = g('grandprix') or g('grand_prix')
            winner = g('winner')
            team = g('team')
            laps_raw = g('laps')
            time = g('time')
            season_raw = g('season')

            if grand_prix:
                grand_prix = grand_prix.replace('\xa0', ' ')

            try: laps = int(laps_raw) if laps_raw else None
            except: laps = None
            try: season = int(season_raw) if season_raw else None
            except: season = None

            if not grand_prix:
                continue

            cur.execute("""
                UPDATE resultados SET winner=?, team=?, laps=?, time=?
                WHERE grand_prix=? AND season=?
            """, (winner, team, laps, time, grand_prix, season))

            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO resultados (grand_prix, winner, team, laps, time, season)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (grand_prix, winner, team, laps, time, season))
                inserted += 1
            else:
                updated += 1

        conn.commit()

    return inserted, updated


# ----------------------------------------------
# MAIN
# ----------------------------------------------
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'f1_app.db')
    csv_path = CSV_FILE

    if len(os.sys.argv) > 1:
        csv_path = os.sys.argv[1]

    conn = create_connection(db_path)
    if not conn:
        return

    # Crear tablas principales
    create_table_drivers(conn)
    inserted, updated = import_from_csv(conn, csv_path)
    print(f"Import finished. Inserted: {inserted}, Updated: {updated}")

    cur = conn.cursor()
    print("Sample rows:")
    for row in cur.execute("SELECT id, pos, name, team, pts, season FROM drivers ORDER BY season DESC, pts DESC LIMIT 20"):
        print(row)

    # Resultados
    create_results_table(conn)
    r_i, r_u = import_results_from_csv(conn, RESULTS_CSV)
    print(f"Resultados import finished. Inserted: {r_i}, Updated: {r_u}")

    # Constructores
    create_constructors_table(conn)
    c_i, c_u = import_constructors_from_csv(conn, CONSTRUCTORS_CSV)
    print(f"Constructors import finished. Inserted: {c_i}, Updated: {c_u}")

    # Race results (ALL + 2025)
    create_race_results_detailed_table(conn)
    rr_all_i, rr_all_u = import_race_results_from_csv(conn, ALLSEASONS_CSV)
    rr25_i, rr25_u = import_race_results_from_csv(conn, SEASON2025_CSV)
    print(f"Race results import finished. Inserted: {rr_all_i + rr25_i}, Updated: {rr_all_u + rr25_u}")

    # Usuarios
    create_usuarios_table(conn)
    ensure_usuarios_monto_column(conn)

    # APUESTAS (NUEVA TABLA)
    create_apuestas_table(conn)

    print("Usuarios count:")
    try:
        print(cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0])
    except:
        pass

    conn.close()


if __name__ == '__main__':
    main()
