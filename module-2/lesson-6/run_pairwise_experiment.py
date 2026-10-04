"""
run_pairwise_experiment.py - Lección 6: Pipeline de Evaluación Pareada (A/B Testing)

Soporta dos modalidades de ejecución:
1. Modo LangSmith Cloud (si LANGSMITH_API_KEY está configurada en .env):
   Sube o sincroniza con LangSmith aevaluate() y evaluate() con randomize_order=True.
2. Modo Local Autónomo (por defecto si no hay API Key o con --local):
   Lee las 25 preguntas de 'module-2/lesson-2/officeflow-dataset.csv', corre Emma v4 y v5,
   aplica el evaluador pareado con mitigación de sesgo de posición (swap test / randomized order),
   calcula el Win-Rate global y el ahorro de tokens con tiktoken.

Uso:
    uv run python module-2/lesson-6/run_pairwise_experiment.py
    uv run python module-2/lesson-6/run_pairwise_experiment.py --limit 5  # Para prueba rápida
"""
import asyncio
import csv
import json
import os
import random
import sys
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent
agent_dir = root_dir / "officeflow-agent"

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))
sys.path.insert(0, str(agent_dir))

load_dotenv(root_dir / ".env")

import agent_v4
from agent_v4 import chat as chat_v4, load_knowledge_base as load_kb_v4
import agent_v5
from agent_v5 import chat as chat_v5, load_knowledge_base as load_kb_v5
from eval_conciseness_pairwise import conciseness_evaluator
import token_utils

DATASET_CSV = module_2_dir / "lesson-2" / "officeflow-dataset.csv"
DATASET_NAME = "officeflow-dataset"
KB_DIR = str(agent_dir / "knowledge_base")


async def chat_wrapper_v4(inputs: dict) -> dict:
    from langsmith import uuid7
    agent_v4.thread_id = str(uuid7())
    question = inputs.get("question", "")
    result = await chat_v4(question)
    return {"answer": result["output"]}


async def chat_wrapper_v5(inputs: dict) -> dict:
    from langsmith import uuid7
    agent_v5.thread_id = str(uuid7())
    question = inputs.get("question", "")
    result = await chat_v5(question)
    return {"answer": result["output"]}


