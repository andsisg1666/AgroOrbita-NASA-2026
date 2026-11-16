"""AgroÓrbita — diagnóstico y exportación de esquema SIN filas de datos.

python preparar_render.py revisar  -> Inspecciona base local y app.py (solo lectura)
python preparar_render.py exportar -> Crea esquema.sql a partir de tablas reales
python preparar_render.py iniciar -> Crea tablas faltantes en Render usando esquema.sql

NO eliminar ni reemplazar la base de datos original.
"""
from pathlib import Path
from contextlib import closing
import ast
import re
import sqlite3
import sys

CARPETA = Path(__file__).resolve().parent
BASE = CARPETA / "agroorbita.db"
ESQUEMA = CARPETA / "esquema.sql"
APP = CARPETA / "app.py"


def _conexion_lectura():
    if not BASE.is_file():
        raise SystemExit(f"ERROR: no existe {BASE.name} junto a este script. Revisa la carpeta.")
    uri = BASE.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def revisar():
    print("=== REVISION LOCAL DE AGROORBITA ===")
    print(f"Carpeta del proyecto: {CARPETA.name}")
    print("Base SQLite encontrada:", BASE.is_file())
    print("app.py encontrado:", APP.is_file())
    print("requirements.txt encontrado:", (CARPETA / "requirements.txt").is_file())
    print("templates encontrado:", (CARPETA / "templates").is_dir())
    if APP.is_file():
        try:
            ast.parse(APP.read_text(encoding="utf-8-sig"), filename="app.py")
            print("Sintaxis de app.py: OK")
        except (SyntaxError, UnicodeError) as exc:
            print("Sintaxis de app.py: ERROR", exc)
    with closing(_conexion_lectura()) as con:
        ok = con.execute("PRAGMA quick_check").fetchone()[0]
        print("Integridad SQLite:", ok)
        filas = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        print("Tablas reales encontradas:", len(filas))
        for (nombre,) in filas:
            qnombre = '"' + nombre.replace('"', '""') + '"'
            total = con.execute(f"SELECT COUNT(*) FROM {qnombre}").fetchone()[0]
            print(f"  - {nombre}: {total} registro(s)")
    print("No se modificó ni se copió ningún registro de tu base.")
    print("IMPORTANTE: el resultado de Render es independiente de tu base local.")


def exportar():
    with closing(_conexion_lectura()) as con:
        objetos = con.execute("""SELECT type, name, sql FROM sqlite_master
            WHERE type IN ('table','index','view','trigger')
            AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL
            ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1
                    WHEN 'view' THEN 2 ELSE 3 END, name""").fetchall()
    tablas = [name for tipo, name, _ in objetos if tipo == 'table']
    if not tablas:
        raise SystemExit("ERROR: la base no tiene tablas; no se generó ningún esquema.")
    comandos = ["-- Esquema de AgroÓrbita. Solo estructura, SIN registros privados."]
    for tipo, nombre, sql in objetos:
        if tipo == "table":
            sql = re.sub(r"^(CREATE\s+(?:VIRTUAL\s+)?TABLE\s+)(?!IF\s+NOT\s+EXISTS\b)",
                         r"\1IF NOT EXISTS ", sql, count=1, flags=re.IGNORECASE)
        elif tipo == "index":
            sql = re.sub(r"^(CREATE\s+(?:UNIQUE\s+)?INDEX\s+)(?!IF\s+NOT\s+EXISTS\b)",
                         r"\1IF NOT EXISTS ", sql, count=1, flags=re.IGNORECASE)
        elif tipo == "view":
            sql = re.sub(r"^(CREATE\s+VIEW\s+)(?!IF\s+NOT\s+EXISTS\b)",
                         r"\1IF NOT EXISTS ", sql, count=1, flags=re.IGNORECASE)
        elif tipo == "trigger":
            sql = re.sub(r"^(CREATE\s+TRIGGER\s+)(?!IF\s+NOT\s+EXISTS\b)",
                         r"\1IF NOT EXISTS ", sql, count=1, flags=re.IGNORECASE)
        comandos.append(sql.strip().rstrip(";") + ";")
    contenido = "\n\n".join(comandos) + "\n"
    # Verificación de que las tablas se pueden crear en una base VACÍA.
    with closing(sqlite3.connect(":memory:")) as prueba:
        prueba.executescript(contenido)
        creada = {r[0] for r in prueba.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not set(tablas).issubset(creada):
            raise SystemExit("ERROR: no se pudieron crear todas las tablas en la prueba; esquema no publicado.")
    ESQUEMA.write_text(contenido, encoding="utf-8")
    print(f"OK: esquema.sql creado con {len(tablas)} tabla(s).")
    print("El esquema pasó la prueba de creación en SQLite vacío.")
    print("No se exportaron usuarios, contraseñas ni terrenos.")


def iniciar():
    if not ESQUEMA.is_file():
        raise SystemExit("ERROR: falta esquema.sql; ejecuta 'exportar' en tu laptop y súbelo a GitHub.")
    with closing(sqlite3.connect(BASE)) as con:
        con.executescript(ESQUEMA.read_text(encoding="utf-8"))
        con.commit()
        tablas = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
    print(f"OK: SQLite inicializado: {tablas} tabla(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"revisar", "exportar", "iniciar"}:
        raise SystemExit("Uso: python preparar_render.py revisar | exportar | iniciar")
    {"revisar": revisar, "exportar": exportar, "iniciar": iniciar}[sys.argv[1]]()
