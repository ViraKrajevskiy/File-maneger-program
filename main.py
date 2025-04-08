import os
from datetime import datetime
import psycopg2
import psycopg2.extras
from tabulate import tabulate

# =================== DATABASE MANAGER ===================
class Database:
    @staticmethod
    def connect():
        try:
            return psycopg2.connect(
                host="localhost",
                user="ViraKrajevskiy",
                password="3003",
                database="test"
            )
        except psycopg2.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return None

    @staticmethod
    def create_table():
        conn = Database.connect()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
CREATE TABLE IF NOT EXISTS items (
id SERIAL PRIMARY KEY,
name TEXT NOT NULL,
type TEXT NOT NULL,
parent_id INTEGER,
absolute_path TEXT,
size INTEGER,
deleted_at TIMESTAMP
);
                    """)

# =================== BASE CLASS ===================
class Item:
    def __init__(self, name, item_type, parent_id, absolute_path, size=0):
        self.name = name
        self.type = item_type
        self.parent_id = parent_id if parent_id else None
        self.absolute_path = absolute_path
        self.size = size

    def save(self):
        conn = Database.connect()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
INSERT INTO items (name, type, parent_id, absolute_path, size)
VALUES (%s, %s, %s, %s, %s)
                        """, (self.name, self.type, self.parent_id, self.absolute_path, self.size))

    @staticmethod
    def get_all(order_by=None):
        conn = Database.connect()
        if conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    sql = "SELECT * FROM items WHERE deleted_at IS NULL"
                    if order_by:
                        sql += f" ORDER BY {order_by}"
                    cursor.execute(sql)
                    return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def search_by_name(name):
        conn = Database.connect()
        if conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("""
SELECT * FROM items
WHERE name ILIKE %s AND deleted_at IS NULL
                        """, (f"%{name}%",))
                    return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update(item_id, new_name):
        try:
            item_id = int(item_id)  # Преобразуем в целое число
            conn = Database.connect()
            if conn:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("UPDATE items SET name = %s WHERE id = %s", (new_name, item_id))
                        print("✅ Имя обновлено.")
        except ValueError:
            print("❌ Неверный формат ID.")
        except psycopg2.Error as e:
            print(f"Ошибка при обновлении: {e}")

    @staticmethod
    def delete(item_id):
        try:
            item_id = int(item_id)  # Преобразуем в целое число
            conn = Database.connect()
            if conn:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("UPDATE items SET deleted_at = %s WHERE id = %s", (datetime.now(), item_id))
                        print("✅ Удаление выполнено (soft delete).")
        except ValueError:
            print("❌ Неверный формат ID.")
        except psycopg2.Error as e:
            print(f"Ошибка при удалении: {e}")

# =================== CHILD CLASSES ===================
class File(Item):
    def __init__(self, name, parent_id, absolute_path):
        if not os.path.isfile(absolute_path):
            raise ValueError("❌ Указанный путь не ведёт к файлу.")
        size = os.path.getsize(absolute_path)
        super().__init__(name, 'file', parent_id, absolute_path, size)

class Directory(Item):
    def __init__(self, name, parent_id, absolute_path):
        if not os.path.isdir(absolute_path):
            create = input(f"Каталог по пути {absolute_path} не существует. Хотите создать его? (y/n): ").strip().lower()
            if create == 'y':
                os.makedirs(absolute_path)  # Создаём каталог
            else:
                raise ValueError("❌ Указанный путь не ведёт к каталогу и не был создан.")
        super().__init__(name, 'directory', parent_id, absolute_path)

# =================== UTIL ===================
def display_items(items):
    if not items:
        print("Нет данных.")
    else:
        print(tabulate(items, headers="keys", tablefmt="grid"))

# =================== MAIN MENU ===================
def main():
    Database.create_table()

    while True:
        print("""
====== ФАЙЛ/КАТАЛОГ МЕНЕДЖЕР ======
1. Создать файл
2. Создать каталог
3. Показать все
4. Сортировать по (name/type/size)
5. Поиск по названию
6. Обновить имя
7. Удалить
8. Выход
        """)
        choice = input("Выберите действие: ").strip()

        if choice == '1':
            name = input("Имя файла: ")
            parent = input("ID родителя (или пусто): ") or None
            path = input("Путь к файлу: ")
            try:
                if os.path.isfile(path):
                    file = File(name, parent, path)
                    file.save()
                    print("✅ Файл сохранён.")
                else:
                    print("❌ Указанный путь не ведёт к файлу.")
            except ValueError as e:
                print(e)

        elif choice == '2':
            name = input("Имя каталога: ")
            parent = input("ID родителя (или пусто): ") or None
            path = input("Путь к каталогу: ")
            try:
                directory = Directory(name, parent, path)
                directory.save()
                print("✅ Каталог сохранён.")
            except ValueError as e:
                print(e)

        elif choice == '3':
            items = Item.get_all()
            display_items(items)

        elif choice == '4':
            by = input("Сортировать по (name/type/size): ").strip().lower()
            if by in ['name', 'type', 'size']:
                items = Item.get_all(order_by=by)
                display_items(items)
            else:
                print("❌ Неверный критерий сортировки.")

        elif choice == '5':
            name = input("Введите имя для поиска: ")
            items = Item.search_by_name(name)
            display_items(items)

        elif choice == '6':
            item_id = input("ID элемента для обновления: ")
            new_name = input("Новое имя: ")
            Item.update(item_id, new_name)

        elif choice == '7':
            item_id = input("ID для удаления: ")
            Item.delete(item_id)

        elif choice == '8':
            print("👋 Выход из программы.")
            break

        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
    