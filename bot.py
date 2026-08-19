import os
import sqlite3
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

DB_NAME = "lms.db"


# ============================================================
# CONTENT — EDIT THIS SECTION TO ADD/CHANGE COURSES & TOPICS
# ============================================================
# Each course has an id, name (Arabic), and a list of topics.
# Each topic has:
#   title        -> Arabic title shown in the topic list
#   explanation  -> the professional explanation text (Arabic,
#                   with English terms where useful)
#   video_url    -> YouTube or Facebook video link (or None)
#   audio_url    -> link to an audio file if you have one (or None)
#
# Topics are shown IN ORDER. In Phase 2 we will lock topic [n+1]
# until the student's assignment for topic [n] is approved.
# ============================================================

COURSES = [
    {
        "id": "arabic_lang",
        "name": "دورة في اللغة العربية",
        "topics": [
            {
                "title": "المقدمة: أهمية اللغة العربية",
                "explanation": (
                    "بسم الله الرحمن الرحيم\n\n"
                    "اللغة العربية هي لغة القرآن الكريم، وهي المفتاح "
                    "لفهم الدين فهماً صحيحاً. في هذه الدورة سنتدرج معكم "
                    "من الأساسيات حتى تتمكنوا بإذن الله من قراءة النصوص "
                    "العربية وفهمها.\n\n"
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-1",
                "audio_url": None,
            },
            {
                "title": "الحروف الهجائية ومخارجها",
                "explanation": (
                    "في هذا الدرس نتعرف على الحروف العربية الثمانية "
                    "والعشرين ومخارج كل حرف.\n\n"
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-2",
                "audio_url": None,
            },
        ],
    },
    {
        "id": "nahw",
        "name": "دورة النحو العربي",
        "topics": [
            {
                "title": "تعريف النحو وأهميته",
                "explanation": (
                    "علم النحو هو العلم الذي يبحث في أحوال أواخر الكلمات "
                    "من حيث الإعراب والبناء.\n\n"
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-3",
                "audio_url": None,
            },
        ],
    },
    {
        "id": "fiqh",
        "name": "دورة الفقه",
        "topics": [
            {
                "title": "مقدمة في أصول الفقه",
                "explanation": (
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-4",
                "audio_url": None,
            },
        ],
    },
    {
        "id": "tafsir",
        "name": "دورة في علم التفسير",
        "topics": [
            {
                "title": "تعريف علم التفسير",
                "explanation": (
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-5",
                "audio_url": None,
            },
        ],
    },
    {
        "id": "mawarith",
        "name": "دورة في علم المواريث",
        "topics": [
            {
                "title": "مقدمة في علم الفرائض",
                "explanation": (
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-6",
                "audio_url": None,
            },
        ],
    },
    {
        "id": "mutoon",
        "name": "دورة في شرح المتون",
        "topics": [
            {
                "title": "منهجية شرح المتون",
                "explanation": (
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-7",
                "audio_url": None,
            },
        ],
    },
    {
        "id": "usul_qawaid",
        "name": "دورة في الأصول والقواعد",
        "topics": [
            {
                "title": "تعريف الأصول والقواعد الفقهية",
                "explanation": (
                    "(Placeholder text — استبدل هذا بشرحك الخاص)"
                ),
                "video_url": "https://youtube.com/your-video-link-8",
                "audio_url": None,
            },
        ],
    },
]


def get_course(course_id):
    for c in COURSES:
        if c["id"] == course_id:
            return c
    return None


# ============================================================
# DATABASE (tracks students only, for now — content lives above)
# ============================================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            first_seen TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def register_student_seen(user_id, name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO students (user_id, name, first_seen)
        VALUES (?, ?, ?)
    """, (user_id, name, datetime.now().isoformat()))

    conn.commit()
    conn.close()


# ============================================================
# MENUS
# ============================================================

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 الدورات المتاحة", callback_data="courses")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def courses_menu():
    keyboard = []
    for course in COURSES:
        keyboard.append([
            InlineKeyboardButton(course["name"], callback_data=f"course_{course['id']}")
        ])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


def topics_menu(course):
    keyboard = []
    for index, topic in enumerate(course["topics"]):
        keyboard.append([
            InlineKeyboardButton(
                f"{index + 1}. {topic['title']}",
                callback_data=f"topic_{course['id']}_{index}"
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع للدورات", callback_data="courses")])
    return InlineKeyboardMarkup(keyboard)


def topic_view_menu(course, index):
    keyboard = []
    topic = course["topics"][index]

    if topic.get("video_url"):
        keyboard.append([InlineKeyboardButton("🎥 مشاهدة الفيديو", url=topic["video_url"])])

    if topic.get("audio_url"):
        keyboard.append([InlineKeyboardButton("🎧 الاستماع للصوت", url=topic["audio_url"])])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ رجوع لمواضيع الدورة",
            callback_data=f"course_{course['id']}"
        )
    ])
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_student_seen(user.id, user.full_name)

    text = (
        "السلام عليكم ورحمة الله وبركاته 🌹\n\n"
        "مرحباً بكم في\n"
        "🎓 *أكاديمية دار التوحيد*\n\n"
        "منصة الدروس العلمية عبر تيليجرام.\n\n"
        "اختر من القائمة:"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.message.edit_text(
            "🎓 *أكاديمية دار التوحيد*\n\nاختر من القائمة:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    elif data == "help":
        await query.message.edit_text(
            "❓ *المساعدة*\n\n"
            "1️⃣ اختر «الدورات المتاحة».\n"
            "2️⃣ اختر الدورة التي تريد دراستها.\n"
            "3️⃣ اختر الموضوع الذي تريد تعلمه.\n"
            "4️⃣ اقرأ الشرح، ثم شاهد الفيديو أو استمع للصوت.\n\n"
            "بارك الله فيكم.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    elif data == "courses":
        await query.message.edit_text(
            "📚 *الدورات المتاحة:*\n\nاختر الدورة:",
            parse_mode="Markdown",
            reply_markup=courses_menu()
        )

    elif data.startswith("course_"):
        course_id = data.split("_", 1)[1]
        course = get_course(course_id)

        if not course:
            await query.message.edit_text("⚠️ لم يتم العثور على الدورة.")
            return

        await query.message.edit_text(
            f"📚 *{course['name']}*\n\nاختر الموضوع:",
            parse_mode="Markdown",
            reply_markup=topics_menu(course)
        )

    elif data.startswith("topic_"):
        _, course_id, index_str = data.split("_", 2)
        index = int(index_str)
        course = get_course(course_id)

        if not course or index >= len(course["topics"]):
            await query.message.edit_text("⚠️ لم يتم العثور على الموضوع.")
            return

        topic = course["topics"][index]

        text = f"📖 *{topic['title']}*\n\n{topic['explanation']}"

        await query.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=topic_view_menu(course, index)
        )


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Daar Tawheed Academy LMS Bot (Phase 1) is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
