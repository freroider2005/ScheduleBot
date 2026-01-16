import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Настройки
TOKEN = "8450976313:AAHUlP-RmlhMoILJvqoEiCh9-Reygst0dXk"
URL = "http://r.sf-misis.ru/group/3831"

# Словарь сокращений для предметов
SUBJECT_SHORTENINGS = {
    "Компьютерное обеспечение специальности (Лабораторная работа)": "КОС (Лабораторная работа)",
    "Информатика Некрасова 1/205 (Лабораторная работа)": "Информатика (Лабораторная работа)",
    "Основы российской государственности (Лекция)": "ОРГ (Лекция)",
}

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def shorten_subject(subject_text):
    """Сокращает название предмета по словарю"""
    for full_name, short_name in SUBJECT_SHORTENINGS.items():
        if full_name == subject_text:
            return short_name
    return subject_text  # Возвращаем оригинал, если сокращение не найдено


def get_fresh_schedule():
    """Получает свежее расписание с сайта и парсит его"""
    try:
        response = requests.get(URL, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим контейнер с элементами расписания
        session_items_div = soup.find('div', class_='session-items')

        schedule = {}

        if session_items_div:
            # Находим все элементы расписания
            session_items = session_items_div.find_all('div', class_='session-item')

            for item in session_items:
                try:
                    # Извлекаем название предмета
                    subject_elem = item.find('div', class_='session-lesson-name')
                    if not subject_elem:
                        continue

                    subject = subject_elem.get_text(strip=True)
                    short_subject = shorten_subject(subject)

                    # Извлекаем дату и время
                    info_elem = item.find('div', class_='result-item-info')
                    if info_elem:
                        info_text = info_elem.get_text(strip=True)
                        if ', с ' in info_text:
                            date_part, time_part = info_text.split(', с ', 1)
                            date = date_part.strip()
                            time = f"с {time_part.strip()}"
                        else:
                            date = info_text
                            time = ""
                    else:
                        date = ""
                        time = ""

                    # Извлекаем аудиторию и преподавателя
                    additional_elem = item.find('div', class_='result-item-additional')
                    room = ""
                    teacher = ""

                    if additional_elem:
                        additional_text = additional_elem.get_text(strip=True)
                        if ',' in additional_text:
                            room_part, teacher_part = additional_text.split(',', 1)
                            room = room_part.strip()
                            teacher = teacher_part.strip()
                        else:
                            room = additional_text

                    # Добавляем в расписание
                    if date:
                        if date not in schedule:
                            schedule[date] = []

                        schedule[date].append({
                            'subject': short_subject,
                            'date': date,
                            'time': time,
                            'room': room,
                            'teacher': teacher
                        })

                except Exception as e:
                    logger.warning(f"Ошибка при парсинге элемента расписания: {e}")
                    continue

        return schedule

    except Exception as e:
        logger.error(f"Ошибка при получении расписания: {e}")
        return {}


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на сегодня"""
    # Получаем свежие данные
    schedule = get_fresh_schedule()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Попробуй позже.")
        return

    today_str = datetime.now().strftime('%d.%m.%Y')

    if today_str in schedule:
        day_schedule = schedule[today_str]
        # Сортируем по времени
        day_schedule_sorted = sorted(day_schedule, key=lambda x: x['time'])

        result = f"*Расписание на сегодня ({today_str})*\n\n"

        for entry in day_schedule_sorted:
            time = entry['time'].replace('с ', '').replace(' до ', '-')
            subject = entry['subject']
            room = entry.get('room', '')

            result += f" *{time}*\n"
            result += f" {subject}\n"
            if room:
                result += f" {room}\n"
            result += "\n"
    else:
        result = f"*Сегодня ({today_str})*\n\n"
        result += " Занятий нет!\n\n"
        result += "Кайфуем братья!😊"

    await update.message.reply_text(result, parse_mode='Markdown')


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на завтра"""
    # Получаем свежие данные
    schedule = get_fresh_schedule()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Попробуйте позже.")
        return

    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')

    if tomorrow_str in schedule:
        day_schedule = schedule[tomorrow_str]
        # Сортируем по времени
        day_schedule_sorted = sorted(day_schedule, key=lambda x: x['time'])

        result = f"*Расписание на завтра ({tomorrow_str})*\n\n"

        for entry in day_schedule_sorted:
            time = entry['time'].replace('с ', '').replace(' до ', '-')
            subject = entry['subject']
            room = entry.get('room', '')

            result += f" *{time}*\n"
            result += f" {subject}\n"
            if room:
                result += f" {room}\n"
            result += "\n"
    else:
        result = f"*Завтра ({tomorrow_str})*\n\n"
        result += " Занятий нет!\n\n"
        result += "Всем золотой сваги!☺️"

    await update.message.reply_text(result, parse_mode='Markdown')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение"""
    welcome_text = (
        "*Расписание для путяжки☺️☺️☺️*\n\n"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f'Ошибка: {context.error}')
    await update.message.reply_text('❌ Произошла ошибка. Попробуйте позже.')


def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Регистрируем только 3 обработчика команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("tomorrow", tomorrow))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()