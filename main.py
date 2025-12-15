# main.py
import telebot
import time
from telebot import types
import re


# Импорт агентов
from agents.analyzer_agent import AnalyzerAgent
from agents.generator_agent import GeneratorAgent
from agents.memory_agent import MemoryAgent
from agents.difficulty_agent import DifficultyAgent
from agents.solver_agent import SolverAgent

# Настройки
TOKEN = '8204844500:AAG1mePjRocfzh-VwKCrp9asArkA6keYaz4'
bot = telebot.TeleBot(TOKEN)

# Инициализация агентов
print("🤖 Инициализация агентов...")
analyzer = AnalyzerAgent()
generator = GeneratorAgent()
memory = MemoryAgent()
difficulty = DifficultyAgent()
solver = SolverAgent(memory_agent=memory)
print("✅ Все 5 агентов готовы!")

#функции для безопасного форматирования:
def safe_markdown(text: str) -> str:
    """Экранирует специальные символы для Markdown"""
    # Экранируем основные символы Markdown
    replacements = {
        '_': '\\_',
        '*': '\\*',
        '[': '\\[',
        ']': '\\]',
        '(': '\\(',
        ')': '\\)',
        '~': '\\~',
        '`': '\\`',
        '>': '\\>',
        '#': '\\#',
        '+': '\\+',
        '-': '\\-',
        '=': '\\=',
        '|': '\\|',
        '{': '\\{',
        '}': '\\}',
        '.': '\\.',
        '!': '\\!'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def send_safe_message(chat_id, text, reply_markup=None):
    """Безопасная отправка сообщения"""
    # Всегда отправляем как обычный текст, без Markdown
    try:
        bot.send_message(chat_id, text, parse_mode=None, reply_markup=reply_markup)
    except Exception as e:
        # Если ошибка, пробуем экранировать
        print(f"Ошибка отправки: {e}")
        safe_text = safe_markdown(text)
        bot.send_message(chat_id, safe_text, parse_mode=None, reply_markup=reply_markup)


#показать главное меню
def show_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "📚 Материалы",
        "🧠 Генерация", 
        "🤖 Агентная система",
        "📊 Статистика",
        "🧩 Проверить ответ"
    ]
    for btn in buttons:
        markup.add(types.KeyboardButton(btn))
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    markup = show_main_menu()
    bot.send_message(
        message.chat.id,
        "👋 Бот с 5 агентами для ЕГЭ!\nВыбери действие:",
        reply_markup=markup
    )


