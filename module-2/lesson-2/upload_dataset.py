"""
upload_dataset.py - Lección 2: Creación y Carga Automatizada de Datasets en LangSmith

Sube el archivo 'officeflow-dataset.csv' directamente a LangSmith utilizando el SDK.
Verifica si el dataset ya existe para evitar duplicados y muestra el enlace de acceso web.

Uso:
    uv run python module-2/lesson-2/upload_dataset.py
"""
import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from langsmith import Client

# Rutas del proyecto
current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent

load_dotenv(root_dir / ".env")

DATASET_NAME = "officeflow-dataset"
CSV_FILE = current_dir / "officeflow-dataset.csv"


def upload_dataset():
    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 2: SUBIENDO DATASET A LANGSMITH")
    print("=" * 70)

    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key or "your_langsmith_api_key_here" in api_key:
        print("❌ ERROR: LANGSMITH_API_KEY no está configurada correctamente en el archivo .env")
        return

    if not CSV_FILE.exists():
        print(f"❌ ERROR: No se encontró el archivo CSV en {CSV_FILE}")
        return

    print(f"📂 Leyendo archivo local: {CSV_FILE.name}")
    df = pd.read_csv(CSV_FILE)
    total_rows = len(df)
    print(f"✅ Se encontraron {total_rows} preguntas de prueba en el dataset.")

    client = Client()

    # Comprobar si ya existe el dataset
    dataset_exists = client.has_dataset(dataset_name=DATASET_NAME)
    
    if dataset_exists:
        print(f"\nℹ️  El dataset '{DATASET_NAME}' ya existe en tu cuenta de LangSmith.")
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"   ID del Dataset: {dataset.id}")
        print(f"   Ejemplos existentes: {client.read_dataset(dataset_name=DATASET_NAME).example_count}")
    else:
        print(f"\n🚀 Creando nuevo dataset en LangSmith: '{DATASET_NAME}'...")
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Golden Dataset de 25 preguntas para evaluar al agente de soporte Emma de OfficeFlow Supply Co."
        )
        print(f"✅ Dataset creado exitosamente con ID: {dataset.id}")

        print(f"\n📤 Subiendo {total_rows} ejemplos...")
        for idx, row in df.iterrows():
            question = row.get("question", "")
            client.create_example(
                inputs={"question": question},
                outputs={},
                dataset_id=dataset.id
            )
            print(f"   [{idx + 1}/{total_rows}] Subido: {question[:60]}...")

        print(f"\n🎉 ¡Todos los {total_rows} ejemplos han sido cargados con éxito!")

    print("\n" + "=" * 70)
    print(f"🔗 Puedes ver y gestionar tu dataset en:")
    print(f"   https://smith.langchain.com/datasets (Buscar: '{DATASET_NAME}')")
    print("=" * 70)


if __name__ == "__main__":
    upload_dataset()
