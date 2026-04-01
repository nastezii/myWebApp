#!/usr/bin/env python3
"""
MyWebApp - Веб-застосунок для лабораторної роботи №1
Підтримує три варіанти: Notes Service, Task Tracker, Simple Inventory
"""

import os
import sys
import json
import argparse
import datetime
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import psycopg2
import pymysql


class DatabaseManager:
    """Клас для роботи з базою даних"""
    
    def __init__(self, db_type: str, host: str, name: str, user: str, password: str):
        self.db_type = db_type
        self.host = host
        self.name = name
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        """Встановлення з'єднання з БД"""
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(
                    host=self.host,
                    database=self.name,
                    user=self.user,
                    password=self.password
                )
            else:  # mysql/mariadb
                self.connection = pymysql.connect(
                    host=self.host,
                    database=self.name,
                    user=self.user,
                    password=self.password,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Перевірка чи є активне з'єднання"""
        try:
            if self.connection:
                if self.db_type == 'postgresql':
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                else:
                    self.connection.ping(reconnect=True)
                return True
        except:
            pass
        return False
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Виконання SELECT запиту"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            if self.db_type == 'postgresql':
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
            else:
                result = cursor.fetchall()
            
            cursor.close()
            return result
        except Exception as e:
            print(f"Query execution error: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Виконання INSERT/UPDATE/DELETE запиту"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            last_id = cursor.lastrowid if self.db_type != 'postgresql' else cursor.fetchone()[0]
            cursor.close()
            return last_id
        except Exception as e:
            print(f"Update execution error: {e}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    def close(self):
        """Закриття з'єднання"""
        if self.connection:
            self.connection.close()


class NotesService:
    """Notes Service - сервіс для зберігання нотаток"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_tables(self):
        """Створення таблиць для нотаток"""
        if self.db.db_type == 'postgresql':
            query = '''
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        else:
            query = '''
                CREATE TABLE IF NOT EXISTS notes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        self.db.execute_update(query)
    
    def get_all_notes(self) -> List[Dict]:
        """Отримати список всіх нотаток (id, title)"""
        query = "SELECT id, title FROM notes ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def get_note_by_id(self, note_id: int) -> Optional[Dict]:
        """Отримати нотатку за ID"""
        query = "SELECT id, title, content, created_at FROM notes WHERE id = %s"
        result = self.db.execute_query(query, (note_id,))
        return result[0] if result else None
    
    def create_note(self, title: str, content: str) -> int:
        """Створити нову нотатку"""
        query = "INSERT INTO notes (title, content) VALUES (%s, %s)"
        return self.db.execute_update(query, (title, content))


class TaskTracker:
    """Task Tracker - сервіс для відстеження задач"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_tables(self):
        """Створення таблиць для задач"""
        if self.db.db_type == 'postgresql':
            query = '''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        else:
            query = '''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        self.db.execute_update(query)
    
    def get_all_tasks(self) -> List[Dict]:
        """Отримати список всіх задач"""
        query = "SELECT id, title, status, created_at FROM tasks ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def create_task(self, title: str) -> int:
        """Створити нову задачу"""
        query = "INSERT INTO tasks (title) VALUES (%s)"
        return self.db.execute_update(query, (title,))
    
    def mark_task_done(self, task_id: int) -> bool:
        """Відмітити задачу як виконану"""
        query = "UPDATE tasks SET status = 'done' WHERE id = %s"
        return self.db.execute_update(query, (task_id,)) > 0


class SimpleInventory:
    """Simple Inventory - сервіс обліку обладнання"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_tables(self):
        """Створення таблиць для інвентарю"""
        if self.db.db_type == 'postgresql':
            query = '''
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    quantity INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        else:
            query = '''
                CREATE TABLE IF NOT EXISTS items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    quantity INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        self.db.execute_update(query)
    
    def get_all_items(self) -> List[Dict]:
        """Отримати список всіх предметів (id, name)"""
        query = "SELECT id, name FROM items ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def get_item_by_id(self, item_id: int) -> Optional[Dict]:
        """Отримати детальну інформацію про предмет"""
        query = "SELECT id, name, quantity, created_at FROM items WHERE id = %s"
        result = self.db.execute_query(query, (item_id,))
        return result[0] if result else None
    
    def create_item(self, name: str, quantity: int) -> int:
        """Створити новий запис в інвентарі"""
        query = "INSERT INTO items (name, quantity) VALUES (%s, %s)"
        return self.db.execute_update(query, (name, quantity))


class MyWebApp:
    """Основний клас веб-застосунку"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Ініціалізація БД
        self.db = DatabaseManager(
            db_type=config['database']['type'],
            host=config['database']['host'],
            name=config['database']['name'],
            user=config['database']['user'],
            password=config['database']['password']
        )
        
        # Визначення типу застосунку
        app_type = config.get('app_type', 'notes')
        
        if app_type == 'tasks':
            self.service = TaskTracker(self.db)
            self.endpoints = [
                ('GET', '/tasks', 'Отримати список всіх задач'),
                ('POST', '/tasks', 'Створити нову задачу'),
                ('POST', '/tasks/<id>/done', 'Відмітити задачу як виконану')
            ]
        elif app_type == 'inventory':
            self.service = SimpleInventory(self.db)
            self.endpoints = [
                ('GET', '/items', 'Отримати список всіх предметів'),
                ('POST', '/items', 'Створити новий запис в інвентарі'),
                ('GET', '/items/<id>', 'Отримати детальну інформацію про предмет')
            ]
        else:  # notes
            self.service = NotesService(self.db)
            self.endpoints = [
                ('GET', '/notes', 'Отримати список всіх нотаток'),
                ('POST', '/notes', 'Створити нову нотатку'),
                ('GET', '/notes/<id>', 'Отримати повний вміст нотатки')
            ]
        
        self.setup_routes()
    
    def setup_routes(self):
        """Налаштування маршрутів"""
        
        @self.app.route('/')
        def index():
            """Кореневий ендпоінт - список всіх ендпоінтів"""
            html = """
            <html>
            <head><title>MyWebApp - API Endpoints</title></head>
            <body>
                <h1>MyWebApp API Endpoints</h1>
                <table border="1">
                    <tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
            """
            
            for method, endpoint, description in self.endpoints:
                html += f"<tr><td>{method}</td><td>{endpoint}</td><td>{description}</td></tr>"
            
            html += """
                </table>
                <h2>Health Check</h2>
                <table border="1">
                    <tr><th>Endpoint</th><th>Description</th></tr>
                    <tr><td>GET /health/alive</td><td>Health check - always returns OK</td></tr>
                    <tr><td>GET /health/ready</td><td>Readiness check - returns OK if DB is ready</td></tr>
                </table>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')
        
        @self.app.route('/health/alive')
        def health_alive():
            """Health check - завжди повертає OK"""
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'status': 'OK'})
            return Response('OK', status=200)
        
        @self.app.route('/health/ready')
        def health_ready():
            """Readiness check - перевіряє з'єднання з БД"""
            if self.db.is_connected():
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'status': 'OK', 'database': 'connected'})
                return Response('OK', status=200)
            else:
                error_msg = 'Database not connected'
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'status': 'ERROR', 'message': error_msg}), 500
                return Response(error_msg, status=500)
        
        # Маршрути для Notes Service
        if isinstance(self.service, NotesService):
            self.setup_notes_routes()
        elif isinstance(self.service, TaskTracker):
            self.setup_tasks_routes()
        elif isinstance(self.service, SimpleInventory):
            self.setup_inventory_routes()
    
    def setup_notes_routes(self):
        """Налаштування маршрутів для Notes Service"""
        
        @self.app.route('/notes', methods=['GET'])
        def get_notes():
            notes = self.service.get_all_notes()
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify(notes)
            
            html = """
            <html>
            <head><title>Notes</title></head>
            <body>
                <h1>Notes List</h1>
                <table border="1">
                    <tr><th>ID</th><th>Title</th></tr>
            """
            
            for note in notes:
                html += f"<tr><td>{note['id']}</td><td>{note['title']}</td></tr>"
            
            html += """
                </table>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')
        
        @self.app.route('/notes', methods=['POST'])
        def create_note():
            data = request.get_json() or request.form
            title = data.get('title')
            content = data.get('content', '')
            
            if not title:
                error = 'Title is required'
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': error}), 400
                return Response(error, status=400)
            
            note_id = self.service.create_note(title, content)
            
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'id': note_id, 'title': title, 'content': content}), 201
            
            return Response(f'Note created with ID: {note_id}', status=201)
        
        @self.app.route('/notes/<int:note_id>', methods=['GET'])
        def get_note(note_id):
            note = self.service.get_note_by_id(note_id)
            if not note:
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': 'Note not found'}), 404
                return Response('Note not found', status=404)
            
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify(note)
            
            html = f"""
            <html>
            <head><title>Note: {note['title']}</title></head>
            <body>
                <h1>{note['title']}</h1>
                <p><strong>ID:</strong> {note['id']}</p>
                <p><strong>Created:</strong> {note['created_at']}</p>
                <hr>
                <pre>{note['content']}</pre>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')
    
    def setup_tasks_routes(self):
        """Налаштування маршрутів для Task Tracker"""
        
        @self.app.route('/tasks', methods=['GET'])
        def get_tasks():
            tasks = self.service.get_all_tasks()
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify(tasks)
            
            html = """
            <html>
            <head><title>Tasks</title></head>
            <body>
                <h1>Tasks List</h1>
                <table border="1">
                    <tr><th>ID</th><th>Title</th><th>Status</th><th>Created</th></tr>
            """
            
            for task in tasks:
                html += f"<tr><td>{task['id']}</td><td>{task['title']}</td><td>{task['status']}</td><td>{task['created_at']}</td></tr>"
            
            html += """
                </table>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')
        
        @self.app.route('/tasks', methods=['POST'])
        def create_task():
            data = request.get_json() or request.form
            title = data.get('title')
            
            if not title:
                error = 'Title is required'
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': error}), 400
                return Response(error, status=400)
            
            task_id = self.service.create_task(title)
            
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'id': task_id, 'title': title, 'status': 'pending'}), 201
            
            return Response(f'Task created with ID: {task_id}', status=201)
        
        @self.app.route('/tasks/<int:task_id>/done', methods=['POST'])
        def mark_task_done(task_id):
            if self.service.mark_task_done(task_id):
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'id': task_id, 'status': 'done'})
                return Response(f'Task {task_id} marked as done')
            else:
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': 'Task not found'}), 404
                return Response('Task not found', status=404)
    
    def setup_inventory_routes(self):
        """Налаштування маршрутів для Simple Inventory"""
        
        @self.app.route('/items', methods=['GET'])
        def get_items():
            items = self.service.get_all_items()
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify(items)
            
            html = """
            <html>
            <head><title>Inventory Items</title></head>
            <body>
                <h1>Inventory Items</h1>
                <table border="1">
                    <tr><th>ID</th><th>Name</th></tr>
            """
            
            for item in items:
                html += f"<tr><td>{item['id']}</td><td>{item['name']}</td></tr>"
            
            html += """
                </table>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')
        
        @self.app.route('/items', methods=['POST'])
        def create_item():
            data = request.get_json() or request.form
            name = data.get('name')
            quantity = data.get('quantity', 0)
            
            if not name:
                error = 'Name is required'
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': error}), 400
                return Response(error, status=400)
            
            try:
                quantity = int(quantity)
            except ValueError:
                error = 'Quantity must be a number'
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': error}), 400
                return Response(error, status=400)
            
            item_id = self.service.create_item(name, quantity)
            
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'id': item_id, 'name': name, 'quantity': quantity}), 201
            
            return Response(f'Item created with ID: {item_id}', status=201)
        
        @self.app.route('/items/<int:item_id>', methods=['GET'])
        def get_item(item_id):
            item = self.service.get_item_by_id(item_id)
            if not item:
                if 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': 'Item not found'}), 404
                return Response('Item not found', status=404)
            
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify(item)
            
            html = f"""
            <html>
            <head><title>Item: {item['name']}</title></head>
            <body>
                <h1>{item['name']}</h1>
                <p><strong>ID:</strong> {item['id']}</p>
                <p><strong>Quantity:</strong> {item['quantity']}</p>
                <p><strong>Created:</strong> {item['created_at']}</p>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')
    
    def run(self):
        """Запуск застосунку"""
        # Підключення до БД
        if not self.db.connect():
            print("Failed to connect to database")
            sys.exit(1)
        
        # Створення таблиць
        self.service.create_tables()
        
        # Запуск Flask застосунку
        host = self.config.get('host', '127.0.0.1')
        port = self.config.get('port', 8080)
        
        print(f"Starting MyWebApp on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """Завантаження конфігурації з файлу"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Визначення типу БД на основі наявності драйвера
    config['database']['type'] = 'postgresql' if 'psycopg2' in sys.modules else 'mysql'
    
    return config


def main():
    """Головна функція"""
    parser = argparse.ArgumentParser(description='MyWebApp - Web Service for Lab #1')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-name', default='mywebapp', help='Database name')
    parser.add_argument('--db-user', default='app', help='Database user')
    parser.add_argument('--db-password', default='apppassword', help='Database password')
    parser.add_argument('--app-type', choices=['notes', 'tasks', 'inventory'], 
                       default='notes', help='Application type')
    
    args = parser.parse_args()
    
    # Завантаження конфігурації
    if args.config:
        config = load_config_from_file(args.config)
    else:
        config = {
            'host': args.host,
            'port': args.port,
            'app_type': args.app_type,
            'database': {
                'host': args.db_host,
                'name': args.db_name,
                'user': args.db_user,
                'password': args.db_password,
                'type': 'postgresql' if 'psycopg2' in sys.modules else 'mysql'
            }
        }
    
    # Створення та запуск застосунку
    app = MyWebApp(config)
    app.run()


if __name__ == '__main__':
    main()