async def run_local_pairwise(limit: int | None = None):
    print("\n" + "=" * 75)
    print("🚀 EJECUTANDO EVALUACIÓN PAREADA EN MODO LOCAL (GPU NVIDIA / OLLAMA)")
    print(f"Dataset Fuente: {DATASET_CSV.name}")
    print(f"Modelo LLM:     {os.getenv('CHAT_MODEL', 'qwen2.5:7b')} ({os.getenv('OPENAI_BASE_URL', 'http://localhost:11434/v1')})")
    print("=" * 75)

    if not DATASET_CSV.exists():
        print(f"❌ Error: No se encontró el dataset en {DATASET_CSV}")
        return

    # Leer preguntas del CSV
    questions = []
    with open(DATASET_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("question"):
                questions.append(row["question"].strip())

    if limit and limit > 0:
        questions = questions[:limit]

    total_q = len(questions)
    print(f"Total de preguntas a evaluar: {total_q}")
    print("-" * 75)

    wins_v4 = 0
    wins_v5 = 0
    ties = 0
    total_tokens_v4 = 0
    total_tokens_v5 = 0
    results_detail = []

    for idx, question in enumerate(questions, start=1):
        print(f"\n[{idx:02d}/{total_q:02d}] Pregunta: \"{question[:65]}...\"" if len(question) > 65 else f"\n[{idx:02d}/{total_q:02d}] Pregunta: \"{question}\"")
        
        # 1. Ejecutar Agent v4
        out_v4 = await chat_wrapper_v4({"question": question})
        ans_v4 = out_v4.get("answer", "").strip() or "N/A"
        tok_v4 = token_utils.count_tokens(ans_v4, model_name="qwen2.5:7b")
        total_tokens_v4 += tok_v4

        # 2. Ejecutar Agent v5
        out_v5 = await chat_wrapper_v5({"question": question})
        ans_v5 = out_v5.get("answer", "").strip() or "N/A"
        tok_v5 = token_utils.count_tokens(ans_v5, model_name="qwen2.5:7b")
        total_tokens_v5 += tok_v5

        # 3. Mitigación de Sesgo de Posición (Randomized Order / Barajado)
        # 50% de probabilidad de presentar A=v4, B=v5 o A=v5, B=v4
        swap = random.choice([True, False])
        if not swap:
            eval_res = conciseness_evaluator(
                inputs={"question": question},
                outputs=[{"answer": ans_v4}, {"answer": ans_v5}],
                runs=[type("Run", (), {"id": "v4"})(), type("Run", (), {"id": "v5"})()]
            )
            v4_score = eval_res["scores"].get("v4", 0)
            v5_score = eval_res["scores"].get("v5", 0)
        else:
            eval_res = conciseness_evaluator(
                inputs={"question": question},
                outputs=[{"answer": ans_v5}, {"answer": ans_v4}],
                runs=[type("Run", (), {"id": "v5"})(), type("Run", (), {"id": "v4"})()]
            )
            v4_score = eval_res["scores"].get("v4", 0)
            v5_score = eval_res["scores"].get("v5", 0)

        if v5_score > v4_score:
            winner = "Emma v5"
            wins_v5 += 1
            verdict_badge = "🏆 GANA v5"
        elif v4_score > v5_score:
            winner = "Emma v4"
            wins_v4 += 1
            verdict_badge = "🥈 GANA v4"
        else:
            winner = "Empate"
            ties += 1
            verdict_badge = "🤝 EMPATE"

        diff_tok = tok_v4 - tok_v5
        pct_tok = (diff_tok / tok_v4 * 100) if tok_v4 > 0 else 0

        print(f"       Tokens -> v4: {tok_v4:3d} | v5: {tok_v5:3d} (Ahorro v5: {diff_tok:+3d} tok / {pct_tok:+.1f}%)")
        print(f"       Veredicto: {verdict_badge} (Swap: {swap})")

        results_detail.append({
            "index": idx,
            "question": question,
            "tokens_v4": tok_v4,
            "tokens_v5": tok_v5,
            "winner": winner,
            "comment": eval_res.get("comment", "")
        })

    # Resumen Estadístico
    print("\n" + "=" * 75)
    print("📊 RESULTADOS FINALES DE LA EVALUACIÓN PAREADA A/B")
    print("=" * 75)
    winrate_v5 = (wins_v5 / total_q) * 100
    winrate_v4 = (wins_v4 / total_q) * 100
    tierate = (ties / total_q) * 100
    total_diff = total_tokens_v4 - total_tokens_v5
    total_pct_saved = (total_diff / total_tokens_v4 * 100) if total_tokens_v4 > 0 else 0

    print(f"Total Evaluaciones:   {total_q}")
    print(f"Victorias Emma v5:    {wins_v5:2d} ({winrate_v5:5.1f}%)")
    print(f"Victorias Emma v4:    {wins_v4:2d} ({winrate_v4:5.1f}%)")
    print(f"Empates Técnicos:     {ties:2d} ({tierate:5.1f}%)")
    print("-" * 75)
    print(f"Total Tokens Emma v4: {total_tokens_v4} tokens")
    print(f"Total Tokens Emma v5: {total_tokens_v5} tokens")
    print(f"Ahorro Neto de Tokens: {total_diff} tokens ({total_pct_saved:.1f}% de reducción de costes)")
    print("=" * 75)

    if winrate_v5 > winrate_v4:
        print("🎉 CONCLUSIÓN: Emma v5 supera a Emma v4 con ventaja estadísticamente significativa.")
        print("   Recomendación: DESPLEGAR EMMA v5 A PRODUCCIÓN.")
    else:
        print("⚠️ CONCLUSIÓN: Emma v5 no superó concluyentemente a Emma v4.")
    print("=" * 75)

    # Guardar reporte en JSON
    report_file = current_dir / "pairwise_results.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_questions": total_q,
            "wins_v5": wins_v5,
            "wins_v4": wins_v4,
            "ties": ties,
            "winrate_v5": winrate_v5,
            "winrate_v4": winrate_v4,
            "tierate": tierate,
            "total_tokens_v4": total_tokens_v4,
            "total_tokens_v5": total_tokens_v5,
            "token_reduction_pct": total_pct_saved,
            "details": results_detail
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetalles completos guardados en: {report_file.name}")


async def run_langsmith_pairwise():
    from langsmith import aevaluate, evaluate
    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 6: EXPERIMENTO COMPLETO EN LANGSMITH CLOUD")
    print(f"Modelo LLM: {os.getenv('CHAT_MODEL', 'qwen2.5:7b')}")
    print("=" * 70)

    max_concurrency = int(os.getenv("MAX_CONCURRENCY", "1"))

    print("\n[Paso 1/3] Ejecutando experimento para Agent v4 en LangSmith...")
    v4_results = await aevaluate(
        chat_wrapper_v4,
        data=DATASET_NAME,
        experiment_prefix="agent-v4",
        max_concurrency=max_concurrency,
    )

    print("\n[Paso 2/3] Ejecutando experimento para Agent v5 en LangSmith...")
    v5_results = await aevaluate(
        chat_wrapper_v5,
        data=DATASET_NAME,
        experiment_prefix="agent-v5",
        max_concurrency=max_concurrency,
    )

    v4_exp = v4_results.experiment_name
    v5_exp = v5_results.experiment_name

    print(f"\nExperimento A (v4): {v4_exp}")
    print(f"Experimento B (v5): {v5_exp}")

    print("\n[Paso 3/3] Ejecutando evaluación pareada con conciseness_evaluator...")
    print("  Mitigación de sesgos activa: randomize_order=True")
    evaluate(
        (v4_exp, v5_exp),
        evaluators=[conciseness_evaluator],
        randomize_order=True,
    )
    print("\n🎉 Evaluación pareada en LangSmith completada.")


async def main():
    # Cargar bases de conocimiento
    print("Cargando bases de conocimiento...")
    await load_kb_v4(KB_DIR)
    await load_kb_v5(KB_DIR)

    # Determinar si hay API Key válida para LangSmith
    has_ls_key = bool(os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGSMITH_API_KEY", "").startswith("lsv2_pt_..."))
    force_local = "--local" in sys.argv

    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    if has_ls_key and not force_local:
        await run_langsmith_pairwise()
    else:
        await run_local_pairwise(limit=limit)


if __name__ == "__main__":
    asyncio.run(main())
