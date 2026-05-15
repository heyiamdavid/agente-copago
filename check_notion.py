import asyncio
import os
import sys

# Agrega la ruta de la aplicación al path para poder importar
sys.path.insert(0, os.path.abspath('backend'))

from app.core.config import settings
from app.integrations.notion import _query_database, _text_prop

async def main():
    print(f"Consultando BD de Pacientes: {settings.notion_db_patients}")
    rows = await _query_database(settings.notion_db_patients)
    print(f"Total de registros encontrados: {len(rows)}")
    
    print("\nIDs de Pacientes disponibles en Notion:")
    print("-" * 40)
    for row in rows:
        pid = _text_prop(row, "patient_id")
        nombre = _text_prop(row, "nombre")
        plan = _text_prop(row, "plan_nombre")
        print(f"ID: {pid} | Nombre: {nombre} | Plan: {plan}")

if __name__ == "__main__":
    asyncio.run(main())
