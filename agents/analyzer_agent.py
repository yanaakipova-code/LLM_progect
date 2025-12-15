# agents/analyzer_agent.py
import json
import re
from typing import Dict
from utils import ask_ai

class AnalyzerAgent:
    """
    Агент 1:
    Агент-анализатор с использованием GigaChat через ask_ai
    """
    
    def __init__(self):
        self.cache = {}  # Кэш для быстрого доступа
    
    def analyze_task(self, task_text: str) -> Dict:
        """Анализирует задачу через GigaChat"""
        
        # Проверяем кэш
        if task_text in self.cache:
            return self.cache[task_text]
        
        # Улучшенный промпт с четким требованием ТОЛЬКО JSON
        prompt = f"""
        Проанализируй математическую задачу:
        "{task_text}"
        
        Определи:
        1. Тип задачи (геометрия, алгебра, теория вероятностей, математический анализ, общая математика)
        2. Уровень сложности (легкий, средний, сложный)
        3. Ключевые темы/ключевые слова (максимум 5)
        4. Номера заданий ЕГЭ, к которым она относится (1-19)
        5. Ориентировочное время решения в минутах (1-15)
        
        ВАЖНО: Ответь ТОЛЬКО JSON объектом без каких-либо дополнительных пояснений, 
        текста до или после JSON. Только JSON.
        
        Формат JSON:
        {{
            "task_type": "тип задачи",
            "difficulty_level": "сложность",
            "keywords": ["ключ1", "ключ2"],
            "suggested_ege_task": [номера],
            "estimated_time_minutes": число
        }}
        """
        
        try:
            # Используем твою функцию ask_ai
            response = ask_ai(prompt)
            
            # Очищаем ответ от лишнего текста
            cleaned_response = self._clean_ai_response(response)
            
            # Пытаемся распарсить JSON
            analysis = json.loads(cleaned_response)
            
            # Валидируем и дополняем анализ
            analysis = self._validate_analysis(analysis, task_text)
            
            # Сохраняем в кэш
            self.cache[task_text] = analysis
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError при анализе задачи: {e}")
            print(f"Сырой ответ ИИ: {response}")
            print(f"Очищенный ответ: {cleaned_response}")
            return self._default_analysis(task_text)
        except Exception as e:
            print(f"Ошибка анализа: {e}")
            return self._default_analysis(task_text)
    
    def _clean_ai_response(self, response: str) -> str:
        """Очищает ответ ИИ, оставляя только JSON"""
        
        # Убираем markdown блоки
        response = response.strip()
        
        # Ищем JSON паттерн { ... }
        json_pattern = r'\{[^{}]*\}'
        
        # Находим самый длинный JSON-подобный объект
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            # Берем самый длинный найденный JSON
            cleaned = max(matches, key=len)
            
            # Убираем markdown обрамление если есть
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            # Убираем лишние пробелы и переносы
            cleaned = cleaned.strip()
            
            # Проверяем, что это валидный JSON
            try:
                json.loads(cleaned)
                return cleaned
            except:
                pass
        
        # Если не нашли JSON, попробуем другой подход
        # Ищем начало {
        start = response.find('{')
        # Ищем конец }
        end = response.rfind('}') + 1
        
        if start != -1 and end != 0:
            json_candidate = response[start:end]
            try:
                json.loads(json_candidate)
                return json_candidate
            except:
                pass
        
        # Если все попытки неудачны, возвращаем дефолтный JSON
        print("Не удалось найти валидный JSON в ответе ИИ")
        default_json = {
            "task_type": "общая математика",
            "difficulty_level": "средний",
            "keywords": [],
            "suggested_ege_task": [1, 2, 3],
            "estimated_time_minutes": 5
        }
        return json.dumps(default_json)
    
    def _validate_analysis(self, analysis: Dict, task_text: str) -> Dict:
        """Валидирует и дополняет анализ"""
        
        required_keys = ["task_type", "difficulty_level", "keywords", 
                        "suggested_ege_task", "estimated_time_minutes"]
        
        # Гарантируем наличие всех ключей
        result = analysis.copy()
        
        if "task_type" not in result:
            result["task_type"] = "общая математика"
        
        if "difficulty_level" not in result:
            # Простая эвристика по длине
            words = len(task_text.split())
            if words < 20:
                result["difficulty_level"] = "легкий"
            elif words < 40:
                result["difficulty_level"] = "средний"
            else:
                result["difficulty_level"] = "сложный"
        
        if "keywords" not in result or not isinstance(result["keywords"], list):
            result["keywords"] = self._extract_keywords(task_text)
        
        if "suggested_ege_task" not in result or not isinstance(result["suggested_ege_task"], list):
            result["suggested_ege_task"] = [1, 2, 3]
        
        if "estimated_time_minutes" not in result or not isinstance(result["estimated_time_minutes"], int):
            result["estimated_time_minutes"] = 5
            
        return result
    
    def _default_analysis(self, task_text: str) -> Dict:
        """Дефолтный анализ если GigaChat не сработал"""
        task_lower = task_text.lower()
        
        # Простая логика
        if any(word in task_lower for word in ["треугольник", "угол", "окружность", "площадь", "объем"]):
            task_type = "геометрия"
        elif any(word in task_lower for word in ["вероятность", "комбинаторика", "статистика"]):
            task_type = "теория вероятностей"
        elif any(word in task_lower for word in ["уравнение", "функция", "логарифм", "степень"]):
            task_type = "алгебра"
        elif any(word in task_lower for word in ["производная", "интеграл", "предел"]):
            task_type = "математический анализ"
        else:
            task_type = "общая математика"
        
        # Оценка сложности по длине
        words = len(task_text.split())
        if words < 15:
            difficulty = "легкий"
        elif words < 30:
            difficulty = "средний"
        else:
            difficulty = "сложный"
        
        return {
            "task_type": task_type,
            "difficulty_level": difficulty,
            "keywords": self._extract_keywords(task_text),
            "suggested_ege_task": [1, 2, 3],
            "estimated_time_minutes": 5
        }
    
    def _extract_keywords(self, text: str):
        """Извлекает ключевые слова"""
        math_words = {
            "геометрия": ["треугольник", "угол", "окружность", "вектор", "площадь", 
                         "объем", "пирамида", "призма", "шар", "конус"],
            "алгебра": ["уравнение", "функция", "логарифм", "корень", "система",
                       "неравенство", "степень", "модуль", "параметр"],
            "теория вероятностей": ["вероятность", "комбинаторика", "случай", "выбор",
                                  "группа", "команда", "распределение", "статистика"],
            "математический анализ": ["производная", "интеграл", "предел", "дифференциал",
                                     "функция", "график", "экстремум", "асимптота"]
        }
        
        keywords = []
        text_lower = text.lower()
        
        for category, words in math_words.items():
            for word in words:
                if word in text_lower and word not in keywords:
                    keywords.append(word)
                    if len(keywords) >= 5:
                        break
            if len(keywords) >= 5:
                break
        
        return keywords[:5]
    
    
