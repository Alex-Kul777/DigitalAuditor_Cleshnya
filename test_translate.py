# python test_translate.py

import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GIGACHAT_API_KEY")
if not api_key:
    print("Ошибка: GIGACHAT_API_KEY не найден в .env")
    exit(1)

import fitz
doc = fitz.open("personas/CISA/raw/CISA Review Manual.pdf")
page = doc[2]  # страница 3, индекс 2
text = page.get_text()

print(f"Страница 3 (первые 500 символов):\n{text[:500]}...\n")

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

print("Перевожу через GigaChat...")
client = GigaChat(
    credentials=api_key,
    scope="GIGACHAT_API_B2B",
    model="GigaChat-2-Max",
    verify_ssl_certs=False
)

messages = [
    Messages(role=MessagesRole.SYSTEM, content="Переведи текст на русский язык. Сохрани термины CISA, ISACA, IT в оригинале."),
    Messages(role=MessagesRole.USER, content=text[:4000])
]
response = client.chat(Chat(messages=messages))
print(f"\n=== РУССКИЙ ПЕРЕВОД (страница 3) ===")
print(response.choices[0].message.content)