#база материалов
MATERIALS_DATABASE = {
    "1": {
        "title": "📐 Задание 1: Простейшие текстовые задачи",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1qdbWfsHHw-pK7iOSV7rfUlJkHLHrta5i/view"
        ],
        "videos": [
            "🎥 Основные факты для задания 1: https://yandex.ru/video/preview/364678334217663889",
            "🎥 Решение первой задачи в одном видео: https://yandex.ru/video/preview/1361262772951039984",
            "🎥 Еще один разбор задания 1: https://yandex.ru/video/preview/2819572906190072463"
        ]
    },
    "2": {
        "title": "📐 Задание 2: Графики и диаграммы",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1bYy5VAXIhn5PAUOxAKJFzBB3DZL-xj-z/view"
        ],
        "videos": [
            "🎥 Решение второй задачи: https://yandex.ru/video/preview/11606668279920598867",
            "🎥 Разбор задания 2: https://yandex.ru/video/preview/14837341659686730149",
            "🎥 Еще один видеоразбор: https://yandex.ru/video/preview/10836725339440036918"
        ]
    },
    "3": {
        "title": "📐 Задание 3: Планиметрия (клетки, координаты)",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/10HGEEq_XSWH4Dhq1wGTFZ3E2i3bfPGPA/view"
        ],
        "videos": [
            "🎥 Решение третьей задачи: https://yandex.ru/video/preview/9523619264972064484",
            "🎥 Разбор задания 3: https://yandex.ru/video/preview/16130713948478353205"
        ]
    },
    "4": {
        "title": "📐 Задание 4: Теория вероятностей",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1Rocm3jB3B06ObE4CSyKekLIY2ECwhjRR/view"
        ],
        "videos": [
            "🎥 Видео 1: https://yandex.ru/video/touch/preview/1157262909225731119",
            "🎥 Видео 2: https://vkvideo.ru/video-168456727_456316320",
            "🎥 Видео 3: https://vkvideo.ru/video-168456727_456316581",
            "🎥 Видео 4: https://vt.tiktok.com/ZSP1ahKKD/"
        ]
    },
    "5": {
        "title": "📐 Задание 5: Простейшие уравнения",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1bTumGnJX9HN6OIWvhIGS2E1B8YljipJI/view"
        ],
        "videos": [
            "🎥 Видео 1: https://rutube.ru/video/648852dce06bb7232a6cae7134d1dda8",
            "🎥 Видео 2: https://rutube.ru/video/2dec72c46858098438d2a128ef9e4637",
            "🎥 Видео 3: https://rutube.ru/video/ecfbf34dc64993baeb70cccd10b9e3a1",
            "🎥 Видео 4: https://rutube.ru/video/a68d593da67ae8fffb02014423918119",
            "🎥 Видео 5: https://rutube.ru/video/d141c28cb081118694463480a9edcbf8",
            "🎥 Видео 6: https://yandex.ru/video/preview/13928507703848790292",
            "🎥 Видео 7: https://yandex.ru/video/preview/12934118697323829505"
        ]
    },
    "6": {
        "title": "📐 Задание 6: Планиметрия (углы, длины)",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1831XswCqJ_nq7EFZ6rbm85bopoDumre1/view"
        ],
        "videos": [
            "🎥 Видео 1: https://yandex.ru/video/preview/1700402614447305271",
            "🎥 Видео 2: https://yandex.ru/video/preview/17334508720375411362",
            "🎥 Видео 3: https://yandex.ru/video/preview/2471487969883483952"
        ]
    },
    "7": {
        "title": "📐 Задание 7: Производная и ее применение",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/16uUlrCQ5T8HIaCBq_QMQU6OkTJ1eYKg_/view"
        ],
        "videos": [
            "🎥 Видео 1: https://yandex.ru/video/preview/9778519433361531623",
            "🎥 Видео 2: https://yandex.ru/video/preview/17334508720375411362",
            "🎥 Видео 3: https://rutube.ru/video/f72831a905b8b565c254964aaa8bffd2"
        ]
    },
    "8": {
        "title": "📐 Задание 8: Стереометрия",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1Pgxn49gDYU7_apzaCMhVuar9L-35muQH/view"
        ],
        "videos": [
            "🎥 Видео 1: https://yandex.ru/video/preview/4127427546672396269",
            "🎥 Видео 2: https://yandex.ru/video/preview/16114680473322052292",
            "🎥 Видео 3: https://yandex.ru/video/preview/17208836436627407562"
        ]
    },
    "9": {
        "title": "📐 Задание 9: Вычисления и преобразования",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1k21fn0vdweQ4nw3Vdb9oFCl255an-SjO/view"
        ],
        "videos": [
            "🎥 Видео 1: https://vkvideo.ru/video-168456727_456316854",
            "🎥 Видео 2: https://vkvideo.ru/video-168456727_456316315",
            "🎥 Видео 3: https://rutube.ru/video/ce085c2d99ecf58846a7c3902add371e"
        ]
    },
    "10": {
        "title": "📐 Задание 10: Задачи с прикладным содержанием",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1NhPltnFmqE1NEHSXtlnLE2srr8z1Dndz/view"
        ],
        "videos": [
            "🎥 Видео 1: https://yandex.ru/video/preview/7396730178769684762",
            "🎥 Видео 2: https://yandex.ru/video/preview/6451367348085699175"
        ]
    },
    "11": {
        "title": "📐 Задание 11: Текстовые задачи",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1cEJ1Z9WJ4VOGj5Q-2TpnxINt38OsSXpm/view"
        ],
        "videos": [
            "🎥 Видео 1: https://vt.tiktok.com/ZSPUHguT3/",
            "🎥 Видео 2: https://rutube.ru/video/e8e3fca47f3b2f4db55baa661f91ac3f",
            "🎥 Видео 3: https://vkvideo.ru/video-212252255_456239452"
        ]
    },
    "12": {
        "title": "📐 Задание 12: Наибольшее и наименьшее значение функций",
        "theory": [
            "📚 Теория (PDF): https://drive.google.com/file/d/1CaV5Gwe9HDXB_RAV8wjem5F-eTJLGFsK/view"
        ],
        "videos": [
            "🎥 Видео 1: https://rutube.ru/video/055eb9020a6e16ddb4dce9231b06e8a9",
            "🎥 Видео 2: https://vt.tiktok.com/ZSPUHg9f9/",
            "🎥 Видео 3: https://vkvideo.ru/video-72614488_456239492"
        ]
    }
}


