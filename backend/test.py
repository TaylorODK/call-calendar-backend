import psycopg2

try:
    conn = psycopg2.connect(
        host="postgres",
        database="calendar",
        user="calendar",
        password="calendar",
        port="5432",
    )
    print("✅ Подключение к БД успешно!")
    conn.close()
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
