
import requests

# Coordenadas de nuestra parcela en Ica, Perú
latitud = -14.0678
longitud = -75.7286

# Servicio oficial de NASA POWER
url = "https://power.larc.nasa.gov/api/temporal/daily/point"

parametros = {
    "parameters": "T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
    "community": "AG",
    "longitude": longitud,
    "latitude": latitud,
    "start": "20250101",
    "end": "20250107",
    "format": "JSON"
}

try:
    respuesta = requests.get(
        url, params=parametros, timeout=60
    )
    respuesta.raise_for_status()

    datos = respuesta.json()
    clima = datos["properties"]["parameter"]

    print("CONEXION EXITOSA CON NASA POWER")
    print("Ubicacion: Ica, Peru")
    print()

    for fecha, temperatura in clima["T2M"].items():
        lluvia = clima["PRECTOTCORR"].get(fecha)
        radiacion = clima["ALLSKY_SFC_SW_DWN"].get(fecha)

        print("Fecha:", fecha)
        print("Temperatura:", temperatura)
        print("Precipitacion:", lluvia)
        print("Radiacion solar:", radiacion)
        print("--------------------")

except requests.RequestException as error:
    print("Error de conexion:", error)
except (KeyError, ValueError) as error:
    print("Error al leer los datos:", error)
