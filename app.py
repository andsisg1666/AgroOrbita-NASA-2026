from flask import Flask, render_template, request, redirect, url_for, session



import sqlite3
from pathlib import Path


from werkzeug.security import generate_password_hash, check_password_hash

import os
import secrets
from datetime import date



# Creamos nuestra aplicación Flask
app = Flask(__name__)

# Clave secreta para las sesiones de usuarios
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)


# Ubicación de nuestra base de datos SQLite
RUTA_BD = Path(__file__).resolve().parent / "agroorbita.db"

# PASO 14.8: Proteger las páginas agrícolas
@app.before_request
def proteger_paginas():

    rutas_protegidas = [
        "/terrenos",
        "/registrar-terreno",
        "/editar-terreno",
        "/eliminar-terreno"
    ]

    for ruta in rutas_protegidas:
        if request.path == ruta or request.path.startswith(ruta + "/"):

            if "usuario_id" not in session:
                return redirect(url_for("iniciar_sesion"))


# Página principal
@app.route("/")
def inicio():
    return render_template("index.html")


# Comprobar la conexión con SQLite
@app.route("/verificar-bd")
def verificar_bd():

    if not RUTA_BD.exists():
        return "No se encontró agroorbita.db", 500

    conexion = sqlite3.connect(RUTA_BD)

    try:
        tabla = conexion.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='terrenos'"
        ).fetchone()
    finally:
        conexion.close()

    if tabla:
        return "Conexión correcta: la tabla terrenos existe en SQLite."

    return "No se encontró la tabla terrenos.", 500



# Mostrar el formulario y guardar terrenos en SQLite
@app.route("/registrar-terreno", methods=["GET", "POST"])
def mostrar_formulario_terreno():

    # Mostrar el formulario
    if request.method == "GET":
        return render_template("registrar_terreno.html")

    # Recibir y comprobar los datos del formulario
    try:
        nombre = request.form["nombre"].strip()
        ubicacion = request.form["ubicacion"].strip()
        latitud = float(request.form["latitud"])
        longitud = float(request.form["longitud"])
        cultivo_actual = request.form["cultivo_actual"].strip()
        tipo_suelo = request.form["tipo_suelo"].strip()
        superficie = float(request.form["superficie"])
        prioridad = request.form["prioridad"].strip()
    except (KeyError, ValueError):
        return "Error: revisa los datos ingresados.", 400

    if not all([nombre, ubicacion, cultivo_actual,
                tipo_suelo, prioridad]):
        return "Error: completa todos los campos.", 400

    if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
        return "Error: coordenadas incorrectas.", 400

    if superficie <= 0:
        return "Error: la superficie debe ser mayor que cero.", 400

    # Conectar con nuestra base de datos
    conexion = sqlite3.connect(RUTA_BD)

    try:
        conexion.execute(
            """
            INSERT INTO terrenos
            (nombre, ubicacion, latitud, longitud,
             cultivo_actual, tipo_suelo, superficie, prioridad, usuario_id)
            
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            """,
            (nombre, ubicacion, latitud, longitud,
             cultivo_actual, tipo_suelo, superficie, prioridad, session["usuario_id"])
        )

        conexion.commit()

    finally:
        conexion.close()

    return (
        "Terreno registrado correctamente en SQLite. "
        "<a href='/registrar-terreno'>Registrar otro terreno</a>"
    )


# Mostrar todos los terrenos registrados
@app.route("/terrenos", methods=["GET"])
def listar_terrenos():

    # Conectar con SQLite
    conexion = sqlite3.connect(RUTA_BD)

    # Permitir consultar las columnas por su nombre
    conexion.row_factory = sqlite3.Row

    try:
        # Consultar los terrenos registrados
        terrenos = conexion.execute(
        "SELECT * FROM terrenos WHERE usuario_id = ? ORDER BY id DESC",
        (session["usuario_id"],)
        ).fetchall()

    finally:
        # Cerrar la conexión
        conexion.close()

    # Mostrar los terrenos en nuestra página HTML
    return render_template(
        "listar_terrenos.html",
        terrenos=terrenos
    )


