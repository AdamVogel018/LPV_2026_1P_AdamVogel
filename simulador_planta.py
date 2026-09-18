"""
SIMULADOR INDUSTRIAL Y VALIDADOR DE API REST
Cátedra: Lenguajes de Programación Visual
Facultad de Ingeniería - UNA

Simula telemetría en tiempo real con inercia física y evalúa la conformidad REST.
"""

import json
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"


class PerfilSensor:
    """Modela el comportamiento físico real con inercia y deriva de un sensor."""
    def __init__(self, nodo: str, tipo: str, modelo: str, unidad: str,
                 min_nominal: f64, max_nominal: f64, rango_max: f64,
                 max_salto: f64, valor_inicial: f64):
        self.nodo = nodo
        self.tipo = tipo
        self.modelo = modelo
        self.unidad = unidad
        self.min_nominal = min_nominal
        self.max_nominal = max_nominal
        self.rango_max = rango_max
        self.max_salto = max_salto
        self.valor_actual = valor_inicial
        self.id = None  # Asignado tras el registro en la API

    def generar_siguiente_lectura(self) -> float:
        # 10% de probabilidad de generar una anomalía de proceso que supere rango_max
        if random.random() < 0.10:
            pico = self.rango_max + random.uniform(1.5, 6.0)
            return round(pico, 2)

        # Paseo aleatorio continuo (inercia física)
        cambio = random.uniform(-self.max_salto, self.max_salto)
        self.valor_actual += cambio

        # Rebotar suavemente si se sale de la zona nominal
        if self.valor_actual < self.min_nominal:
            self.valor_actual = self.min_nominal + random.uniform(0.1, 0.4)
        elif self.valor_actual > self.max_nominal:
            self.valor_actual = self.max_nominal - random.uniform(0.1, 0.4)

        return round(self.valor_actual, 2)


def http_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            body = response.read().decode("utf-8")
            return status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        print(f"❌ Error de conexión al servidor en {url}: {e}")
        input("\nPresione Enter para salir...")
        sys.exit(1)


def ejecutar():
    print("=" * 65)
    print(" 🏭 SIMULADOR DE PLANTA INDUSTRIAL - EVALUADOR DE PARCIAL")
    print(f" 📍 URL Destino: {BASE_URL}")
    print("=" * 65 + "\n")

    # Configuración de los sensores con datos coherentes de ingeniería
    sensores = [
        PerfilSensor("ESP32-Caldera-01", "Temperatura", "DS18B20", "°C", 62.0, 78.0, 85.0, 0.6, 68.5),
        PerfilSensor("ESP32-Caldera-01", "Presión", "BMP280", "Bar", 2.2, 3.8, 5.0, 0.12, 3.1),
        PerfilSensor("STM32-Motor-A", "Vibración", "MPU6050", "m/s²", 2.0, 4.5, 12.0, 0.35, 3.2),
        PerfilSensor("ESP32-Ambiente-02", "Humedad", "DHT22", "%", 50.0, 68.0, 85.0, 1.2, 58.0),
    ]

    # --- PASO 1: Registro de Sensores (POST /api/sensores) ---
    print("📋 [Paso 1] Registrando sensores en la API (POST /api/sensores)...")
    for s in sensores:
        payload = {
            "nodo": s.nodo,
            "tipo": s.tipo,
            "modelo": s.modelo,
            "unidad": s.unidad,
            "rango_max": s.rango_max,
        }
        status, resp = http_request("POST", "/api/sensores", payload)

        if status != 201:
            print(f"❌ Error en POST /api/sensores. Código esperado 201, recibido: {status}")
            print(f"   Respuesta: {resp}")
            input("\nPresione Enter para salir...")
            sys.exit(1)

        # Detectar clave del identificador devuelto
        sensor_id = resp.get("id") or resp.get("sensor_id") or resp.get("_id")
        if not sensor_id:
            print(f"❌ Error: La respuesta no incluye un ID ('id', 'sensor_id' o '_id'): {resp}")
            input("\nPresione Enter para salir...")
            sys.exit(1)

        s.id = sensor_id
        print(f"   ✔ [{s.tipo}] registrado correctamente con ID: {s.id}")

    # --- PASO 2: Ingesta de Telemetría Dinámica (POST /api/lecturas) ---
    print("\n📡 [Paso 2] Emitiendo ráfaga de lecturas de telemetría (POST /api/lecturas)...")
    total_lecturas = 16
    for i in range(1, total_lecturas + 1):
        sensor: PerfilSensor = random.choice(sensores)
        valor = sensor.generar_siguiente_lectura()

        lectura_payload = {
            "sensor_id": sensor.id,
            "valor": valor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        status, resp = http_request("POST", "/api/lecturas", lectura_payload)
        if status != 201:
            print(f"❌ Error en POST /api/lecturas. Código esperado 201, recibido: {status}")
            print(f"   Payload enviado: {lectura_payload}")
            print(f"   Respuesta: {resp}")
            input("\nPresione Enter para salir...")
            sys.exit(1)

        alerta_txt = " [⚠️ ANOMALÍA GENERADA]" if valor > sensor.rango_max else ""
        print(f"   [{i:02d}/{total_lecturas:02d}] {sensor.tipo:<12} (ID {sensor.id}): {valor:>6.2f} {sensor.unidad:<4}{alerta_txt}")
        time.sleep(0.25)

    # --- PASO 3: Histórico de Lecturas (GET /api/lecturas) ---
    print("\n🔍 [Paso 3] Verificando consulta general (GET /api/lecturas)...")
    status, lecturas = http_request("GET", "/api/lecturas")
    if status == 200 and isinstance(lecturas, list):
        print(f"   ✔ OK: Se recuperaron {len(lecturas)} lecturas de la base de datos.")
    else:
        print(f"❌ Error en GET /api/lecturas. Esperado 200 y una lista, recibido: {status} -> {lecturas}")
        input("\nPresione Enter para salir...")
        sys.exit(1)

    # --- PASO 4: Estadísticas por Sensor (GET /api/lecturas/estadisticas/{sensor_id}) ---
    target = sensores[0]
    print(f"\n📊 [Paso 4] Consultando estadísticas para sensor '{target.tipo}' (ID {target.id})...")
    status, stats = http_request("GET", f"/api/lecturas/estadisticas/{target.id}")

    if status == 200 and isinstance(stats, dict):
        print(f"   ✔ OK: Métricas calculadas por el backend:")
        print(f"      - Mínimo:   {stats.get('minimo')}")
        print(f"      - Máximo:   {stats.get('maximo')}")
        print(f"      - Promedio: {stats.get('promedio')}")
    else:
        print(f"❌ Error en GET estadísticas. Recibido status: {status} -> {stats}")
        input("\nPresione Enter para salir...")
        sys.exit(1)

    # --- PASO 5: Prueba de Manejo de Errores (404) ---
    print("\n🛡️ [Paso 5] Verificando respuesta ante recurso inexistente (Status 404)...")
    status, _ = http_request("GET", "/api/lecturas/estadisticas/id-fantasma-99999")
    if status == 404:
        print("   ✔ OK: El servidor devolvió 404 Not Found apropiadamente.")
    else:
        print(f"   ⚠️ Alerta: Para un sensor inexistente se esperaba código 404, pero devolvió: {status}")

    print("\n" + "=" * 65)
    print(" 🎉 TODAS LAS PRUEBAS COMPLETADAS CORRECTAMENTE")
    print("=" * 65)
    input("\nPresione Enter para finalizar...")


if __name__ == "__main__":
    ejecutar()
