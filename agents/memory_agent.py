# agents/memory_agent.py
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import json

class MemoryAgent:
    """
    Агент 2: Память и история
    """
    
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Инициализирует базу данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Таблица пользователей
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, 
                      username TEXT,
                      first_name TEXT,
                      created_at TIMESTAMP)''')
        
        # Таблица истории задач
        c.execute('''CREATE TABLE IF NOT EXISTS task_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      original_task TEXT,
                      task_type TEXT,
                      difficulty TEXT,
                      correct INTEGER DEFAULT 0,
                      timestamp TIMESTAMP)''')
        
        # Таблица правильных решений
        c.execute('''CREATE TABLE IF NOT EXISTS correct_answers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      task_type TEXT,
                      timestamp TIMESTAMP)''')
        
        # Таблица ошибок
        c.execute('''CREATE TABLE IF NOT EXISTS wrong_answers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      task_type TEXT,
                      error_reason TEXT,
                      timestamp TIMESTAMP)''')
        
        conn.commit()
        conn.close()
    
    def record_task_attempt(self, user_id: int, 
                           original_task: str,
                           task_analysis: Dict,
                           correct: int = 0):  # 0=неизвестно, 1=правильно, -1=неправильно
        """Записывает попытку решения задачи"""
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Добавляем пользователя если его нет
        c.execute('''INSERT OR IGNORE INTO users 
                     (user_id, created_at) VALUES (?, ?)''',
                  (user_id, datetime.now()))
        
        # Сохраняем историю задачи
        c.execute('''INSERT INTO task_history 
                     (user_id, original_task, task_type, difficulty, correct, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id,
                   original_task[:500],  # Ограничиваем длину
                   task_analysis.get('task_type', 'unknown'),
                   task_analysis.get('difficulty_level', 'medium'),
                   correct,
                   datetime.now()))
        
        # Если правильно - записываем в отдельную таблицу
        if correct == 1:
            c.execute('''INSERT INTO correct_answers 
                         (user_id, task_type, timestamp)
                         VALUES (?, ?, ?)''',
                      (user_id, 
                       task_analysis.get('task_type', 'unknown'),
                       datetime.now()))
        
        # Если неправильно - записываем ошибку
        elif correct == -1:
            c.execute('''INSERT INTO wrong_answers 
                         (user_id, task_type, error_reason, timestamp)
                         VALUES (?, ?, ?, ?)''',
                      (user_id,
                       task_analysis.get('task_type', 'unknown'),
                       'неправильное решение',
                       datetime.now()))
        
        conn.commit()
        conn.close()
    
    def mark_task_correct(self, user_id: int, task_id: int = None):
        """Отмечает задачу как решенную правильно"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if task_id:
            # Обновляем конкретную запись
            c.execute('''UPDATE task_history 
                         SET correct = 1 
                         WHERE id = ? AND user_id = ?''',
                      (task_id, user_id))
        else:
            # Обновляем последнюю запись пользователя
            c.execute('''UPDATE task_history 
                         SET correct = 1 
                         WHERE id = (SELECT MAX(id) FROM task_history WHERE user_id = ?)''',
                      (user_id,))
        
        conn.commit()
        conn.close()
    
    def mark_task_wrong(self, user_id: int, task_id: int = None, reason: str = ""):
        """Отмечает задачу как решенную неправильно"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if task_id:
            c.execute('''UPDATE task_history 
                         SET correct = -1 
                         WHERE id = ? AND user_id = ?''',
                      (task_id, user_id))
        else:
            c.execute('''UPDATE task_history 
                         SET correct = -1 
                         WHERE id = (SELECT MAX(id) FROM task_history WHERE user_id = ?)''',
                      (user_id,))
        
        # Записываем причину ошибки
        if reason:
            last_task = self.get_last_task(user_id)
            if last_task:
                c.execute('''INSERT INTO wrong_answers 
                             (user_id, task_type, error_reason, timestamp)
                             VALUES (?, ?, ?, ?)''',
                          (user_id, last_task.get('task_type'), reason, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """Получает реальную статистику пользователя - УЧИТЫВАЕТ ТОЛЬКО ПРОБОВАННЫЕ ЗАДАЧИ"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Считаем ТОЛЬКО задачи, которые пользователь пытался решить (correct=1 или -1)
        c.execute('''SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct,
                        SUM(CASE WHEN correct = -1 THEN 1 ELSE 0 END) as wrong
                    FROM task_history 
                    WHERE user_id = ? AND correct != 0''', (user_id,))
        
        total, correct, wrong = c.fetchone()
        total = total or 0
        correct = correct or 0
        wrong = wrong or 0
        
        # Статистика по темам (только пробованные задачи)
        c.execute('''SELECT 
                        task_type,
                        COUNT(*) as total,
                        SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct
                    FROM task_history 
                    WHERE user_id = ? AND correct != 0
                    GROUP BY task_type
                    ORDER BY total DESC''', (user_id,))
        
        topics_stats = []
        for task_type, topic_total, topic_correct in c.fetchall():
            accuracy = (topic_correct / topic_total * 100) if topic_total > 0 else 0
            topics_stats.append({
                "topic": task_type,
                "total": topic_total,
                "correct": topic_correct or 0,
                "accuracy": round(accuracy, 1),
                "weak": accuracy < 50  # Менее 50% - слабая тема
            })
        
        # Слабые темы (где точность < 50%)
        weak_topics = [t for t in topics_stats if t['weak']]
        
        # Активность (только пробованные задачи за последнюю неделю)
        week_ago = datetime.now() - timedelta(days=7)
        c.execute('''SELECT COUNT(*) FROM task_history 
                    WHERE user_id = ? AND timestamp > ? AND correct != 0''',
                (user_id, week_ago))
        recent_tasks = c.fetchone()[0] or 0
        
        if recent_tasks >= 7:
            activity = "высокая"
        elif recent_tasks >= 3:
            activity = "средняя"
        else:
            activity = "низкая"
        
        conn.close()
        
        # Рассчитываем точность (только по пробованным задачам)
        accuracy = 0
        if total > 0:
            accuracy = (correct / total * 100)
        
        return {
            "total_tasks": total,  # Только пробованные задачи
            "correct_answers": correct,
            "wrong_answers": wrong,
            "accuracy": round(accuracy, 1),
            "topics": topics_stats,
            "weak_topics": weak_topics[:3],  # Только 3 самых слабых
            "activity_level": activity,
            "last_active": self.get_last_activity(user_id)
        }



    def get_last_task(self, user_id: int):
        """Получает последнюю задачу пользователя"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT id, original_task, task_type, correct, timestamp
                     FROM task_history 
                     WHERE user_id = ?
                     ORDER BY timestamp DESC
                     LIMIT 1''', (user_id,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "task": row[1],
                "type": row[2],
                "correct": row[3],
                "timestamp": row[4]
            }
        return None
    
    def get_last_activity(self, user_id: int):
        """Получает время последней активности"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT timestamp FROM task_history 
                     WHERE user_id = ?
                     ORDER BY timestamp DESC
                     LIMIT 1''', (user_id,))
        
        row = c.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def get_user_progress(self, user_id: int, days: int = 30) -> List[Dict]:
        """Получает прогресс пользователя за N дней"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as total,
                        SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct
                     FROM task_history 
                     WHERE user_id = ? AND timestamp > ?
                     GROUP BY DATE(timestamp)
                     ORDER BY date''', (user_id, start_date))
        
        progress = []
        for date, total, correct in c.fetchall():
            progress.append({
                "date": date,
                "total": total,
                "correct": correct or 0
            })
        
        conn.close()
        return progress