# Editar un terreno agrícola existente
@app.route("/editar-terreno/<int:terreno_id>",
           methods=["GET", "POST"])
def editar_terreno(terreno_id):

    # Conectamos con SQLite
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row

    # Mostrar el formulario con los datos existentes
    if request.method == "GET":

        terreno = conexion.execute(
            "SELECT * FROM terrenos WHERE id = ? AND usuario_id = ?",
            (terreno_id, session["usuario_id"])
        ).fetchone()


        conexion.close()

        if terreno is None:
            return "Terreno no encontrado.", 404

        return render_template(
            "editar_terreno.html",
            terreno=terreno
        )

    # Recibir los datos modificados
    try:
        nombre = request.form["nombre"].strip()
        ubicacion = request.form["ubicacion"].strip()
        latitud = float(request.form["latitud"])
        longitud = float(request.form["longitud"])
        cultivo_actual = request.form["cultivo_actual"].strip()
        tipo_suelo = request.form["tipo_suelo"].strip()
        superficie = float(request.form["superficie"])
        prioridad = request.form["prioridad"].strip()

    except (KeyError, ValueError):
        conexion.close()
        return "Error: revisa los datos ingresados.", 400

    # Validar los campos
    if not all([nombre, ubicacion, cultivo_actual,
                tipo_suelo, prioridad]):
        conexion.close()
        return "Debes completar todos los campos.", 400

    if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
        conexion.close()
        return "Coordenadas incorrectas.", 400

    if not (0 < superficie < float("inf")):
        conexion.close()
        return "La superficie debe ser positiva y válida.", 400

    # Actualizar los datos en SQLite
    try:
        cursor = conexion.execute(
            """
            UPDATE terrenos
            SET nombre = ?,
                ubicacion = ?,
                latitud = ?,
                longitud = ?,
                cultivo_actual = ?,
                tipo_suelo = ?,
                superficie = ?,
                prioridad = ?
WHERE id = ? AND usuario_id = ?

            """,
            (
                nombre,
                ubicacion,
                latitud,
                longitud,
                cultivo_actual,
                tipo_suelo,
                superficie,
                prioridad,
                terreno_id,

                session["usuario_id"]

            )
        )

        actualizados = cursor.rowcount
        conexion.commit()

    finally:
        conexion.close()

    if actualizados == 0:
        return "Terreno no encontrado.", 404

    # Regresar a la lista de terrenos
    return redirect(url_for("listar_terrenos"))

# Eliminar un terreno agrícola de SQLite
@app.route("/eliminar-terreno/<int:terreno_id>",
           methods=["POST"])
def eliminar_terreno(terreno_id):

    # Conectamos con nuestra base de datos
    conexion = sqlite3.connect(RUTA_BD)

    try:
        # Buscar y eliminar el terreno por su ID
        cursor = conexion.execute(
            "DELETE FROM terrenos WHERE id = ? AND usuario_id = ?",
        
             (terreno_id, session["usuario_id"])

        )

        eliminados = cursor.rowcount

        # Guardamos los cambios
        conexion.commit()

    finally:
        conexion.close()

    # Comprobar si el terreno existía
    if eliminados == 0:
        return "Terreno no encontrado.", 404

    # Volver a la lista de terrenos
    return redirect(url_for("listar_terrenos"))


