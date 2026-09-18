from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

app = FastAPI(title="API Gateway Industrial")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "planta.db"

# CONEXIÓN A BASE DE DATOS (SQLite en memoria)
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn




# INICIALIZACION DE TABLAS EN LA BASE DE DATOS
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo TEXT,
            tipo TEXT,
            modelo TEXT,
            unidad TEXT,
            rango_max REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER,
            valor REAL,
            timestamp TEXT,
            FOREIGN KEY(sensor_id) REFERENCES sensores(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()




# ESQUEMAS PYDANTIC
class SensorCreate(BaseModel):
    nodo: str
    tipo: str
    modelo: str
    unidad: str
    rango_max: float

class SensorResponse(SensorCreate):
    id: int

class LecturaCreate(BaseModel):
    sensor_id: int
    valor: float
    timestamp: str

class LecturaResponse(LecturaCreate):
    id: int




# ENDPOINTS DE SENSORES
@app.post("/api/sensores", status_code=status.HTTP_201_CREATED, response_model=SensorResponse)
def crear_sensor(sensor: SensorCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sensores (nodo, tipo, modelo, unidad, rango_max) VALUES (?, ?, ?, ?, ?)",
        (sensor.nodo, sensor.tipo, sensor.modelo, sensor.unidad, sensor.rango_max)
    )
    conn.commit()
    sensor_id = cursor.lastrowid
    conn.close()
    
    return {**sensor.model_dump(), "id": sensor_id}


@app.get("/api/sensores", response_model=List[SensorResponse])
def listar_sensores():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensores")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.put("/api/sensores/{sensor_id}", response_model=SensorResponse)
def actualizar_sensor(sensor_id: int, sensor: SensorCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sensores WHERE id = ?", (sensor_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    cursor.execute(
        "UPDATE sensores SET nodo = ?, tipo = ?, modelo = ?, unidad = ?, rango_max = ? WHERE id = ?",
        (sensor.nodo, sensor.tipo, sensor.modelo, sensor.unidad, sensor.rango_max, sensor_id)
    )
    conn.commit()
    conn.close()
    return {**sensor.model_dump(), "id": sensor_id}


@app.delete("/api/sensores/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sensor(sensor_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sensores WHERE id = ?", (sensor_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    cursor.execute("DELETE FROM lecturas WHERE sensor_id = ?", (sensor_id,))
    cursor.execute("DELETE FROM sensores WHERE id = ?", (sensor_id,))
    conn.commit()
    conn.close()
    return Response(status_code=status.HTTP_204_NO_CONTENT)




# ENDPOINTS DE LECTURAS
@app.post("/api/lecturas", status_code=status.HTTP_201_CREATED)
def ingerir_lectura(lectura: LecturaCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Validar que el sensor existe (Requisito: HTTP 404 si no existe)
    cursor.execute("SELECT id FROM sensores WHERE id = ?", (lectura.sensor_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
        
    cursor.execute(
        "INSERT INTO lecturas (sensor_id, valor, timestamp) VALUES (?, ?, ?)",
        (lectura.sensor_id, lectura.valor, lectura.timestamp)
    )
    conn.commit()
    conn.close()
    return {"message": "Lectura registrada"}


@app.get("/api/lecturas")
def obtener_lecturas(sensor_id: Optional[int] = None, limit: int = Query(default=50, ge=1, le=1000)):
    conn = get_db()
    cursor = conn.cursor()

    if sensor_id is not None:
        cursor.execute("SELECT * FROM lecturas WHERE sensor_id = ? ORDER BY id DESC LIMIT ?", (sensor_id, limit))
    else:
        cursor.execute("SELECT * FROM lecturas ORDER BY id DESC LIMIT ?", (limit,))
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.put("/api/lecturas/{lectura_id}")
def actualizar_lectura(lectura_id: int, lectura: LecturaCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Validar que la lectura existe
    cursor.execute("SELECT id FROM lecturas WHERE id = ?", (lectura_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    
    # Validar que el sensor existe
    cursor.execute("SELECT id FROM sensores WHERE id = ?", (lectura.sensor_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
        
    cursor.execute(
        "UPDATE lecturas SET sensor_id = ?, valor = ?, timestamp = ? WHERE id = ?",
        (lectura.sensor_id, lectura.valor, lectura.timestamp, lectura_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Lectura actualizada"}


@app.delete("/api/lecturas/{lectura_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_lectura(lectura_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # Validar que la lectura existe
    cursor.execute("SELECT id FROM lecturas WHERE id = ?", (lectura_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
        
    cursor.execute("DELETE FROM lecturas WHERE id = ?", (lectura_id,))
    conn.commit()
    conn.close()
    return Response(status_code=status.HTTP_204_NO_CONTENT)





# MÓDULO DE ANALÍTICA
@app.get("/api/lecturas/estadisticas/{sensor_id}")
def obtener_estadisticas(sensor_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si el sensor existe
    cursor.execute("SELECT id FROM sensores WHERE id = ?", (sensor_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
        
    # Calcular estadísticas en SQL
    cursor.execute('''
        SELECT MIN(valor) as minimo, MAX(valor) as maximo, AVG(valor) as promedio 
        FROM lecturas WHERE sensor_id = ?
    ''', (sensor_id,))
    stats = cursor.fetchone()
    conn.close()
    
    return {
        "sensor_id": sensor_id,
        "minimo": round(stats['minimo'], 2) if stats['minimo'] is not None else 0.0,
        "maximo": round(stats['maximo'], 2) if stats['maximo'] is not None else 0.0,
        "promedio": round(stats['promedio'], 2) if stats['promedio'] is not None else 0.0
    }


@app.get("/")
def salud():
    return {"status": "ok", "service": "API Gateway Industrial"}