#функция для показа меню материалов
@bot.message_handler(func=lambda m: m.text == "📚 Материалы")
def handle_materials(message):
    """Обработка кнопки Материалы - показывает задания 1-12"""
    
    # Создаем inline-клавиатуру с заданиями 1-12
    markup = types.InlineKeyboardMarkup(row_width=4)
    
    # Кнопки для заданий 1-12
    buttons = []
    for i in range(1, 13):
        buttons.append(types.InlineKeyboardButton(
            text=f"📚 {i}", 
            callback_data=f"material_task_{i}"
        ))
    
    # Распределяем кнопки по строкам
    for i in range(0, len(buttons), 4):
        markup.row(*buttons[i:i+4])
    
    
    response = "📚 *МАТЕРИАЛЫ ДЛЯ ПОДГОТОВКИ К ЕГЭ*\n\n"
    response += "Выберите номер задания из первой части ЕГЭ (1-12):\n\n"
    response += "• 1-3: Простейшие задачи\n"
    response += "• 4: Теория вероятностей\n"
    response += "• 5: Уравнения\n"
    response += "• 6: Планиметрия\n"
    response += "• 7: Производные\n"
    response += "• 8: Стереометрия\n"
    response += "• 9: Вычисления\n"
    response += "• 10: Прикладные задачи\n"
    response += "• 11: Текстовые задачи\n"
    response += "• 12: Экстремумы функций\n\n"
    
    bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)


