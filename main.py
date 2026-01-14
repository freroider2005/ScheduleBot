import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Настройки
TOKEN = "7986423255:AAENVKeAv68TnOC2wnZF7l3PUmuWpt_SjYs"  # Получите у @BotFather
URL = "http://r.sf-misis.ru/group/3831"

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def get_fresh_schedule():
    """Получает свежее расписание с сайта"""
    try:
        response = requests.get(URL, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        session_items_div = soup.find('div', class_='session-items')

        if session_items_div:
            return session_items_div.get_text(strip=False, separator='\n')
        return ""
    except Exception as e:
        logger.error(f"Ошибка при получении расписания: {e}")
        return ""


def parse_schedule(text):
    """Парсит текст расписания и группирует по дням"""
    if not text:
        return {}

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    schedule = {}
    current_entry = {}

    i = 0
    while i < len(lines):
        line = lines[i]

        if '(' in line and ')' in line and line.endswith(')'):
            if current_entry and 'subject' in current_entry:
                date = current_entry['date']
                if date not in schedule:
                    schedule[date] = []
                schedule[date].append(current_entry.copy())

            current_entry = {'subject': line}

            if i + 1 < len(lines):
                i += 1
                date_time_line = lines[i]

                if ',' in date_time_line and 'с ' in date_time_line:
                    date_part, time_part = date_time_line.split(', с ')
                    current_entry['date'] = date_part.strip()
                    current_entry['time'] = f"с {time_part.strip()}"

            if i + 1 < len(lines):
                i += 1
                room_teacher = lines[i]

                if ',' in room_teacher:
                    room, teacher = room_teacher.split(',', 1)
                    current_entry['room'] = room.strip()
                    current_entry['teacher'] = teacher.strip()
                else:
                    current_entry['room'] = room_teacher
                    current_entry['teacher'] = ""

        i += 1

    if current_entry and 'subject' in current_entry:
        date = current_entry['date']
        if date not in schedule:
            schedule[date] = []
        schedule[date].append(current_entry.copy())

    return schedule


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на сегодня"""
    await update.message.reply_text("🔄 Загрузка расписания на сегодня...")

    # Получаем свежие данные
    text = get_fresh_schedule()
    if not text:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Попробуй позже.")
        return

    schedule = parse_schedule(text)
    today_str = datetime.now().strftime('%d.%m.%Y')

    # Форматируем результат
    if today_str in schedule:
        day_schedule = sorted(schedule[today_str], key=lambda x: x['time'])

        result = f"*Расписание на сегодня ({today_str})*\n\n"

        for entry in day_schedule:
            time = entry['time'].replace('с ', '').replace(' до ', '-')
            subject = entry['subject']
            room = entry.get('room', '')

            result += f" *{time}*\n"
            result += f" {subject}\n"
            if room:
                result += f" {room}\n"
            result += "\n"
    else:
        result = f" *Сегодня ({today_str})*\n\n"
        result += " Занятий нет!\n\n"
        result += "Кайфуем братья!😊"

    await update.message.reply_text(result, parse_mode='Markdown')


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на завтра"""
    await update.message.reply_text("🔄 Загрузка расписания на завтра...")

    # Получаем свежие данные
    text = get_fresh_schedule()
    if not text:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Попробуйте позже.")
        return

    schedule = parse_schedule(text)
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')

    # Форматируем результат
    if tomorrow_str in schedule:
        day_schedule = sorted(schedule[tomorrow_str], key=lambda x: x['time'])

        result = f"*Расписание на завтра ({tomorrow_str})*\n\n"

        for entry in day_schedule:
            time = entry['time'].replace('с ', '').replace(' до ', '-')
            subject = entry['subject']
            room = entry.get('room', '')

            result += f" *{time}*\n"
            result += f" {subject}\n"
            if room:
                result += f" {room}\n"
            result += "\n"
    else:
        result = f" *Завтра ({tomorrow_str})*\n\n"
        result += "✅ Занятий нет!\n\n"
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