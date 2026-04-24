# test_giga.py 
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GIGACHAT_API_KEY")
if not api_key:
    print("ERROR: GIGACHAT_API_KEY not found in .env")
    exit(1)

print(f"Key found: {api_key[:10]}...{api_key[-4:]}")

# Вариант 1: Через официальный SDK gigachat (работает точно)
print("\n[Test 1] Using official gigachat SDK...")
try:
    from gigachat import GigaChat
    from gigachat.models import Chat, Messages, MessagesRole
    
    client = GigaChat(
        credentials=api_key,
        scope="GIGACHAT_API_B2B",  # <-- ВОТ КЛЮЧЕВОЕ ОТЛИЧИЕ
        model="GigaChat-2-Max",
        verify_ssl_certs=False,
        timeout=30
    )
    
    messages = [
        Messages(role=MessagesRole.SYSTEM, content="Ты ассистент."),
        Messages(role=MessagesRole.USER, content="Скажи Привет мир.")
    ]
    
    response = client.chat(Chat(messages=messages))
    print(f"SUCCESS: {response.choices[0].message.content}")
    
except ImportError:
    print("ERROR: pip install gigachat")
except Exception as e:
    print(f"ERROR: {e}")

# Вариант 2: Через langchain_gigachat с правильным scope
print("\n[Test 2] Using langchain_gigachat...")
try:
    from langchain_gigachat import GigaChat
    
    llm = GigaChat(
        credentials=api_key,
        scope="GIGACHAT_API_B2B",  # <-- И ЗДЕСЬ ТОЖЕ
        model="GigaChat-2-Max",
        max_tokens=50,
        temperature=0.3,
        timeout=30,
        verify_ssl_certs=False
    )
    
    response = llm.invoke("Скажи Привет мир на русском.")
    print(f"SUCCESS: {response}")
    
except ImportError:
    print("ERROR: langchain-gigachat not installed")
except Exception as e:
    print(f"ERROR: {e}")