#функция handle_material_task
@bot.callback_query_handler(func=lambda call: call.data.startswith('material_task_'))
def handle_material_task(call):
    """Показывает материалы для выбранного задания - БЕЗ MARKDOWN"""
    task_num = call.data.split('_')[-1]
    
    if task_num in MATERIALS_DATABASE:
        material = MATERIALS_DATABASE[task_num]
        
        # Формируем сообщение БЕЗ Markdown
        response = f"{material['title']}\n\n"
        
        # Теория (PDF)
        if material.get('theory'):
            response += "📚 ТЕОРИЯ (PDF):\n"
            for item in material['theory']:
                response += f"{item}\n"
            response += "\n"
        
        # Видеоматериалы
        if material.get('videos'):
            response += "🎥 ВИДЕОУРОКИ:\n"
            for i, video in enumerate(material['videos'], 1):
                response += f"{i}. {video}\n"
        
        # Советы по подготовке
        tips = {
            "1": "• Внимательно читайте условие\n• Проверяйте единицы измерения\n• Тренируйтесь на простых задачах",
            "2": "• Изучите типы графиков\n• Практикуйтесь в чтении диаграмм\n• Учитесь быстро извлекать данные",
            "3": "• Запомните формулы площадей\n• Тренируйте пространственное мышление\n• Решайте задачи на клетках",
            "4": "• Выучите основные формулы вероятности\n• Разбирайте типовые задачи\n• Внимательно считайте варианты",
            "5": "• Повторите все типы уравнений\n• Тренируйтесь в преобразованиях\n• Проверяйте ОДЗ",
            "6": "• Знайте теоремы планиметрии\n• Учитесь видеть подобные треугольники\n• Тренируйте вычисления",
            "7": "• Понимайте геометрический смысл производной\n• Учитесь исследовать функции\n• Тренируйте нахождение экстремумов",
            "8": "• Развивайте пространственное мышление\n• Знайте формулы стереометрии\n• Учитесь разбивать сложные фигуры",
            "9": "• Тренируйте вычислительные навыки\n• Знайте свойства степеней и корней\n• Внимательно выполняйте преобразования",
            "10": "• Учитесь переводить текст в математику\n• Составляйте уравнения\n• Проверяйте логику решения",
            "11": "• Разбирайте типовые сюжеты задач\n• Учитесь составлять уравнения\n• Тренируйте проверку решения",
            "12": "• Знайте алгоритм нахождения экстремумов\n• Учитесь исследовать функции\n• Проверяйте концы отрезка"
        }
        
        if task_num in tips:
            response += f"\n💡 СОВЕТЫ ПО ПОДГОТОВКЕ:\n{tips[task_num]}"
        
        # Проверяем длину сообщения
        if len(response) > 4000:
            # Разделяем если слишком длинное
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            
            for i, part in enumerate(parts):
                if i == 0:
                    # Редактируем оригинальное сообщение
                    bot.edit_message_text(
                        part,
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode=None  
                    )
                else:
                    # Отправляем новое сообщение
                    bot.send_message(
                        call.message.chat.id,
                        part,
                        parse_mode=None  
                    )
            
            # Добавляем кнопку в последнее сообщение
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                text="⬅️ Назад к выбору задания", 
                callback_data="back_to_materials"
            ))
            
            bot.send_message(
                call.message.chat.id,
                "Выберите действие:",
                reply_markup=markup,
                parse_mode=None  
            )
            
        else:
            # Отправляем как есть
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                text="⬅️ Назад к выбору задания", 
                callback_data="back_to_materials"
            ))
            
            bot.edit_message_text(
                response,
                call.message.chat.id,
                call.message.message_id,
                parse_mode=None,  
                reply_markup=markup
            )
        
    else:
        bot.answer_callback_query(call.id, "Материалы для этого задания готовятся...")


# Обработчик для возврата к выбору материалов
@bot.callback_query_handler(func=lambda call: call.data == "back_to_materials")
def handle_back_to_materials(call):
    """Возвращает к выбору задания"""
    # Создаем новую клавиатуру
    markup = types.InlineKeyboardMarkup(row_width=4)
    
    buttons = []
    for i in range(1, 13):
        buttons.append(types.InlineKeyboardButton(
            text=f"📚 {i}", 
            callback_data=f"material_task_{i}"
        ))
    
    for i in range(0, len(buttons), 4):
        markup.row(*buttons[i:i+4])
    
    markup.add(types.InlineKeyboardButton(
        text="📚 Все материалы одним файлом", 
        callback_data="material_all"
    ))
    
    response = "📚 *МАТЕРИАЛЫ ДЛЯ ПОДГОТОВКИ К ЕГЭ*\n\n"
    response += "Выберите номер задания (1-12):"
    
    bot.edit_message_text(
        response,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )


def process_material_generation(message, task_num):
    """Генерация задачи на основе ввода пользователя и номера задания"""
    user_task = message.text
    
    try:
        # Используем генератор
        similar_tasks = generator.generate_similar_tasks(
            user_task, 
            {"task_type": "задание " + task_num, "difficulty_level": "средняя"}, 
            1
        )
        
        if similar_tasks and len(similar_tasks) > 0:
            task_text = similar_tasks[0].replace('$', '')
            response = f"🧠 *Задание {task_num}: похожая задача*\n\n"
            response += f"📝 *Ваш запрос:* {user_task}\n\n"
            response += f"🎯 *Сгенерировано:*\n{task_text}"
        else:
            response = f"🧠 Для задания {task_num} по теме '{user_task}' пока нет похожих задач."
        
        send_safe_message(message.chat.id, response)
        
    except Exception as e:
        send_safe_message(message.chat.id, f"❌ Ошибка генерации: {e}")
    finally:
        markup = show_main_menu()
        bot.send_message(message.chat.id, "✅ Готово!", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "🤖 Агентная система")
