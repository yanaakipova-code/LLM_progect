# agents/solver_agent.py
from typing import Dict, List, Tuple
from utils import ask_ai
import re

class SolverAgent:
    """
    Агент 5: Решатель задач
    Решает задачи, проверяет ответы пользователя, ведет статистику решений
    """
    
    def __init__(self, memory_agent=None):
        self.memory_agent = memory_agent
        self.solution_cache = {}
        self.solution_history = []
    
    def solve_and_explain(self, task_text: str, task_type: str = None) -> Dict:
        """Решает задачу и дает подробное объяснение"""
        
        # Проверяем кэш
        cache_key = task_text[:100]
        if cache_key in self.solution_cache:
            return self.solution_cache[cache_key]
        
        prompt = self._create_solution_prompt(task_text, task_type)
        
        try:
            response = ask_ai(prompt)
            
            # Извлекаем ответ и решение
            solution_data = {
                "full_solution": response,
                "short_answer": self._extract_short_answer(response),
                "step_by_step": self._extract_steps(response),
                "explanation": self._extract_explanation(response),
                "hints": self._generate_hints(task_text),
                "success": True
            }
            
            # Кэшируем
            self.solution_cache[cache_key] = solution_data
            
            # Сохраняем в историю
            self.solution_history.append({
                "task": task_text,
                "solution": solution_data,
                "timestamp": self._get_timestamp()
            })
            
            return solution_data
            
        except Exception as e:
            print(f"Ошибка решения: {e}")
            return {
                "full_solution": "Не удалось решить задачу",
                "short_answer": "Неизвестно",
                "step_by_step": [],
                "explanation": "Ошибка при обращении к ИИ",
                "hints": ["Попробуйте решить самостоятельно"],
                "success": False
            }
    
    def check_user_answer(self, user_answer: str, task_text: str, 
                         correct_answer: str = None) -> Tuple[bool, str, str]:
        """
        Проверяет ответ пользователя
        Возвращает: (правильность, пояснение, верный_ответ)
        """
        
        # Если не передан правильный ответ, вычисляем его
        if not correct_answer:
            solution = self.solve_and_explain(task_text)
            correct_answer = solution.get("short_answer", "")
        
        # Нормализуем ответы для сравнения
        user_norm = self._normalize_answer(user_answer)
        correct_norm = self._normalize_answer(correct_answer)
        
        # Сравниваем
        is_correct = self._compare_answers(user_norm, correct_norm)
        
        # Генерируем пояснение
        if is_correct:
            explanation = "✅ Ваш ответ правильный!"
        else:
            explanation = f"❌ Ваш ответ: {user_answer}\n✅ Правильный ответ: {correct_answer}"
        
        return is_correct, explanation, correct_answer
    
    def generate_practice_task(self, user_id: int, topic: str = None, 
                              difficulty: str = None) -> Dict:
        """Генерирует задачу для практики с учетом истории пользователя"""
        
        # Если есть память, получаем слабые темы пользователя
        weak_topics = []
        if self.memory_agent:
            stats = self.memory_agent.get_user_statistics(user_id)
            weak_topics = [t.get('topic') for t in stats.get('weak_topics', [])]
        
        # Выбираем тему
        if not topic and weak_topics:
            topic = weak_topics[0]  # Берем самую слабую тему
        
        prompt = f"""
        Сгенерируй математическую задачу из ЕГЭ.
        
        {"Тема: " + topic if topic else "Любая тема из ЕГЭ"}
        {"Сложность: " + difficulty if difficulty else "Средняя сложность"}
        
        Формат:
        ЗАДАЧА: [текст задачи]
        ОТВЕТ: [число или выражение]
        ТИП: [тип задачи]
        """
        
        try:
            response = ask_ai(prompt)
            
            # Парсим ответ
            task_data = {
                "task": "",
                "answer": "",
                "type": "общая математика"
            }
            
            lines = response.split('\n')
            for line in lines:
                line_lower = line.lower()
                if 'задача:' in line_lower:
                    task_data["task"] = line.split(':', 1)[1].strip()
                elif 'ответ:' in line_lower:
                    task_data["answer"] = line.split(':', 1)[1].strip()
                elif 'тип:' in line_lower:
                    task_data["type"] = line.split(':', 1)[1].strip()
            
            return task_data
            
        except Exception as e:
            print(f"Ошибка генерации задачи: {e}")
            # Заглушка
            return {
                "task": f"Задача по теме {topic or 'математика'}: Найдите значение выражения 2 + 2 × 2",
                "answer": "6",
                "type": "алгебра"
            }
    
    def _create_solution_prompt(self, task_text: str, task_type: str = None) -> str:
        """Создает промпт для решения задачи"""
        prompt = f"""
        Реши математическую задачу из ЕГЭ:
        
        "{task_text}"
        
        Дай подробное пошаговое решение на русском языке.
        В конце обязательно укажи окончательный ответ в формате: "Ответ: [число/выражение]"
        
        Структура:
        1. Понимание условия
        2. План решения
        3. Шаги решения
        4. Ответ
        5. Проверка (если возможно)
        6. Объяснение метода
        """
        
        if task_type:
            prompt += f"\nТип задачи: {task_type}"
            
        return prompt
    
    def _extract_short_answer(self, solution_text: str) -> str:
        """Извлекает краткий ответ - ПРОСТАЯ РАБОЧАЯ ВЕРСИЯ"""
        if not solution_text:
            return "Не найден"
        
        import re
        
        # Разбиваем текст на строки
        lines = solution_text.split('\n')
        
        # Ищем строку с "Ответ:"
        for line in reversed(lines):  # Ищем с конца
            line_lower = line.lower()
            if 'ответ' in line_lower:
                # Убираем "Ответ:" и все до него
                if ':' in line:
                    answer_part = line.split(':', 1)[1].strip()
                else:
                    answer_part = line.replace('Ответ', '').replace('ответ', '').strip()
                
                # Ищем числа в оставшейся части
                numbers = re.findall(r'[-+]?\d*\.?\d+', answer_part)
                if numbers:
                    return numbers[-1]
        
        # Если не нашли, ищем последнее число в тексте
        all_numbers = re.findall(r'[-+]?\d*\.?\d+', solution_text)
        if all_numbers:
            return all_numbers[-1]
        
        return "Не найден"
    
    def _extract_steps(self, solution_text: str) -> List[str]:
        """Извлекает шаги решения"""
        steps = []
        lines = solution_text.split('\n')
        
        current_step = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Определяем шаги
            if (re.match(r'^\d+[\.\)]', line) or 
                'шаг' in line.lower() or 
                'step' in line.lower()):
                if current_step:
                    steps.append(current_step)
                current_step = line
            elif current_step and len(line) > 10:
                current_step += " " + line
        
        if current_step:
            steps.append(current_step)
        
        return steps[:5]  # не более 5 шагов
    
    def _extract_explanation(self, solution_text: str) -> str:
        """Извлекает объяснение метода"""
        explanation_parts = []
        keywords = ['объяснение', 'пояснение', 'метод', 'способ', 'идея']
        
        lines = solution_text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                explanation_parts.append(line.strip())
        
        if explanation_parts:
            return " ".join(explanation_parts[:2])
        
        # Ищем последние строки как объяснение
        last_lines = lines[-3:]
        return " ".join([l.strip() for l in last_lines if l.strip()])
    
    def _generate_hints(self, task_text: str) -> List[str]:
        """Генерирует подсказки для задачи"""
        prompt = f"""
        Для задачи: "{task_text}"
        
        Дай 3 подсказки от простой к сложной, чтобы помочь решить задачу:
        1. Первая подсказка (самая простая)
        2. Вторая подсказка (средняя)
        3. Третья подсказка (почти решение)
        """
        
        try:
            response = ask_ai(prompt)
            hints = []
            
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or 'подсказка' in line.lower()):
                    hints.append(line)
            
            return hints[:3]
        except:
            return ["Внимательно прочитайте условие", "Разбейте задачу на части", "Проверьте вычисления"]
    
    def _normalize_answer(self, answer: str) -> str:
        """Нормализует ответ для сравнения"""
        if not answer:
            return ""
        
        # Приводим к строке
        answer = str(answer).strip().lower()
        
        # Убираем лишние символы
        remove_chars = ['$', '€', '£', '`', "'", '"', ' ', '\t', '\n', '\\']
        for char in remove_chars:
            answer = answer.replace(char, '')
        
        # Заменяем запятые на точки
        answer = answer.replace(',', '.')
        
        # Убираем лишние нули в конце десятичных дробей
        if '.' in answer:
            answer = answer.rstrip('0').rstrip('.')
        
        return answer
    
    def _compare_answers(self, user_answer: str, correct_answer: str) -> bool:
        """Сравнивает два ответа"""
        if user_answer == correct_answer:
            return True
        
        # Пробуем числовое сравнение
        try:
            import math
            user_num = float(user_answer)
            correct_num = float(correct_answer)
            
            # Допускаем погрешность 0.0001
            return math.isclose(user_num, correct_num, rel_tol=1e-4)
        except:
            return False
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
    
    def solve(self, task_text: str, task_type: str = None):
        """Простой метод для обратной совместимости - принимает task_type как опциональный"""
        result = self.solve_and_explain(task_text, task_type)
        return {
            "solution": result.get("full_solution", ""),
            "success": result.get("success", False)
        }