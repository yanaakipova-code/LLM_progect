# agents/difficulty_agent.py
import json
from typing import Dict, List
from datetime import datetime

class DifficultyAgent:
    """
    Агент 3
    Агент адаптации сложности
    Анализирует успехи пользователя и подбирает подходящий уровень сложности
    """
    
    def __init__(self):
        self.user_profiles = {}  # user_id -> профиль
        self.difficulty_rules = self._load_difficulty_rules()
    
    def adjust_difficulty(self, user_id: int, 
                         task_analysis: Dict,
                         user_stats: Dict) -> Dict:
        """Адаптирует сложность задачи для пользователя"""
        
        # Получаем или создаем профиль пользователя
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_user_profile(user_stats)
        
        profile = self.user_profiles[user_id]
        
        # Определяем целевой уровень сложности
        target_difficulty = self._determine_target_difficulty(profile, user_stats)
        
        # Модифицируем задачу под нужную сложность
        adjusted_task = self._adjust_task_difficulty(task_analysis, 
                                                    target_difficulty)
        
        # Обновляем профиль пользователя
        self._update_user_profile(user_id, profile, task_analysis, 
                                 adjusted_task["difficulty_level"])
        
        return adjusted_task
    
    def _load_difficulty_rules(self) -> Dict:
        """Загружает правила адаптации сложности"""
        return {
            "easy_to_medium": {
                "condition": "accuracy > 80 AND recent_tasks > 5",
                "action": "increase_difficulty",
                "increment": 0.3
            },
            "medium_to_hard": {
                "condition": "accuracy > 70 AND recent_medium_tasks > 3",
                "action": "increase_difficulty",
                "increment": 0.4
            },
            "hard_to_medium": {
                "condition": "accuracy < 40",
                "action": "decrease_difficulty",
                "decrement": 0.3
            },
            "medium_to_easy": {
                "condition": "accuracy < 30",
                "action": "decrease_difficulty",
                "decrement": 0.5
            }
        }
    
    def _create_user_profile(self, initial_stats: Dict) -> Dict:
        """Создает начальный профиль пользователя"""
        return {
            "initial_level": "medium",
            "current_difficulty": "medium",
            "difficulty_history": [],
            "accuracy_trend": [],
            "last_adjustment": datetime.now(),
            "total_adjustments": 0
        }
    
    def _determine_target_difficulty(self, profile: Dict, 
                                    stats: Dict) -> str:
        """Определяет целевой уровень сложности"""
        
        # Если мало данных - оставляем средний
        if stats.get("total_tasks", 0) < 3:
            return "medium"
        
        accuracy = stats.get("accuracy", 50)
        recent_tasks = len(stats.get("recent_tasks", []))
        
        # Правила адаптации
        if accuracy > 80 and recent_tasks >= 5:
            # Отличные результаты - увеличиваем сложность
            current = profile["current_difficulty"]
            if current == "easy":
                return "medium"
            elif current == "medium":
                return "hard"
        
        elif accuracy < 40 and recent_tasks >= 3:
            # Плохие результаты - уменьшаем сложность
            current = profile["current_difficulty"]
            if current == "hard":
                return "medium"
            elif current == "medium":
                return "easy"
        
        # Оставляем текущую сложность
        return profile["current_difficulty"]
    
    def _adjust_task_difficulty(self, task_analysis: Dict, 
                               target_difficulty: str) -> Dict:
        """Адаптирует задачу под нужную сложность"""
        
        original_diff = task_analysis.get("difficulty_level", "medium")
        
        # Если сложность уже целевая - не меняем
        if original_diff == target_difficulty:
            return task_analysis
        
        # Создаем модифицированный анализ
        modified = task_analysis.copy()
        
        # Меняем сложность
        modified["difficulty_level"] = target_difficulty
        
        # Адаптируем время решения
        time_multiplier = self._get_time_multiplier(original_diff, 
                                                   target_difficulty)
        if "estimated_time_minutes" in modified:
            modified["estimated_time_minutes"] = int(
                modified["estimated_time_minutes"] * time_multiplier
            )
        
        # Адаптируем рекомендуемые номера ЕГЭ
        if "suggested_ege_task" in modified:
            modified["suggested_ege_task"] = self._adjust_ege_tasks(
                modified["suggested_ege_task"], 
                target_difficulty
            )
        
        # Добавляем флаг адаптации
        modified["difficulty_adjusted"] = True
        modified["original_difficulty"] = original_diff
        
        return modified
    
    def _get_time_multiplier(self, from_diff: str, to_diff: str) -> float:
        """Множитель времени решения при изменении сложности"""
        multipliers = {
            ("easy", "medium"): 1.5,
            ("easy", "hard"): 2.5,
            ("medium", "easy"): 0.7,
            ("medium", "hard"): 1.8,
            ("hard", "easy"): 0.4,
            ("hard", "medium"): 0.6
        }
        
        return multipliers.get((from_diff, to_diff), 1.0)
    
    def _adjust_ege_tasks(self, ege_tasks: List[int], 
                         target_difficulty: str) -> List[int]:
        """Адаптирует номера заданий ЕГЭ под сложность"""
        difficulty_mapping = {
            "easy": [1, 2, 3, 4, 5],
            "medium": [6, 7, 8, 9, 10, 11, 12],
            "hard": [13, 14, 15, 16, 17, 18, 19]
        }
        
        return difficulty_mapping.get(target_difficulty, ege_tasks)
    
    def _update_user_profile(self, user_id: int, 
                            profile: Dict,
                            task_analysis: Dict,
                            actual_difficulty: str):
        """Обновляет профиль пользователя"""
        
        profile["current_difficulty"] = actual_difficulty
        profile["difficulty_history"].append({
            "timestamp": datetime.now().isoformat(),
            "task_type": task_analysis.get("task_type"),
            "difficulty_level": actual_difficulty,
            "original_difficulty": task_analysis.get("difficulty_level")
        })
        
        profile["last_adjustment"] = datetime.now()
        profile["total_adjustments"] += 1
        
        # Ограничиваем историю
        if len(profile["difficulty_history"]) > 20:
            profile["difficulty_history"] = profile["difficulty_history"][-20:]
        
        self.user_profiles[user_id] = profile

    def get_user_profile(self, user_id: int) -> Dict:
        """Возвращает профиль пользователя для статистики"""
        return self.user_profiles.get(user_id, {})