def handle_agents(message):
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(
        message.chat.id,
        "✏️ Напиши задачу для 5 агентов:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_agent_system)


def clean_solution_text(text: str) -> str:
    """
    Очищает текст решения от LaTeX-разметки, оставляя математические выражения
    в читаемом текстовом формате.
    
    Параметры:
    ----------
    text : str
        Исходный текст с LaTeX-разметкой
        
    Возвращает:
    -----------
    str
        Очищенный текст с математическими выражениями в текстовом формате
    """
    # Удаляем эмодзи и символы форматирования в начале
    text = re.sub(r'^[📋🔍✨\*]*\s*', '', text.strip())
    
    # Сначала обработаем дроби: \frac{a}{b} -> a/b
    def replace_fraction(match):
        numerator = match.group(1) if match.group(1) else ''
        denominator = match.group(2) if match.group(2) else ''
        return f"{numerator}/{denominator}"
    
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', replace_fraction, text)
    
    # Обработка индексов: S_{ABC} -> S_ABC
    text = re.sub(r'_\{([^}]+)\}', r'_\1', text)
    
    # Обработка степеней: k^{2} -> k^2
    text = re.sub(r'\^\{([^}]+)\}', r'^\1', text)
    
    # Удаляем одиночные команды LaTeX (кроме некоторых специальных)
    text = re.sub(r'\\[a-zA-Z]+\s*', '', text)
    
    # Заменяем математические символы на текстовые аналоги
    replacements = {
        r'\times': '×',
        r'\cdot': '·',
        r'\le': '≤',
        r'\ge': '≥',
        r'\neq': '≠',
        r'\approx': '≈',
        r'\pm': '±',
        r'\mp': '∓',
        r'\infty': '∞',
        r'\alpha': 'α',
        r'\beta': 'β',
        r'\gamma': 'γ',
        r'\pi': 'π',
        r'\theta': 'θ',
        r'\phi': 'φ',
        r'\lambda': 'λ',
        r'\sum': 'Σ',
        r'\prod': 'Π',
        r'\int': '∫',
        r'\sqrt': '√',
        r'\rightarrow': '→',
        r'\Rightarrow': '⇒',
        r'\leftarrow': '←',
        r'\Leftarrow': '⇐',
        r'\leftrightarrow': '↔',
        r'\Leftrightarrow': '⇔',
    }
    
    for latex, text_repl in replacements.items():
        text = text.replace(latex, text_repl)
    
    # Убираем доллары для inline-формул, оставляя содержимое
    text = re.sub(r'\$(.*?)\$', r'\1', text)
    
    # Убираем $$ для display-формул
    text = re.sub(r'\$\$(.*?)\$\$', r'\1', text, flags=re.DOTALL)
    
    # Удаляем лишние фигурные скобки (оставшиеся после обработки)
    text = re.sub(r'\{([^}]+)\}', r'\1', text)
    
    # Обработка матриц и векторов
    text = re.sub(r'\\begin\{[^}]+\}', '', text)
    text = re.sub(r'\\end\{[^}]+\}', '', text)
    
    # Удаляем разметку заголовков
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Убираем команды для скобок с размерами
    text = re.sub(r'\\left|\\right|\\big|\\Big|\\bigg|\\Bigg', '', text)
    
    # Заменяем \\ на перенос строки (для матриц)
    text = text.replace(r'\\', '\n')
    
    # Обработка пробелов и выравнивания в формулах
    text = re.sub(r'&', ' ', text)  # выравнивание в матрицах
    text = re.sub(r'~', ' ', text) 
    
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    
    # Чистим строки
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not line.isspace():
            # Убираем лишние точки в начале нумерованных списков
            line = re.sub(r'^\d+\.\s+', '', line)
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def process_agent_system(message):
    """Основной процесс работы 5 агентов"""
    user_id = message.from_user.id
    user_task = message.text
    
    wait_msg = bot.send_message(
        message.chat.id,
        "🔄 *Работают 5 агентов...*\n\n"
        "1. 🔍 Анализатор: определяет тип задачи\n"
        "2. 🧠 Память: проверяет статистику\n"
        "3. 📈 Адаптер: подбирает сложность\n"
        "4. 🎯 Генератор: создает похожие задачи\n"
        "5. 🧮 Решатель: решает задачу и дает ответ",
        parse_mode=None
    )
    
    try:
        # === 1. АНАЛИЗАТОР ===
        analysis = analyzer.analyze_task(user_task)
        
        # === 2. ПАМЯТЬ ===
        user_stats = memory.get_user_statistics(user_id)
        
        # === 3. АДАПТЕР СЛОЖНОСТИ ===
        adapted = difficulty.adjust_difficulty(user_id, analysis, user_stats)
        
        # === 4. ГЕНЕРАТОР ===
        similar_tasks = generator.generate_similar_tasks(user_task, adapted, 2)
        
        # === 5. РЕШАТЕЛЬ === (ЗАМЕНА РЕКОМЕНДАТЕЛЯ)
        solution = solver.solve_and_explain(user_task, adapted.get('task_type'))
        
        # === ЗАПИСЬ В ПАМЯТЬ ===
        memory.record_task_attempt(user_id, user_task, adapted, correct=0)
        
        # === ФОРМИРУЕМ ОТВЕТ ===
        response = "🤖 *РЕЗУЛЬТАТЫ 5 АГЕНТОВ:*\n\n"
        
        # Агент 1
        response += "🔍 *АГЕНТ 1 (Анализатор):*\n"
        response += f"• Тип: {adapted.get('task_type', '?')}\n"
        response += f"• Сложность: {adapted.get('difficulty_level', '?')}\n\n"
        
        # Агент 2
        response += "🧠 *АГЕНТ 2 (Память):*\n"
        response += f"• Всего задач: {user_stats['total_tasks'] + 1}\n"
        response += f"• Точность: {user_stats.get('accuracy', 0):.1f}%\n\n"
        
        # Агент 3
        response += "📈 *АГЕНТ 3 (Адаптер):*\n"
        if adapted.get('difficulty_adjusted'):
            response += f"• Сложность адаптирована\n\n"
        else:
            response += f"• Сложность оптимальна\n\n"
        
        # Агент 4
        response += "🎯 *АГЕНТ 4 (Генератор):*\n"
        response += f"• Похожих задач: {len(similar_tasks)}\n\n"
        
        # Агент 5
        response += "🧮 *АГЕНТ 5 (Решатель):*\n"
        if solution.get('success'):
            short_answer = solution.get('short_answer', 'Не найден')
            response += f"• Ответ: {short_answer}\n"
            response += f"• Решение: готово\n"
        else:
            response += "• Не удалось решить\n"
        
        bot.edit_message_text(response, message.chat.id, wait_msg.message_id, parse_mode=None)
        
        # === ПОКАЗЫВАЕМ РЕШЕНИЕ ===
        if solution.get('success'):
            solution_text = solution.get('full_solution', '')[:3000]
            clean_text = clean_solution_text(solution_text)
            
            response = "📋 РЕШЕНИЕ ЗАДАЧИ:\n\n"
            response += clean_text
            
            bot.send_message(message.chat.id, response, parse_mode=None)
        
        # === ПОКАЗЫВАЕМ ПОХОЖИЕ ЗАДАЧИ ===
        if similar_tasks:
            bot.send_message(message.chat.id, "🎯 *Похожие задачи:*", parse_mode=None)
            for i, task in enumerate(similar_tasks, 1):
                bot.send_message(message.chat.id, f"{i}. {task}", parse_mode=None)
        
        # Возвращаем меню
        markup = show_main_menu()
        bot.send_message(
            message.chat.id,
            "✅ *Все 5 агентов завершили работу!*",
            reply_markup=markup
        )
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)[:200]}",
            message.chat.id,
            wait_msg.message_id,
            parse_mode=None
        )
        
        markup = show_main_menu()
        bot.send_message(message.chat.id, "⚠️ Возникла ошибка", reply_markup=markup)


