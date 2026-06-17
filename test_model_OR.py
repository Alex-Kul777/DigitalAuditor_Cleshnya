# python test_model_OR.py
import os
import time
import json
from openai import OpenAI
from tqdm import tqdm

# Проверяем наличие API ключа в разных переменных
api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise Exception("❌ API ключ не найден. Установите OPENROUTER_API_KEY или ANTHROPIC_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

def compare_models(prompt: str, models: list[str]) -> dict:
    """Сравнение моделей с прогресс-баром"""
    results = {}
    
    print(f"\n🎯 Задача: {prompt[:80]}...\n")
    
    # Прогресс-бар для моделей
    with tqdm(total=len(models), desc="🔄 Тестирование моделей", unit="модель", ncols=80) as pbar:
        for model in models:
            pbar.set_description(f"📡 {model[:40]}")
            
            start = time.time()
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7,
                )
                latency = (time.time() - start) * 1000
                
                results[model] = {
                    "response": response.choices[0].message.content[:200],
                    "tokens": response.usage.prompt_tokens + response.usage.completion_tokens,
                    "latency_ms": round(latency, 1),
                    "success": True,
                }
                pbar.set_postfix({"✅": model[:25], "токены": results[model]["tokens"]})
                
            except Exception as e:
                results[model] = {
                    "error": str(e),
                    "success": False,
                }
                pbar.set_postfix({"❌": model[:25], "ошибка": str(e)[:20]})
            
            pbar.update(1)
            time.sleep(0.5)  # небольшая пауза между запросами
    
    return results

def print_results(results: dict):
    """Красивый вывод результатов"""
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ СРАВНЕНИЯ МОДЕЛЕЙ")
    print("=" * 70)
    
    # Сортируем по успешности и задержке
    successful = {k: v for k, v in results.items() if v.get("success")}
    failed = {k: v for k, v in results.items() if not v.get("success")}
    
    if successful:
        print("\n✅ УСПЕШНЫЕ ЗАПРОСЫ:")
        print("-" * 70)
        for model, data in sorted(successful.items(), key=lambda x: x[1]["latency_ms"]):
            print(f"\n🔹 {model}")
            print(f"   ⏱️  Задержка: {data['latency_ms']} мс")
            print(f"   📝 Токенов: {data['tokens']}")
            print(f"   💰 Стоимость: ~${data['tokens'] * 0.000001:.4f} (оценка)")
            print(f"   📄 Ответ: {data['response'][:100]}...")
    
    if failed:
        print("\n❌ ОШИБКИ:")
        print("-" * 70)
        for model, data in failed.items():
            print(f"\n🔹 {model}: {data['error']}")
    
    print("\n" + "=" * 70)

def compare_with_progress(prompt: str, models: list[str]):
    """Запуск сравнения с прогресс-баром"""
    print("🚀 ЗАПУСК СРАВНЕНИЯ МОДЕЛЕЙ")
    print("=" * 70)
    
    results = compare_models(prompt, models)
    print_results(results)
    
    return results

if __name__ == "__main__":
    # Пример сравнения моделей для Python-кодинга
    results = compare_with_progress(
        "Напиши функцию на Python для быстрой сортировки списка с подробными комментариями",
        models=[
            "deepseek/deepseek-v3.2",
            "minimax/minimax-m2.5",
            "google/gemini-2.5-flash",
            "anthropic/claude-3.5-sonnet",
            "nvidia/nemotron-3-super-120b-a12b:free",
        ]
    )
    
    # Сохранить результаты в файл
    with open("model_comparison.json", "w") as f:
        # Убираем длинные ответы для компактности
        clean_results = {}
        for model, data in results.items():
            if data.get("success"):
                clean_results[model] = {
                    "latency_ms": data["latency_ms"],
                    "tokens": data["tokens"],
                    "success": True,
                }
            else:
                clean_results[model] = {"error": data.get("error"), "success": False}
        
        json.dump(clean_results, f, indent=2)
    
    print("\n💾 Результаты сохранены в model_comparison.json")