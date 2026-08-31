from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Функция подключения к БД
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'notesdb'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres')
    )
    return conn

# Инициализация таблицы при старте
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Главная страница
@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to SRE Notes API!',
        'endpoints': {
            'GET /notes': 'List all notes',
            'POST /notes': 'Create new note',
            'GET /health': 'Health check'
        }
    })

# Health check (для мониторинга)
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# Получить все заметки
@app.route('/notes', methods=['GET'])
def get_notes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC')
    notes = cur.fetchall()
    cur.close()
    conn.close()
    
    notes_list = []
    for note in notes:
        notes_list.append({
            'id': note[0],
            'title': note[1],
            'content': note[2],
            'created_at': note[3].strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(notes_list)

# Создать новую заметку
@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    title = data['title']
    content = data.get('content', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO notes (title, content) VALUES (%s, %s) RETURNING id',
        (title, content)
    )
    note_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'id': note_id, 'message': 'Note created successfully'}), 201

if __name__ == '__main__':
    # Инициализируем БД при старте
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)