def edit_safe_message(chat_id, message_id, text):
    """Безопасное редактирование сообщения"""
    try:
        bot.edit_message_text(text, chat_id, message_id, parse_mode=None)
    except:
        bot.edit_message_text(safe_markdown(text), chat_id, message_id)


@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def show_stats(message):
    """Показывает детальную статистику от агента памяти - УПРОЩЕННАЯ ВЕРСИЯ"""

    user_id = message.from_user.id
    stats = memory.get_user_statistics(user_id)
    
    response = f"📊 ДЕТАЛЬНАЯ СТАТИСТИКА\n\n"
    response += f"👤 Пользователь: @{message.from_user.username or 'Аноним'}\n"
    response += f"📝 Всего задач: {stats['total_tasks']}\n"
    response += f"✅ Правильных: {stats.get('correct_answers', 0)}\n"
    response += f"❌ Ошибок: {stats.get('wrong_answers', 0)}\n"
    
    if stats.get('accuracy'):
        response += f"🎯 Точность: {stats['accuracy']:.1f}%\n"
    
    # Просто выводим слабые темы без подсчета ошибок
    if stats.get('weak_topics'):
        response += "\n📌 Слабые темы:\n"
        for topic in stats['weak_topics'][:3]:
            topic_name = topic.get('topic', 'Неизвестно')
            response += f"• {topic_name}\n"
    
    # Используем безопасную отправку
    send_safe_message(message.chat.id, response)


