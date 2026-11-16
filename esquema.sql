-- Esquema de AgroÓrbita. Solo estructura, SIN registros privados.

CREATE TABLE IF NOT EXISTS "terrenos" (
	"id"	INTEGER,
	"nombre"	TEXT NOT NULL,
	"ubicacion"	TEXT NOT NULL,
	"latitud"	REAL NOT NULL,
	"longitud"	REAL NOT NULL,
	"cultivo_actual"	TEXT NOT NULL,
	"tipo_suelo"	TEXT NOT NULL,
	"superficie"	REAL NOT NULL,
	"prioridad"	TEXT NOT NULL, usuario_id INTEGER REFERENCES usuarios(id),
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    contrasena_hash TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'agricultor'
        CHECK (rol IN ('administrador', 'agricultor')),
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
);
