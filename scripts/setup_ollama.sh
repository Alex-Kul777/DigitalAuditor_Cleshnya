#!/bin/bash
echo "[*] Проверка Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "[-] Ollama не установлен. Установите с https://ollama.com"
    exit 1
fi
echo "[*] Загрузка Qwen2.5-0.5B-Instruct..."
ollama pull qwen2.5:0.5b-instruct
echo "[*] Создание модели digital-auditor-cisa..."
ollama create digital-auditor-cisa -f - << 'EOF'
FROM qwen2.5:0.5b-instruct
SYSTEM "Ты — старший ИТ-аудитор с сертификатами CISA и CIA. Отвечай на русском языке в официально-деловом стиле. Обязательно ссылайся на источники и стандарты."
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
EOF
echo "[+] Модель digital-auditor-cisa создана"