@bot.message_handler(func=lambda m: m.text == "🧠 Генерация")
def simple_gen(message):
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(message.chat.id, "✏️ Напиши задачу:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_simple_generation)


def handle_simple_generation(message):
    try:
        # Используем генератор напрямую
        similar_tasks = generator.generate_similar_tasks(
            message.text, 
            {"task_type": "общая", "difficulty_level": "средняя"}, 
            1
        )
        
        if similar_tasks and len(similar_tasks) > 0:
            # Убираем значки $$ из сгенерированного текста
            task_text = similar_tasks[0].replace('$', '')
            response = f"*🧠 Сгенерирована похожая задача:*\n\n{task_text}"
        else:
            response = f"*🧠 Для задачи:*\n{message.text}\n\nПока нет похожих задач в базе."
        
        send_safe_message(message.chat.id, response)
        
    except Exception as e:
        send_safe_message(message.chat.id, f"❌ Ошибка генерации: {e}")
    finally:
        markup = show_main_menu()
        bot.send_message(message.chat.id, "✅ Готово!", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "🧩 Проверить ответ")
def handle_check_answer(message):
    """Проверка ответа пользователя на задачу"""
    msg = bot.send_message(
        message.chat.id,
        "✏️ *Режим проверки ответов*\n\n"
        "1. Введите задачу\n"
        "2. Введите свой ответ\n"
        "3. Узнаете, правильно ли решили\n\n"
        "📝 *Введите задачу:*",
        parse_mode=None
    )
    bot.register_next_step_handler(msg, process_user_task_for_checking)


def process_user_task_for_checking(message):
    """Обрабатывает задачу от пользователя"""
    task_text = message.text
    
    # Сохраняем задачу во временном хранилище
    if not hasattr(bot, 'user_check_data'):
        bot.user_check_data = {}
    
    bot.user_check_data[message.from_user.id] = {
        'task': task_text,
        'time': time.time()
    }
    
    msg = bot.send_message(
        message.chat.id,
        f"📝 *Задача принята:*\n{task_text}\n\n"
        f"✏️ *Теперь введите ваш ответ:* (только число или выражение)",
        parse_mode=None
    )
    bot.register_next_step_handler(msg, process_user_answer)


def process_user_answer(message):
    """Обрабатывает ответ пользователя"""
    user_id = message.from_user.id
    user_answer = message.text.strip()
    
    # Получаем задачу
    if not hasattr(bot, 'user_check_data') or user_id not in bot.user_check_data:
        bot.send_message(message.chat.id, "❌ Ошибка: задача не найдена")
        return
    
    task_data = bot.user_check_data[user_id]
    task_text = task_data['task']
    
    # Удаляем временные данные
    del bot.user_check_data[user_id]
    
    # Показываем обработку
    wait_msg = bot.send_message(
        message.chat.id,
        "🔍 Проверяю ответ...",
        parse_mode=None
    )
    
    try:
        # Проверяем ответ с помощью агента-решателя
        is_correct, explanation, correct_answer = solver.check_user_answer(
            user_answer, task_text
        )
        
        # Записываем в память
        analysis = analyzer.analyze_task(task_text)
        
        if is_correct:
            memory.record_task_attempt(user_id, task_text, analysis, correct=1)
            memory.mark_task_correct(user_id)
            result_emoji = "✅"
        else:
            memory.record_task_attempt(user_id, task_text, analysis, correct=-1)
            memory.mark_task_wrong(user_id, reason=f"Ответ: {user_answer}")
            result_emoji = "❌"
        
        # Показываем результат
        result_msg = f"{result_emoji} *РЕЗУЛЬТАТ ПРОВЕРКИ*\n\n"
        result_msg += f"📝 Задача: {task_text}\n\n"
        result_msg += f"✏️ Ваш ответ: {user_answer}\n"
        result_msg += f"📊 Результат: {'ПРАВИЛЬНО' if is_correct else 'НЕПРАВИЛЬНО'}\n\n"
        result_msg += f"{explanation}\n\n"
        
        bot.edit_message_text(
            result_msg,
            message.chat.id,
            wait_msg.message_id,
            parse_mode=None
        )
        
        # Показываем полное решение
        solution = solver.solve_and_explain(task_text, analysis.get('task_type'))
        
        if solution.get('success'):
            solution_text = solution.get('full_solution', '')
            if solution_text:
                # Очищаем от LaTeX
                clean_text = clean_solution_text(solution_text[:3000])
                
                bot.send_message(
                    message.chat.id,
                    f"📋 РЕШЕНИЕ ЗАДАЧИ:\n\n{clean_text}",
                    parse_mode=None
                )
        
        # Показываем обновленную статистику
        stats = memory.get_user_statistics(user_id)
        stat_msg = f"\n📊 *ВАША СТАТИСТИКА:*\n"
        stat_msg += f"Всего задач: {stats['total_tasks']}\n"
        stat_msg += f"✅ Правильных: {stats.get('correct_answers', 0)}\n"
        stat_msg += f"❌ Ошибок: {stats.get('wrong_answers', 0)}\n"
        if stats.get('accuracy'):
            stat_msg += f"🎯 Точность: {stats['accuracy']:.1f}%\n"
        
        bot.send_message(message.chat.id, stat_msg, parse_mode=None)
        
        # Предлагаем похожие задачи для тренировки
        if not is_correct:
            similar_tasks = generator.generate_similar_tasks(
                task_text, analysis, 2
            )
            
            if similar_tasks:
                similar_msg = "🎯 *Похожие задачи для тренировки:*\n\n"
                for i, task in enumerate(similar_tasks, 1):
                    similar_msg += f"{i}. {task}\n\n"
                
                bot.send_message(message.chat.id, similar_msg, parse_mode=None)
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка при проверке: {str(e)[:200]}",
            message.chat.id,
            wait_msg.message_id
        )
    
    finally:
        # Возвращаем меню
        markup = show_main_menu()
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Запуск
if __name__ == '__main__':
    print("🚀 Бот запущен...")
    bot.polling(none_stop=True)