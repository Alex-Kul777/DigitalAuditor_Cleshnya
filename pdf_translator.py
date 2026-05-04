# tools/pdf_translator.py 
"""
Перевод PDF через PyMuPDF (извлечение текста) + GigaChat SDK (перевод).
Полностью обходит SSL-проблемы pdf2zh.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def translate_pdf(input_path: str, output_path: str = None, lang: str = "ru", pages: list = None):
    """
    Переводит PDF-файл на указанный язык.
    
    Args:
        input_path: путь к исходному PDF
        output_path: путь для сохранения перевода (если None — сохраняет рядом с суффиксом _ru.pdf)
        lang: целевой язык (по умолчанию ru)
        pages: список страниц для перевода (None = все)
    """
    import fitz
    from gigachat import GigaChat
    from gigachat.models import Chat, Messages, MessagesRole
    
    api_key = os.getenv("GIGACHAT_API_KEY")
    if not api_key:
        raise ValueError("GIGACHAT_API_KEY не найден в .env")
    
    # Открываем PDF
    doc = fitz.open(input_path)
    total_pages = doc.page_count
    
    if pages is None:
        pages = list(range(total_pages))
    
    print(f"📄 Файл: {input_path}")
    print(f"📊 Всего страниц: {total_pages}")
    print(f"🔄 Перевод страниц: {pages}")
    
    client = GigaChat(
        credentials=api_key,
        scope="GIGACHAT_API_B2B",
        model="GigaChat-2-Max",
        verify_ssl_certs=False
    )
    
    translated_pages = {}
    
    for page_num in pages:
        if page_num >= total_pages:
            print(f"⚠️ Страница {page_num + 1} не существует (всего {total_pages})")
            continue
        
        text = doc[page_num].get_text()
        if not text.strip():
            continue
        
        print(f"  📝 Страница {page_num + 1}: {len(text)} символов → перевод...")
        
        messages = [
            Messages(role=MessagesRole.SYSTEM, content=f"Переведи текст на {lang} язык. Сохрани термины, имена собственные и аббревиатуры в оригинале."),
            Messages(role=MessagesRole.USER, content=text[:4000])
        ]
        
        try:
            response = client.chat(Chat(messages=messages))
            translated_pages[page_num] = response.choices[0].message.content
            print(f"  ✅ Страница {page_num + 1} переведена ({len(translated_pages[page_num])} символов)")
        except Exception as e:
            print(f"  ❌ Ошибка на странице {page_num + 1}: {e}")
            translated_pages[page_num] = f"[ОШИБКА ПЕРЕВОДА: {e}]"
    
    # Сохраняем результат
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_ru{input_path_obj.suffix}"
    
    # Создаём новый PDF с переводом (простой текстовый)
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    
    for page_num in sorted(translated_pages.keys()):
        text = translated_pages[page_num]
        y = height - 50
        
        # Заголовок страницы
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Страница {page_num + 1} (перевод)")
        y -= 30
        
        # Текст
        c.setFont("Helvetica", 10)
        for line in text.split('\n'):
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(50, y, line[:100])
            y -= 15
        
        c.showPage()
    
    c.save()
    
    print(f"\n✅ Перевод сохранён: {output_path}")
    return str(output_path)

def main():
    parser = argparse.ArgumentParser(description="Перевод PDF через GigaChat")
    parser.add_argument("--input", required=True, help="Путь к PDF-файлу")
    parser.add_argument("--output", default=None, help="Путь для сохранения перевода")
    parser.add_argument("--lang", default="ru", help="Целевой язык")
    parser.add_argument("--pages", nargs="+", type=int, help="Страницы для перевода (например: 1 2 3)")
    args = parser.parse_args()
    
    translate_pdf(args.input, args.output, args.lang, args.pages)

if __name__ == "__main__":
    main()


# Тест: перевод 3-й страницы
# python tools/pdf_translator.py --input "personas/CISA/raw/CISA Review Manual.pdf" --pages 3