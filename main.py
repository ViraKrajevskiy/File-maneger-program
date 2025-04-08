import os
from datetime import datetime
import psycopg2
import psycopg2.extras
from tabulate import tabulate

# =================== TRANSLATIONS ===================
translations = {
    'ru': {
        'menu_title': 'Файловый/Каталожный Менеджер',
        'create_file': 'Создать файл',
        'create_directory': 'Создать каталог',
        'show_all': 'Показать все',
        'sort_by': 'Сортировать по (name/type/size)',
        'search_name': 'Поиск по имени',
        'update_name': 'Обновить имя',
        'delete': 'Удалить',
        'exit': 'Выход',
        'choose_action': 'Выберите действие: ',
        'file_name': 'Имя файла: ',
        'directory_name': 'Имя каталога: ',
        'parent_id': 'ID родителя (или пусто): ',
        'file_path': 'Путь к файлу: ',
        'directory_path': 'Путь к каталогу: ',
        'file_saved': '✅ Файл сохранён.',
        'directory_saved': '✅ Каталог сохранён.',
        'invalid_file': '❌ Указанный путь не ведёт к файлу.',
        'invalid_dir': '❌ Указанный путь не ведёт к каталогу.',
        'invalid_choice': '❌ Неверный выбор. Попробуйте снова.',
        'sort_invalid': '❌ Неверный критерий сортировки.',
        'enter_name_to_search': 'Введите имя для поиска: ',
        'update_id': 'ID элемента для обновления: ',
        'new_name': 'Новое имя: ',
        'delete_id': 'ID для удаления: ',
        'exit_msg': '👋 Выход.',
        'no_data': 'Нет данных.',
    },
    'uz': {
        'menu_title': 'Fayl/Katalog Menejeri',
        'create_file': 'Fayl yaratish',
        'create_directory': 'Katalog yaratish',
        'show_all': 'Hammasini ko‘rsatish',
        'sort_by': 'Saralash (name/type/size)',
        'search_name': 'Nom bo‘yicha qidirish',
        'update_name': 'Nomni yangilash',
        'delete': 'O‘chirish',
        'exit': 'Chiqish',
        'choose_action': 'Amalni tanlang: ',
        'file_name': 'Fayl nomi: ',
        'directory_name': 'Katalog nomi: ',
        'parent_id': 'Ota ID (yoki bo‘sh): ',
        'file_path': 'Fayl yo‘li: ',
        'directory_path': 'Katalog yo‘li: ',
        'file_saved': '✅ Fayl saqlandi.',
        'directory_saved': '✅ Katalog saqlandi.',
        'invalid_file': '❌ Ko‘rsatilgan yo‘l fayl emas.',
        'invalid_dir': '❌ Ko‘rsatilgan yo‘l katalog emas.',
        'invalid_choice': '❌ Noto‘g‘ri tanlov. Qayta urinib ko‘ring.',
        'sort_invalid': '❌ Noto‘g‘ri saralash mezoni.',
        'enter_name_to_search': 'Qidiriladigan nomni kiriting: ',
        'update_id': 'Yangilanadigan ID: ',
        'new_name': 'Yangi nom: ',
        'delete_id': 'O‘chiriladigan ID: ',
        'exit_msg': '👋 Chiqildi.',
        'no_data': 'Maʼlumot yoʻq.',
    },
    'en': {
        'menu_title': 'File/Directory Manager',
        'create_file': 'Create file',
        'create_directory': 'Create directory',
        'show_all': 'Show all',
        'sort_by': 'Sort by (name/type/size)',
        'search_name': 'Search by name',
        'update_name': 'Update name',
        'delete': 'Delete',
        'exit': 'Exit',
        'choose_action': 'Choose an action: ',
        'file_name': 'File name: ',
        'directory_name': 'Directory name: ',
        'parent_id': 'Parent ID (or empty): ',
        'file_path': 'File path: ',
        'directory_path': 'Directory path: ',
        'file_saved': '✅ File saved.',
        'directory_saved': '✅ Directory saved.',
        'invalid_file': '❌ The specified path is not a file.',
        'invalid_dir': '❌ The specified path is not a directory.',
        'invalid_choice': '❌ Invalid choice. Try again.',
        'sort_invalid': '❌ Invalid sorting criteria.',
        'enter_name_to_search': 'Enter name to search: ',
        'update_id': 'ID of item to update: ',
        'new_name': 'New name: ',
        'delete_id': 'ID to delete: ',
        'exit_msg': '👋 Exit.',
        'no_data': 'No data.',
    }
}

