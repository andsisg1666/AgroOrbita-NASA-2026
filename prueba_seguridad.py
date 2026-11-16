
from pathlib import Path
import sqlite3
import shutil
import tempfile

import app as proyecto

from contextlib import closing


# Ubicar nuestra base de datos de prueba
carpeta_proyecto = Path(__file__).resolve().parent
origen = carpeta_proyecto / "RESPALDO" / "agroorbita_prueba.db"

if not origen.exists():
    raise SystemExit("ERROR: No se encontró agroorbita_prueba.db")

# Crear otra copia temporal para no modificar los respaldos
with tempfile.TemporaryDirectory() as carpeta:
    base_prueba = Path(carpeta) / "prueba_temporal.db"
    shutil.copy2(origen, base_prueba)

    # Verificar los terrenos antes de la prueba    
    with closing(sqlite3.connect(base_prueba)) as conexion:

        antes = conexion.execute(
            "SELECT id, usuario_id FROM terrenos ORDER BY id"
        ).fetchall()

    if (1, 1) not in antes:
        raise SystemExit("ERROR: El terreno 1 no pertenece al usuario 1.")

    # Utilizar exclusivamente la base temporal
    ruta_original = proyecto.RUTA_BD
    proyecto.RUTA_BD = str(base_prueba)

    try:
        proyecto.app.config["TESTING"] = True

        with proyecto.app.test_client() as cliente:
            # Simular la sesión del agricultor 2
            with cliente.session_transaction() as sesion:
                sesion["usuario_id"] = 2
                sesion["usuario_nombre"] = "Agricultor prueba2"
                sesion["usuario_rol"] = "agricultor"

            # Intentar eliminar el terreno del agricultor 1
            respuesta = cliente.post("/eliminar-terreno/1")

    finally:
        proyecto.RUTA_BD = ruta_original

    # Comprobar que los terrenos siguen intactos    
    with closing(sqlite3.connect(base_prueba)) as conexion:

        despues = conexion.execute(
            "SELECT id, usuario_id FROM terrenos ORDER BY id"
        ).fetchall()

    print("Respuesta HTTP:", respuesta.status_code)
    print("Terrenos antes:", antes)
    print("Terrenos después:", despues)

    if respuesta.status_code == 404 and antes == despues:
        print("PRUEBA EXITOSA: Eliminación ajena bloqueada.")
    else:
        print("PRUEBA FALLIDA: Revisar la seguridad.")
        raise SystemExit(1)
