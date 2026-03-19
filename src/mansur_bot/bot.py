import os
import time
import logging
import sys
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
from dotenv import load_dotenv
import re
import subprocess
from PIL import Image
import io
import requests

# Use relative import for config if run as module, otherwise fallback
try:
    from .config import REPO_ROOT, UNIVERSITY_DIR as PROJECT_UNIVERSITY_DIR, load_project_env
except ImportError:
    # Handle direct script execution or different context
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mansur_bot.config import REPO_ROOT, UNIVERSITY_DIR as PROJECT_UNIVERSITY_DIR, load_project_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load credentials
load_project_env()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not BOT_TOKEN:
    logger.critical("TELEGRAM_BOT_TOKEN not found in environment variables.")
    sys.exit(1)

# Initialize Bot & AI
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        # Download file
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save temporarily
        temp_path = f"temp_{message.voice.file_id}.ogg"
        with open(temp_path, 'wb') as f:
            f.write(downloaded_file)
            
        # Transcribe
        with open(temp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        bot.reply_to(message, f"🎙️ {transcript.text}")
        
    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        bot.reply_to(message, "Could not transcribe. Please try again.")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

client = None
if DEEPSEEK_API_KEY:
    try:
        # Load model and base_url from env
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=base_url)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
else:
    logger.warning("DEEPSEEK_API_KEY not found. AI chat features will be disabled.")