current_lang = 'ru'

def t(key):
    return translations.get(current_lang, {}).get(key, key)

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
            item_id = int(item_id)
            conn = Database.connect()
            if conn:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("UPDATE items SET name = %s WHERE id = %s", (new_name, item_id))
                        print("✅ " + t('update_name'))
        except ValueError:
            print("❌ Неверный формат ID.")
        except psycopg2.Error as e:
            print(f"Ошибка при обновлении: {e}")

    @staticmethod
    def delete(item_id):
        try:
            item_id = int(item_id)
            conn = Database.connect()
            if conn:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("UPDATE items SET deleted_at = %s WHERE id = %s", (datetime.now(), item_id))
                        print("✅ " + t('delete'))
        except ValueError:
            print("❌ Неверный формат ID.")
        except psycopg2.Error as e:
            print(f"Ошибка при удалении: {e}")

# =================== CHILD CLASSES ===================
class File(Item):
    def __init__(self, name, parent_id, absolute_path):
        if not os.path.isfile(absolute_path):
            raise ValueError(t('invalid_file'))
        size = os.path.getsize(absolute_path)
        super().__init__(name, 'file', parent_id, absolute_path, size)

class Directory(Item):
    def __init__(self, name, parent_id, absolute_path):
        if not os.path.isdir(absolute_path):
            create = input(f"{absolute_path} {t('invalid_dir')} {t('create_directory')}? (y/n): ").strip().lower()
            if create == 'y':
                os.makedirs(absolute_path)
            else:
                raise ValueError(t('invalid_dir'))
        super().__init__(name, 'directory', parent_id, absolute_path)

# =================== UTIL ===================
def display_items(items):
    if not items:
        print(t('no_data'))
    else:
        print(tabulate(items, headers="keys", tablefmt="grid"))

# =================== MAIN MENU ===================
#choose language
def main():
    global current_lang
    lang = input("Выберите язык (ru/uz/en): ").strip().lower()
    if lang in translations:
        current_lang = lang

    Database.create_table()

    while True:
        print(f"""
              ====== {t('menu_title')} ======
              1. {t('create_file')}
              2. {t('create_directory')}
              3. {t('show_all')}
              4. {t('sort_by')}
              5. {t('search_name')}
              6. {t('update_name')}
              7. {t('delete')}
              8. {t('exit')}
              """)
        choice = input(t('choose_action')).strip()

        if choice == '1':
            name = input(t('file_name'))
            parent = input(t('parent_id')) or None
            path = input(t('file_path'))
            try:
                file = File(name, parent, path)
                file.save()
                print(t('file_saved'))
            except ValueError as e:
                print(e)

        elif choice == '2':
            name = input(t('directory_name'))
            parent = input(t('parent_id')) or None
            path = input(t('directory_path'))
            try:
                directory = Directory(name, parent, path)
                directory.save()
                print(t('directory_saved'))
            except ValueError as e:
                print(e)

        elif choice == '3':
            items = Item.get_all()
            display_items(items)

        elif choice == '4':
            by = input(t('sort_by')).strip().lower()
            if by in ['name', 'type', 'size']:
                items = Item.get_all(order_by=by)
                display_items(items)
            else:
                print(t('sort_invalid'))

        elif choice == '5':
            name = input(t('enter_name_to_search'))
            items = Item.search_by_name(name)
            display_items(items)

        elif choice == '6':
            item_id = input(t('update_id'))
            new_name = input(t('new_name'))
            Item.update(item_id, new_name)

        elif choice == '7':
            item_id = input(t('delete_id'))
            Item.delete(item_id)

        elif choice == '8':
            print(t('exit_msg'))
            break

        else:
            print(t('invalid_choice'))

if __name__ == "__main__":
    main()