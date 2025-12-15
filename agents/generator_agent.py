# agents/generator_agent.py
from typing import List, Dict
from datetime import datetime
from utils import ask_ai

class GeneratorAgent:
    """
    Агент 4:
    Агент-генератор с использованием ask_ai
    """
    
    def __init__(self):
        self.generation_history = []
    
    def generate_similar_tasks(self, original_task: str, 
                              task_analysis: Dict,
                              count: int = 2) -> List[str]:
        """Генерирует похожие задачи через ask_ai"""
        
        prompt = self._create_generation_prompt(original_task, task_analysis, count)
        
        try:
            # Используем твою функцию ask_ai
            response = ask_ai(prompt)
            
            # УБИРАЕМ $ ПРЯМО ЗДЕСЬ
            response = response.replace('$', '')

            # Парсим ответ
            tasks = self._parse_generated_tasks(response, count)
            
            # Сохраняем в историю
            self._save_to_history(original_task, tasks, task_analysis)
            
            return tasks
            
        except Exception as e:
            print(f"Ошибка генерации: {e}")
            return self._generate_fallback_tasks(original_task, count)
    
    def _create_generation_prompt(self, original_task: str, 
                                 analysis: Dict, 
                                 count: int) -> str:
        """Создает промпт для генерации"""
        
        return f"""
        Сгенерируй {count} похожих математических задач на основе этой:
        
        Оригинальная задача: {original_task}
        
        Характеристики:
        - Тип: {analysis.get('task_type', 'неизвестно')}
        - Сложность: {analysis.get('difficulty_level', 'средняя')}
        - Ключевые темы: {', '.join(analysis.get('keywords', []))}
        
        Требования:
        1. Сохрани тип и метод решения
        2. Измени числа, контекст, но оставь структуру
        3. Сохрани уровень сложности
        4. Задачи должны быть из ЕГЭ по математике
        5. Пронумеруй задачи: 1), 2), 3)
        
        Только условия задач, без решений!
        """
    
    def _parse_generated_tasks(self, response: str, expected_count: int) -> List[str]:
        """Парсит сгенерированные задачи из ответа"""
        tasks = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Ищем пронумерованные задачи
            if line.startswith(('1)', '2)', '3)', '4)', '5)', 
                              '1.', '2.', '3.', '4.', '5.',
                              'Задача 1:', 'Задача 2:', 'Задача 3:')):
                task = line.split(')', 1)[1] if ')' in line else line.split(':', 1)[1]
                tasks.append(task.strip())
            elif line and len(tasks) < expected_count and len(line) > 20:
                # Если нет нумерации, но текст похож на задачу
                tasks.append(line)
        
        # Если не нашли достаточно задач, создаем свои
        if len(tasks) < expected_count:
            for i in range(len(tasks), expected_count):
                tasks.append(f"Похожая задача {i+1} (сгенерирована)")
        
        return tasks[:expected_count]
    
    def _generate_fallback_tasks(self, original_task: str, count: int) -> List[str]:
        """Заглушка если генерация не сработала"""
        tasks = []
        for i in range(count):
            tasks.append(f"Задача {i+1} похожая на: '{original_task[:50]}...'")
        return tasks
    
    def _save_to_history(self, original: str, generated: List[str], analysis: Dict):
        """Сохраняет в историю для будущего использования"""
        self.generation_history.append({
            "timestamp": datetime.now().isoformat(),
            "original": original,
            "generated": generated,
            "analysis": analysis
        })
        
        # Ограничиваем размер истории
        if len(self.generation_history) > 50:
            self.generation_history = self.generation_history[-50:]
    
    def generate_simple_task(self, user_task: str) -> str:
        """Простая генерация одной задачи (для кнопки без агентов)"""
        prompt = f"Сгенерируй похожую задачу: {user_task}"
        try:
            response = ask_ai(prompt)
            return response.replace('$', '')  # Убираем $ здесь
        except:
            return "Похожая задача на эту тему"