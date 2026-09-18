Este proyecto de Python pertenece a la evaluacion del 1er Parcial de la materia
"Lenguajes de Programación Visual" (2026, 2do Ciclo) de la Facultad de Ingenieria 
de la Universidad Nacional de Asuncion, Sede San Lorenzo.

**Nombre de los docentes:**
 - Ing. Jorge Luis Tillería Mereles
 - Ing. Carlos María Benítez Cardozo

**Nombre del alumno:**
 - Adam Jeferson Guenther Vogel (C.I.: 4648952)

Proyecto: "API Gateway Industrial"

Objetivo: Diseñar, estructurar e implementar el Backend y la API REST que reciba, 
persista, consulte y administre las entidades requeridas por dicho concentrador y 
por las estaciones de supervisión.


**INSTRUCCIONES:**

**1. Software utilizado:**
 - Python 3.14.6 (usar 3.12+)
 - SQLite (Persistencia local)
 - FastAPI (Framework REST)
(Todo integrado en Visual Studio Code)


**2. Dependencias importantes de Pyhon utilizadas:**
 - uvicorn
 - fastapi
 - fastapi.responses
 - sqlite3
 - pydantic
 - pathlib
 - datetime
 - typing

**3. Instrucciones para correr el proyecto:**
(1) Clonar o extraer el proyecto:
--> main.py, simulador_planta.py
(2) Crear un entorno virtual (opcional):
--> "python -m venv venv" (en la terminal powershell)
(3) (si creaste el entorno virtual) Activar el entorno virtual:
--> "venv\Scripts\activate" (en la terminal powershell)
(4) Instalar las dependencias necesarias:
--> En la terminal powershell, escribir:
"pip install fastapi uvicorn sqlalchemy pydantic"
"python -m pip install fastapi uvicorn sqlalchemy pydantic"
(5) Ejecutar main.py
(6) En la terminal abierta por main.py, ingresar el comando:
--> "python -m uvicorn main:app --reload"
(Verificar que el PATH sea correcto al ejecutar el comando, para activar el servidor local)
(7) Una vez activo el servidor, ejecutar simulador_planta.py en otra terminal de Python.
(8) Ingresar a "http://localhost:8000/docs" en el navegador de internet.
