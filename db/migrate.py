#!/usr/bin/env python3
"""
Скрипт міграції бази даних для MyWebApp
Підтримує PostgreSQL та MariaDB/MySQL
"""

import sys
import argparse
import psycopg2
import pymysql


def migrate_postgresql(host, database, user, password, app_type):
    """Міграція для PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cursor = connection.cursor()
        
        print(f"Creating tables for {app_type} service on PostgreSQL...")
        
        if app_type == 'notes':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✓ Created 'notes' table")
            
        elif app_type == 'tasks':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✓ Created 'tasks' table")
            
        elif app_type == 'inventory':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    quantity INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✓ Created 'items' table")
        
        # Створення індексів для покращення продуктивності
        if app_type == 'notes':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)')
        elif app_type == 'tasks':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)')
        elif app_type == 'inventory':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_quantity ON items(quantity)')
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✓ PostgreSQL migration completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL migration failed: {e}")
        return False


def migrate_mysql(host, database, user, password, app_type):
    """Міграція для MariaDB/MySQL"""
    try:
        connection = pymysql.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        
        print(f"Creating tables for {app_type} service on MySQL/MariaDB...")
        
        if app_type == 'notes':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✓ Created 'notes' table")
            
        elif app_type == 'tasks':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✓ Created 'tasks' table")
            
        elif app_type == 'inventory':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    quantity INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("✓ Created 'items' table")
        
        # Створення індексів
        if app_type == 'notes':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)')
        elif app_type == 'tasks':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)')
        elif app_type == 'inventory':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_quantity ON items(quantity)')
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✓ MySQL/MariaDB migration completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ MySQL/MariaDB migration failed: {e}")
        return False


def main():
    """Головна функція"""
    parser = argparse.ArgumentParser(description='Database migration script for MyWebApp')
    parser.add_argument('--db-type', choices=['postgresql', 'mysql'], required=True,
                       help='Database type')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-name', default='mywebapp', help='Database name')
    parser.add_argument('--db-user', default='app', help='Database user')
    parser.add_argument('--db-password', default='apppassword', help='Database password')
    parser.add_argument('--app-type', choices=['notes', 'tasks', 'inventory'], 
                       default='notes', help='Application type')
    
    args = parser.parse_args()
    
    print(f"Starting database migration...")
    print(f"Database: {args.db_type} at {args.db_host}/{args.db_name}")
    print(f"Application: {args.app_type}")
    print("-" * 50)
    
    # Виконання міграції
    if args.db_type == 'postgresql':
        success = migrate_postgresql(
            args.db_host, args.db_name, 
            args.db_user, args.db_password, 
            args.app_type
        )
    else:
        success = migrate_mysql(
            args.db_host, args.db_name,
            args.db_user, args.db_password,
            args.app_type
        )
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