# Check for Tesseract
try:
    subprocess.run(["tesseract", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    HAS_TESSERACT = True
    logger.info("Tesseract OCR found.")
except (FileNotFoundError, subprocess.CalledProcessError):
    HAS_TESSERACT = False
    logger.warning("Tesseract OCR not found. Explanations from images will be disabled.")

# Set telebot logger
telebot.logger.setLevel(logging.INFO)

# Paths
SAFE_DIR = os.fspath(REPO_ROOT)
UNIVERSITY_DIR = os.fspath(PROJECT_UNIVERSITY_DIR)

# Global state
user_quiz_state = {}
user_chat_context = {}
user_assignment_pick_state = {}
ocr_explanation_cache = {}

def normalize_math_text(text):
    if not text:
        return text

    # Remove markdown emphasis markers so Telegram plain-text output looks clean.
    text = text.replace("**", "")

    # Strip common LaTeX wrappers and macros.
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("\\displaystyle", "")
    text = text.replace("\\,", ",")
    text = text.replace("\\quad", "  ")
    text = re.sub(r"\\text\{([^{}]+)\}", r"\1", text)

    # Piecewise formatting.
    text = text.replace("\\begin{cases}", "cases:\n")
    text = text.replace("\\end{cases}", "")
    text = text.replace("\\\\", "\n")
    text = text.replace("&", " ")

    # LaTeX math symbols (before removing backslashes).
    text = text.replace("\\infty", "∞")
    text = text.replace("\\pi", "π")
    text = text.replace("\\cdot", "·")
    text = text.replace("\\in", "∈")
    text = text.replace("\\cup", "∪")
    text = text.replace("\\cap", "∩")
    text = text.replace("\\times", "×")
    text = text.replace("\\to", "→")
    text = text.replace("\\ge", "≥")
    text = text.replace("\\le", "≤")
    text = text.replace("\\ne", "≠")

    # Fractions and radicals.
    text = text.replace("\\dfrac", "frac")
    text = text.replace("\\frac", "frac")
    text = re.sub(r"sqrt\[3\]\{([^{}]+)\}", r"∛(\1)", text)
    text = text.replace("\\sqrt", "sqrt")
    text = re.sub(r"sqrt\{([^{}]+)\}", r"√(\1)", text)
    text = re.sub(r"frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", text)

    # Normalize braces and remove remaining backslashes.
    text = text.replace("\\{", "{").replace("\\}", "}")
    text = text.replace("\\", "")

    # Convert numeric exponents safely: x^2 -> x², x^{-2} -> x⁻².
    superscript_map = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")

    def _sup(match):
        return match.group(1).translate(superscript_map)

    text = re.sub(r"\^\{(-?\d+)\}", _sup, text)
    text = re.sub(r"\^(-?\d+)\b", _sup, text)

    # Light spacing cleanup.
    text = re.sub(r"\s*=\s*", " = ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_teacher_review_explanation(image_paths):
    if not HAS_TESSERACT:
        return ""
        
    cache_key = tuple(sorted(image_paths))
    if cache_key in ocr_explanation_cache:
        return ocr_explanation_cache[cache_key]

    combined = []
    for p in image_paths:
        try:
            ocr_text = subprocess.check_output(
                ["tesseract", p, "stdout"],
                stderr=subprocess.DEVNULL,
                text=True
            )
            combined.append(ocr_text)
        except Exception as e:
            logger.warning(f"OCR failed for {p}: {e}")
            continue
    text = "\n\n".join(combined)
    if not text.strip():
        ocr_explanation_cache[cache_key] = ""
        return ""

    explanation = ""
    # Regex fixes: use single backslashes for whitespace in raw strings.
    m = re.search(r"(?is)answer\s*analysis\s*:\s*(.+)$", text)
    if m:
        explanation = m.group(1).strip()
    else:
        m = re.search(r"(?is)teacher\s*review\s*(.+)$", text)
        if m:
            explanation = m.group(1).strip()
        else:
            m = re.search(r"(?is)correct\s*answer\s*:\s*(.+)$", text)
            if m:
                explanation = m.group(1).strip()

    # Cleanup noisy lines.
    explanation = re.sub(r"(?im)^\s*my\s*answer\s*:.*$", "", explanation)
    explanation = re.sub(r"(?im)^\s*score\s*\d+.*$", "", explanation)
    explanation = re.sub(r"\n{3,}", "\n\n", explanation).strip()
    if len(explanation) > 1800:
        explanation = explanation[:1800].rsplit("\n", 1)[0].strip()

    explanation = normalize_math_text(explanation)
    ocr_explanation_cache[cache_key] = explanation
    return explanation

def is_safe_path(path):
    return os.path.abspath(path).startswith(SAFE_DIR)

def stop_chat_logic(chat_id):
    if chat_id in user_chat_context:
        user_chat_context.pop(chat_id)
        return True
    return False

def is_mcq_text(text):
    if not text:
        return False
    return all(re.search(rf"(?m)^{letter}[.)]\s*", text) for letter in ["A", "B", "C", "D"])

def parse_mcq_answer(answer):
    ans = (answer or "").strip().upper()
    if re.fullmatch(r"[A-D]", ans):
        return {"type": "single", "choices": {ans}}
    if re.fullmatch(r"[A-D]{2,4}", ans):
        return {"type": "multi", "choices": set(ans)}
    return None

def load_questions_for_subject(subject, assignment_filter=None):
    subject_dir = os.path.join(UNIVERSITY_DIR, subject)
    prep_candidates = [
        os.path.join(subject_dir, "Exam_Prep.md"),
        os.path.join(subject_dir, "Calculus_Questions.md"),
    ]
    prep_file = next((p for p in prep_candidates if os.path.exists(p)), None)
    questions = []
    if not prep_file:
        return []
    
    with open(prep_file, 'r') as f:
        content = f.read()

    assignment_markers = [(m.start(), m.group(1).strip()) for m in re.finditer(r'(?m)^##\s+(Assignment\s+\d+)\s*$', content)]
    q_headers = list(re.finditer(r'(?m)^### Question[^\n]*$', content))

    for i, qh in enumerate(q_headers):
        try:
            start = qh.start()
            end = q_headers[i + 1].start() if i + 1 < len(q_headers) else len(content)
            block = content[start:end]
            lines = block.strip().split('\n')
            header = lines[0]

            assignment_name = "General"
            for pos, name in assignment_markers:
                if pos <= start:
                    assignment_name = name
                else:
                    break
            if assignment_filter and assignment_name != assignment_filter:
                continue
            img_full_path = None
            image_paths = []
            img_nums = re.findall(r'IMG_(\d+)', header)
            for img_num in img_nums:
                image_candidates = [
                    f"IMG_{img_num}.PNG",
                    f"IMG_{img_num}.JPG",
                    f"IMG_{img_num}.jpg",
                    f"IMG_{img_num}.png",
                ]
                for img_name in image_candidates:
                    candidate_path = os.path.join(subject_dir, img_name)
                    if os.path.exists(candidate_path):
                        image_paths.append(candidate_path)
                        break
            if image_paths:
                img_full_path = image_paths[0]
            
            correct_answer = None
            explanation = ""
            if "**Explanation:**" in block:
                parts = block.split("**Explanation:**")
                explanation = parts[1].strip()
                main_part = parts[0]
            else:
                main_part = block

            # Find answer in main_part
            for line in main_part.split('\n'):
                if "**Correct Answer:**" in line:
                    correct_answer = line.split("**Correct Answer:**")[1].strip().split(' ')[0]
                    break
            
            text_lines = []
            for line in main_part.split('\n')[1:]:
                if "**Correct Answer:**" in line: break
                if line.strip(): text_lines.append(line.strip())
            
            # Detect MCQ blocks by presence of A/B/C/D options in body.
            body_text = "\n".join(text_lines)
            has_mcq_options = is_mcq_text(body_text)
            question_type = "mcq" if has_mcq_options else "study"
            default_explanation = (
                f"Correct answer: {correct_answer}" if correct_answer else "Study note."
            )
            explanation_text = normalize_math_text(explanation) if explanation else default_explanation
            questions.append({
                "id": header.strip(),
                "assignment": assignment_name,
                "image_path": img_full_path,
                "image_paths": image_paths,
                "text": normalize_math_text(body_text),
                "answer": correct_answer or "",
                "question_type": question_type,
                "pre_written_explanation": explanation_text
            })
        except: continue

    return questions

def list_assignments_for_subject(subject):
    questions = load_questions_for_subject(subject)
    seen = []
    for q in questions:
        a = q.get("assignment", "General")
        if a not in seen:
            seen.append(a)
    return seen

@bot.message_handler(commands=['quiz'])
def start_quiz_subject_select(message):
    subjects = [d for d in os.listdir(UNIVERSITY_DIR) if os.path.isdir(os.path.join(UNIVERSITY_DIR, d))]
    markup = InlineKeyboardMarkup()
    for s in subjects: markup.add(InlineKeyboardButton(f"📚 {s}", callback_data=f"subject_{s}"))
    bot.send_message(message.chat.id, "🎯 Select Subject:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("subject_"))
def handle_subject_selection(call):
    chat_id = call.message.chat.id
    subject = call.data.split('_')[1]
    assignments = list_assignments_for_subject(subject)
    if not assignments:
        bot.answer_callback_query(call.id, "❌ No questions.")
        return
    if len(assignments) <= 1:
        questions = load_questions_for_subject(subject)
        user_quiz_state[chat_id] = {
            "subject": subject,
            "assignment": assignments[0] if assignments else "General",
            "questions": questions,
            "current_index": 0,
            "answers": {}
        }
        bot.answer_callback_query(call.id, f"🚀 {subject} Quiz Started!")
        send_question(chat_id)
        return

    user_assignment_pick_state[chat_id] = {"subject": subject, "assignments": assignments}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📚 All Assignments", callback_data="assign_all"))
    for idx, a in enumerate(assignments):
        markup.add(InlineKeyboardButton(a, callback_data=f"assign_idx_{idx}"))
    bot.answer_callback_query(call.id)
    bot.send_message(chat_id, f"🎯 {subject}: Select Assignment", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "assign_all" or call.data.startswith("assign_idx_"))
def handle_assignment_selection(call):
    chat_id = call.message.chat.id
    pick = user_assignment_pick_state.get(chat_id)
    if not pick:
        bot.answer_callback_query(call.id, "Session expired.")
        return
    subject = pick["subject"]
    assignments = pick["assignments"]

    assignment = "All"
    if call.data.startswith("assign_idx_"):
        idx = int(call.data.split("_")[-1])
        if idx < 0 or idx >= len(assignments):
            bot.answer_callback_query(call.id, "Invalid selection.")
            return
        assignment = assignments[idx]

    questions = load_questions_for_subject(subject, None if assignment == "All" else assignment)
    if not questions:
        bot.answer_callback_query(call.id, "❌ No questions.")
        return
    user_quiz_state[chat_id] = {
        "subject": subject,
        "assignment": assignment,
        "questions": questions,
        "current_index": 0,
        "answers": {}
    }
    user_assignment_pick_state.pop(chat_id, None)
    bot.answer_callback_query(call.id, f"🚀 {subject} {assignment} Quiz Started!")
    send_question(chat_id)

def send_question(chat_id):
    state = user_quiz_state.get(chat_id)
    if not state: return
    idx = state["current_index"]
    if idx >= len(state["questions"]):
        correct = 0
        for i, q in enumerate(state["questions"]):
            chosen = state["answers"].get(i)
            answer_meta = parse_mcq_answer(q.get("answer", ""))
            if not chosen or not answer_meta:
                continue
            if answer_meta["type"] == "single" and chosen in answer_meta["choices"]:
                correct += 1
            elif answer_meta["type"] == "multi" and chosen in answer_meta["choices"]:
                correct += 1
        bot.send_message(chat_id, f"🏁 Quiz Finished!\nResult: {correct}/{len(state['questions'])}")
        user_quiz_state.pop(chat_id, None)
        return
    q = state["questions"][idx]
    markup = InlineKeyboardMarkup()
    # Fallback detection handles older cached question objects that may miss question_type.
    answer_meta = parse_mcq_answer(q.get("answer", ""))
    is_mcq = (
        (q.get("question_type") == "mcq" or is_mcq_text(q.get("text", "")))
    )
    if is_mcq:
        ans_row = []
        for letter in ["A", "B", "C", "D"]:
            symbol = "✅" if state["answers"].get(idx) == letter else letter
            ans_row.append(InlineKeyboardButton(symbol, callback_data=f"ans_{letter}_{idx}"))
        markup.row(*ans_row)
    nav_row = [InlineKeyboardButton("⬅️ Prev", callback_data="nav_prev"), InlineKeyboardButton("Next ➡️", callback_data="nav_next")]
    markup.row(*nav_row)
    markup.row(InlineKeyboardButton("Explain 💡", callback_data=f"expl_{idx}"), InlineKeyboardButton("Chat 🤖", callback_data=f"chat_{idx}"))
    
    assignment_label = state.get("assignment", q.get("assignment", "General"))
    q_text = (
        f"📖 {state['subject']}"
        f"\n🗂 {assignment_label}"
        f"\n❓ Question {idx + 1}/{len(state['questions'])}\n\n{q['text']}"
    )
    if not is_mcq:
        q_text += "\n\n📝 Study-only item (no multiple choice)"
    image_paths = [p for p in q.get("image_paths", []) if os.path.exists(p)]
    if image_paths:
        if len(image_paths) == 1:
            img_path = image_paths[0]
            with open(img_path, 'rb') as photo:
                if len(q_text) <= 1024:
                    bot.send_photo(chat_id, photo, caption=q_text, reply_markup=markup)
                else:
                    bot.send_photo(chat_id, photo)
                    bot.send_message(chat_id, q_text, reply_markup=markup)
        else:
            for img_path in image_paths:
                with open(img_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo)
            bot.send_message(chat_id, q_text, reply_markup=markup)
        return
    
    # Fallback for single image_path field
    if q.get("image_path") and os.path.exists(q["image_path"]):
        with open(q["image_path"], 'rb') as photo:
            if len(q_text) <= 1024:
                bot.send_photo(chat_id, photo, caption=q_text, reply_markup=markup)
            else:
                bot.send_photo(chat_id, photo)
                bot.send_message(chat_id, q_text, reply_markup=markup)
            return
    bot.send_message(chat_id, q_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("expl_"))
def explain_logic(call):
    chat_id = call.message.chat.id
    state = user_quiz_state.get(chat_id)
    if not state: return
    idx = int(call.data.split('_')[1])
    q = state["questions"][idx]
    
    # Use only pre-written explanations from the question file.
    explanation = q.get("pre_written_explanation", "")
    # If file doesn't have a real explanation yet, pull teacher review text from the source image(s).
    if not explanation or explanation.strip().lower().startswith("correct answer:"):
        image_paths = [p for p in q.get("image_paths", []) if os.path.exists(p)]
        ocr_expl = extract_teacher_review_explanation(image_paths)
        if ocr_expl:
            explanation = ocr_expl
    if not explanation:
        explanation = f"Correct answer: {q['answer']}" if q.get("answer") else "Study note."
    markup = InlineKeyboardMarkup()
    if client:
        markup.add(InlineKeyboardButton("Chat about this 💬", callback_data=f"chat_{idx}"))
    bot.send_message(chat_id, f"💡 Explanation for Q{idx+1}:\n\n{explanation}", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("chat_"))
def enter_ai_chat(call):
    if not client:
        bot.answer_callback_query(call.id, "AI Chat not configured.", show_alert=True)
        return
    chat_id = call.message.chat.id
    q = user_quiz_state[chat_id]["questions"][int(call.data.split('_')[1])]
    user_chat_context[chat_id] = {"question": q['text'], "answer": q['answer'], "history": []}
    bot.answer_callback_query(call.id, "🤖 AI Chat Mode ON")
    bot.send_message(chat_id, "🤖 Chatting about this question.\nAsk anything! Tapping /stopchat or the 'Stop' button will exit.", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⏹ Stop Chat", callback_data="stop_chat")))

@bot.callback_query_handler(func=lambda call: call.data.startswith("nav_"))
def handle_navigation(call):
    chat_id = call.message.chat.id
    state = user_quiz_state.get(chat_id)
    if not state: return
    direction = call.data.split('_')[1]
    if direction == "next" and state["current_index"] < len(state["questions"]) - 1: state["current_index"] += 1
    elif direction == "prev" and state["current_index"] > 0: state["current_index"] -= 1
    bot.answer_callback_query(call.id)
    send_question(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def check_answer(call):
    chat_id = call.message.chat.id
    state = user_quiz_state.get(chat_id)
    if not state: return
    _, letter, q_idx = call.data.split('_')
    q_idx = int(q_idx)
    state["answers"][q_idx] = letter
    q = state["questions"][q_idx]
    if not (q.get("question_type") == "mcq" or is_mcq_text(q.get("text", ""))):
        bot.answer_callback_query(call.id, "This is a study-only item.")
        return
    answer_meta = parse_mcq_answer(q.get("answer", ""))
    if answer_meta is None:
        bot.answer_callback_query(call.id, "✅ Answer saved.")
    elif answer_meta["type"] == "single":
        if letter in answer_meta["choices"]:
            bot.answer_callback_query(call.id, "✅ Correct!")
        else:
            bot.answer_callback_query(call.id, f"❌ Wrong! Correct: {q['answer']}", show_alert=True)
    else:
        correct_set = "".join(sorted(answer_meta["choices"]))
        if letter in answer_meta["choices"]:
            bot.answer_callback_query(call.id, f"✅ Included in correct set ({correct_set})")
        else:
            bot.answer_callback_query(call.id, f"❌ Wrong! Correct set: {correct_set}", show_alert=True)
    state["current_index"] += 1
    send_question(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "stop_chat")
def stop_chat_callback(call):
    if stop_chat_logic(call.message.chat.id):
        bot.answer_callback_query(call.id, "Context cleared.")
        bot.send_message(call.message.chat.id, "✅ AI Chat ended.")

@bot.message_handler(commands=['stopchat'])
def stop_chat_cmd(message):
    if stop_chat_logic(message.chat.id): bot.reply_to(message, "✅ Chat ended.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if not client:
        # If AI is disabled, just echo or ignore, but here we can tell user.
        # But for random messages, maybe just ignore to not be spammy.
        # If context exists (weird state), clear it.
        if chat_id in user_chat_context:
            user_chat_context.pop(chat_id)
            bot.reply_to(message, "AI Chat features are currently disabled (missing API key).")
        return

    if chat_id in user_chat_context:
        ctx = user_chat_context[chat_id]
        status_msg = bot.reply_to(message, "🧠 Thinking...")
        msgs = [{"role": "system", "content": f"Economics support. Q: {ctx['question']}\nAns: {ctx['answer']}\nENGLISH ONLY."}]
        for m in ctx["history"]: msgs.append(m)
        msgs.append({"role": "user", "content": message.text})
        try:
            res = client.chat.completions.create(model="deepseek-chat", messages=msgs)
            reply = normalize_math_text(res.choices[0].message.content)
            ctx["history"].extend([
                {"role": "user", "content": message.text},
                {"role": "assistant", "content": reply}
            ])
            bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=reply, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⏹ Stop Chat", callback_data="stop_chat")))
        except Exception as e:
            logger.error(f"AI Chat error: {e}")
            bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="❌ Error processing AI response.")
        return
    
    # Fallback/General chat (if desired, or maybe just ignore)
    # The original code had a general chat fallback.
    try:
        status_msg = bot.reply_to(message, "🧠 Thinking...")
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": "Assistant. ENGLISH ONLY."}, {"role": "user", "content": message.text}])
        bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=normalize_math_text(res.choices[0].message.content))
    except Exception as e:
        logger.error(f"General AI error: {e}")
        bot.reply_to(message, "❌ Error.")

def main():
    try:
        bot.remove_webhook()
    except Exception as exc:
        logging.warning("Could not remove webhook at startup: %s", exc)
    try:
        bot.set_my_commands([
            telebot.types.BotCommand("quiz", "Select subject and start quiz"),
            telebot.types.BotCommand("stopchat", "Stop AI question chat")
        ])
    except Exception as exc:
        logging.warning("Could not set Telegram commands at startup: %s", exc)
    
    retry_delay_seconds = 3
    max_retry_delay_seconds = 30
    
    logger.info("Bot started and polling...")
    
    while True:
        try:
            bot.infinity_polling(
                none_stop=True,
                interval=1,
                timeout=30,
                long_polling_timeout=25,
                allowed_updates=["message", "callback_query"],
                skip_pending=False,
                logger_level=logging.INFO
            )
            logging.error("infinity_polling returned unexpectedly. Retrying in %ss...", retry_delay_seconds)
            retry_delay_seconds = 3
        except telebot.apihelper.ApiTelegramException as exc:
            msg = str(exc)
            if "terminated by other getUpdates request" in msg:
                logging.error("Telegram conflict: another bot process is running with same token. Stop the other instance.")
            else:
                logging.error("Telegram API error: %s", msg)
        except requests.exceptions.ReadTimeout:
            logging.warning("Telegram polling read timeout. Retrying in %ss...", retry_delay_seconds)
        except requests.exceptions.RequestException as exc:
            logging.warning("Telegram polling network error: %s. Retrying in %ss...", exc, retry_delay_seconds)
        except Exception as exc:
            logging.exception("Unexpected polling error: %s. Retrying in %ss...", exc, retry_delay_seconds)
        time.sleep(retry_delay_seconds)
        retry_delay_seconds = min(retry_delay_seconds * 2, max_retry_delay_seconds)

if __name__ == "__main__":
    main()