# PASO 13.3: Registro de usuarios
@app.route("/registrar-usuario", methods=["GET", "POST"])
def registrar_usuario():

    if request.method == "GET":
        return render_template("registrar_usuario.html")

    nombre = request.form.get("nombre", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    contrasena = request.form.get("contrasena", "")
    confirmar = request.form.get("confirmar_contrasena", "")

    if not nombre or not correo or not contrasena:
        return "Debes completar todos los campos.", 400

    if len(contrasena) < 8:
        return "La contraseña debe tener al menos 8 caracteres.", 400

    if contrasena != confirmar:
        return "Las contraseñas no coinciden.", 400

    contrasena_hash = generate_password_hash(contrasena)

    conexion = sqlite3.connect(RUTA_BD)

    try:
        conexion.execute(
            """
            INSERT INTO usuarios
            (nombre, correo, contrasena_hash, rol)
            VALUES (?, ?, ?, ?)
            """,
            (nombre, correo, contrasena_hash, "agricultor")
        )

        conexion.commit()

    except sqlite3.IntegrityError:
        return "Este correo ya está registrado.", 409

    finally:
        conexion.close()

    return (
        "Cuenta creada correctamente en AgroÓrbita. "
        "<a href='/registrar-usuario'>Volver al registro</a>"
    ), 201


# PASO 14.3: Inicio de sesión de usuarios
@app.route("/iniciar-sesion", methods=["GET", "POST"])
def iniciar_sesion():

    if request.method == "GET":
        return render_template("iniciar_sesion.html")

    correo = request.form.get("correo", "").strip().lower()
    contrasena = request.form.get("contrasena", "")

    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row

    try:
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE correo = ?",
            (correo,)
        ).fetchone()
    finally:
        conexion.close()

    if usuario is None or not check_password_hash(
        usuario["contrasena_hash"], contrasena
    ):
        return "Correo o contraseña incorrectos.", 401

    # Guardar los datos del usuario en la sesión
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["usuario_nombre"] = usuario["nombre"]
    session["usuario_rol"] = usuario["rol"]

    return redirect(url_for("listar_terrenos"))


# PASO 14.5: Cerrar sesión del usuario
@app.route("/cerrar-sesion", methods=["POST"])
def cerrar_sesion():

    # Eliminar los datos de la sesión
    session.clear()

    # Regresar al inicio de sesión
    return redirect(url_for("iniciar_sesion"))



# PASO 16: Consultar datos climaticos de NASA POWER
@app.route("/clima/<int:terreno_id>")
def consultar_clima(terreno_id):
    import requests
    from flask import jsonify
    from contextlib import closing
    from datetime import date

    # Comprobar que el agricultor inicio sesion
    if "usuario_id" not in session:
        return "Debes iniciar sesion.", 401

    # Buscar solamente terrenos del usuario
    with closing(sqlite3.connect(RUTA_BD)) as conexion:
        terreno = conexion.execute(
            """
            SELECT nombre, latitud, longitud
            FROM terrenos
            WHERE id = ? AND usuario_id = ?
            """,
            (terreno_id, session["usuario_id"])
        ).fetchone()

    if terreno is None:
        return "Terreno no encontrado.", 404
    nombre, latitud, longitud = terreno


    # Fechas seleccionadas por el agricultor
    fecha_inicio = request.args.get("inicio", "2025-01-01")
    fecha_fin = request.args.get("fin", "2025-01-07")

    try:
        inicio_dt = date.fromisoformat(fecha_inicio)
        fin_dt = date.fromisoformat(fecha_fin)
    except ValueError:
        return "Formato de fecha incorrecto.", 400

    # Validar las fechas seleccionadas
    if inicio_dt > fin_dt:
        return "La fecha inicial debe ser anterior a la final.", 400

    if inicio_dt < date(1981, 1, 1) or fin_dt > date.today():
        return "Las fechas están fuera del periodo permitido.", 400

    if (fin_dt - inicio_dt).days > 30:
        return "Selecciona un periodo máximo de 31 días.", 400


    # Consultar datos historicos de NASA
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    parametros = {
        "parameters": "T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "latitude": latitud,
        "longitude": longitud,
        
        "start": inicio_dt.strftime("%Y%m%d"),
        "end": fin_dt.strftime("%Y%m%d"),

        "format": "JSON"
    }

    try:
        respuesta = requests.get(
            url, params=parametros, timeout=60
        )
        respuesta.raise_for_status()
        clima = respuesta.json()["properties"]["parameter"]

    except (requests.RequestException, KeyError, ValueError):
        return "No se pudieron consultar los datos de NASA.", 502


    return render_template(
        "clima.html",
        terreno=nombre,
        periodo="01 al 07 de enero de 2025",
        temperatura=clima["T2M"],
        precipitacion=clima["PRECTOTCORR"],
        radiacion_solar=clima["ALLSKY_SFC_SW_DWN"]
    )




# Ejecutamos nuestra aplicación
if __name__ == "__main__":
    app.run(debug=True, port=5000)
