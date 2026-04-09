# app/services/whatsapp_flow.py

import re
import time
import random
from typing import Optional
from app.core.bot_config import BOT_CONFIG
from app.services.whatsapp_user_service import get_name, save_name
from app.services.llm_service import call_llama
from app.services.calendar_service import find_next_free_slot, create_meet_event, format_slot

CFG      = BOT_CONFIG
SERVICES = {str(i + 1): svc["name"] for i, svc in enumerate(CFG["services"])}
MAX_S    = CFG["max_sentences"]

# ── Hardcoded instant greeting (no LLM, fast response) ───────────────────────
GREETING_MSG = "Hi, welcome to Swarnsoft AI. We are happy to help you."

# ── In-memory stage store ─────────────────────────────────────────────────────
_flow_state: dict[str, dict] = {}

# ── Hardcoded CEO / Founder answer ───────────────────────────────────────────
_CEO_ANSWER = (
    " *Yogesh Huja* is the *Founder, CEO & AI Architect* of *Swaran Soft*.\n\n"
    "He holds a *B.Sc (Hons) in Mathematics* and brings over *25 years* of enterprise IT experience, "
    "with a focused mission on building *India's Edge AI ecosystem*. "
)

_CEO_KEYWORDS = [
    "ceo", "founder", "who is the ceo", "who is ceo", "who is founder",
    "who founded", "who started", "who built", "who created",
    "head of", "chief executive", "yogesh", "yogesh huja",
    "who runs", "who leads", "leadership", "who is the owner", "owner",
    "who is behind", "who is in charge", "managing director",
    "kaun hai ceo", "kaun hai founder", "company ka head", "company ka malik",
    "malik kaun hai", "ceo kaun hai", "founder kaun hai", "head kaun hai",
    "company ke founder", "company ke ceo", "swaran soft ka ceo",
    "swaran soft ke founder", "swaran soft ka founder", "swaran soft ceo",
    "swaran soft founder", "company ki leadership", "top person",
    "in charge", "who is leading", "who is running",
]

# ── Greeting keywords ─────────────────────────────────────────────────────────
_GREETING_WORDS = {
    "hi", "hii", "hiii", "hiiii", "hello", "hey", "helo", "heyy",
    "hola", "namaste", "namaskar", "yo", "sup", "greetings", "heyyy",
}

# ── Words that are clearly NOT a person's name ───────────────────────────────
_NOT_A_NAME = {
    "ok", "okay", "yes", "no", "sure", "thanks", "bye", "good", "nice",
    "great", "cool", "fine", "alright", "yep", "nope", "noted", "perfect",
    "awesome", "got it", "sounds good",
}


def _is_ceo_question(text: str) -> bool:
    tl = text.strip().lower()
    return any(kw in tl for kw in _CEO_KEYWORDS)


def _is_greeting(text: str) -> bool:
    return text.strip().lower() in _GREETING_WORDS


def _is_real_question(text: str) -> bool:
    """True if message looks like an actual question (3+ words), not a name."""
    return len(text.strip().split()) >= 3


def get_state(phone: str) -> dict:
    if phone not in _flow_state:
        _flow_state[phone] = {"stage": "new", "service": None, "attempts": 0, "msg_count": 0, "meet_offered": False}
    _flow_state[phone]["name"] = get_name(phone)
    return _flow_state[phone]


def _reset_stage(phone: str) -> dict:
    name = get_name(phone)
    _flow_state[phone] = {
        "stage":        "menu" if name else "awaiting_name",
        "service":      None,
        "attempts":     0,
        "msg_count":    0,
        "meet_offered": False,
        "name":         name,
    }
    return _flow_state[phone]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _services_text() -> str:
    return "\n".join(
        f"{s['emoji']} *{i+1}.* {s['name']}"
        for i, s in enumerate(CFG["services"])
    )


def _actions_text() -> str:
    return "\n".join(
        f"{a['emoji']} *{a['key']}.* {a['label']}"
        for a in CFG["actions"]
    )


def _llm(prompt: str, fallback: str) -> str:
    import threading
    result_holder = [None]

    def _call():
        try:
            r = call_llama(prompt, temperature=0.55, num_predict=120)
            if r and len(r.strip()) > 15:
                result_holder[0] = r.strip()
        except Exception:
            pass

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=4)
    return result_holder[0] if result_holder[0] else fallback


# ── LLM prompt builders ───────────────────────────────────────────────────────

def _ask_name() -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']} ({CFG['website']}) on WhatsApp.\n"
        f"A new user just messaged. Write a warm greeting in {MAX_S} sentences:\n"
        f"- Welcome them to {CFG['company_name']}\n"
        f"- Introduce yourself as Swaran AI\n"
        f"- Ask for their name\n"
        f"Use *bold* for key words. Output the message only.",
        f"Hello! 😊 Welcome to *{CFG['company_name']}*. "
        f"I'm Swaran AI. Could you please tell me your *name*?"
    )


def _welcome_new(name: str) -> str:
    services = _services_text()
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"User's name: {name}. First time chatting.\n"
        f"Write a {MAX_S}-sentence welcome that greets {name} by name and says "
        f"{CFG['company_name']} is {CFG['tagline']}.\n"
        f"Then append EXACTLY this list (do not change it):\n\n"
        f"{services}\n\n_(Reply with the number)_\n\n"
        f"Use *bold* for key words. Output the message only.",
        f"Great to meet you, *{name}*! Welcome to *{CFG['company_name']}* 🎉\n\n"
        f"{services}\n\n_(Reply with the number)_"
    )


def _welcome_back(name: str) -> str:
    # ✅ Instant hardcoded — no LLM
    return GREETING_MSG


def _action_menu(name: str, service: str) -> str:
    actions = _actions_text()
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} chose *{service}*. Write 1-2 sentences confirming their choice "
        f"and asking what they'd like to do.\n"
        f"Then append EXACTLY:\n\n{actions}\n\n_(Reply with a number)_\n\n"
        f"Use *bold*. Output the message only.",
        f"Great choice, *{name}*! You selected *{service}*. 🎯\n\n"
        f"{actions}\n\n_(Reply with a number)_"
    )


def _demo_reply(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants a demo for *{service}*.\n"
        f"Write {MAX_S} sentences: confirm enthusiasm, give booking link "
        f"{CFG['website']}/contact, phones {CFG['phone_india']} (India) / "
        f"{CFG['phone_uae']} (UAE), say team confirms in 24 hours.\n"
        f"End: _(Type *menu* to explore other services)_\n"
        f"Use *bold*. Output the message only.",
        f"📅 Let's book a demo for *{service}*, *{name}*!\n\n"
        f"👉 {CFG['website']}/contact\n"
        f"📞 {CFG['phone_india']} (India) | {CFG['phone_uae']} (UAE)\n\n"
        f"Team confirms within 24 hours. ✅\n\n"
        f"_(Type *menu* to explore other services)_"
    )


def _expert_reply(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants to talk to an expert about *{service}*.\n"
        f"Write {MAX_S} sentences: say expert will reach out, give "
        f"email {CFG['email']}, phones {CFG['phone_india']} / {CFG['phone_uae']}, "
        f"mention 2-business-hour response.\n"
        f"End: _(Type *menu* to explore other services)_\n"
        f"Use *bold*. Output the message only.",
        f"💬 A *{service}* expert will reach you soon, *{name}*!\n\n"
        f"📧 {CFG['email']}\n"
        f"📞 {CFG['phone_india']} (India) | {CFG['phone_uae']} (UAE)\n\n"
        f"Response within *2 business hours*. 🚀\n\n"
        f"_(Type *menu* to explore other services)_"
    )


def _website_reply(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants to visit the website for *{service}*.\n"
        f"Write {MAX_S} sentences pointing to {CFG['website']} and inviting questions.\n"
        f"End: _(Type *menu* to explore other services)_\n"
        f"Use *bold*. Output the message only.",
        f"🌐 Learn all about *{service}* here, *{name}*:\n\n"
        f"👉 *{CFG['website']}*\n\n"
        f"Feel free to ask me anything! 😊\n\n"
        f"_(Type *menu* to explore other services)_"
    )


def _meet_invite(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants to book a Google Meet for *{service}*.\n"
        f"Write 1-2 warm sentences saying you'd love to connect over a Google Meet "
        f"and ask them to share their email so the team can send the invite.\n"
        f"Use *bold*. Output the message only.",
        f"📹 We'd love to meet you, *{name}*! Please share your *email address* "
        f"and we'll send you a Google Meet invite for *{service}* shortly. ✅"
    )


def _meet_confirm(name: str, service: str, email: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} has shared their email: {email} for a Google Meet about *{service}*.\n"
        f"Write 2 sentences: confirm the email was received, say the team will send "
        f"a Google Meet invite within 2 business hours, and thank them.\n"
        f"End: _(Type *menu* to explore other services)_\n"
        f"Use *bold*. Output the message only.",
        f"✅ Got it, *{name}*! A Google Meet invite for *{service}* will be sent to "
        f"*{email}* within *2 business hours*.\n\n"
        f"_(Type *menu* to explore other services)_"
    )


def _meet_invalid_email(name: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"The user {name} typed something that doesn't look like an email address.\n"
        f"Write 1 friendly sentence asking them to type a valid *email address*.\n"
        f"Use *bold*. Output the message only.",
        f"That doesn't look like a valid email, *{name}*. Could you please type your *email address*? 😊"
    )


def _qa_invite(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants to ask a question about *{service}*.\n"
        f"Write 1-2 sentences inviting them to type their question.\n"
        f"End: _(Type *menu* anytime to go back)_\n"
        f"Use *bold*. Output the message only.",
        f"❓ Go ahead, *{name}* — what would you like to know about *{service}*? 👇\n\n"
        f"_(Type *menu* anytime to go back)_"
    )


def _anything_else(name: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"You just finished helping {name}.\n"
        f"Write 1 sentence asking if there's anything else you can help with. "
        f"Mention they can type *menu* to see services.\n"
        f"Use *bold*. Output the message only.",
        f"Is there anything else I can help you with, *{name}*? "
        f"Type *menu* to see our services again. 😊"
    )


def _name_not_caught() -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']} on WhatsApp.\n"
        f"You asked for the user's name but couldn't understand their reply.\n"
        f"Write 1 friendly sentence asking them to type just their name.\n"
        f"Use *bold*. Output the message only.",
        f"I didn't catch that 😊 Could you please type just your *name*?"
    )


# ── Convinced detection ───────────────────────────────────────────────────────

_INTEREST_PHRASES = [
    "interested", "i want to know more", "tell me more", "want more info",
    "more details", "want to know more", "want more", "i want more",
    "know more about this", "know more", "learn more", "sounds interesting",
    "i'm interested", "im interested", "we are interested", "we're interested",
    "get in touch", "contact you", "reach out", "more info",
]

_CONVINCED_PHRASES = [
    "let's do it", "lets do it", "sounds good", "i want",
    "i'd like", "id like", "please proceed", "go ahead", "yes please",
    "definitely", "absolutely", "for sure", "count me in", "sign me up",
    "book", "schedule", "when can we", "how do i start", "let's start",
    "let's connect", "lets connect", "great idea", "love to", "would love",
    "yes i want", "yes we need",
]


def _is_convinced(text: str, msg_count: int) -> bool:
    tl = text.strip().lower()
    if any(phrase in tl for phrase in _INTEREST_PHRASES):
        return True
    if msg_count < 6:
        return False
    return any(phrase in tl for phrase in _CONVINCED_PHRASES)


def _convinced_meet_reply(name: str, service: str) -> str:
    slot = find_next_free_slot()
    if slot is None:
        return (
            f"🎉 Wonderful, *{name}*! Let's get a call scheduled for *{service}*. "
            f"Please share your *email address* and we'll send you a Google Meet invite. ✅"
        )
    slot_str = format_slot(slot)
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} has shown clear interest in *{service}*.\n"
        f"A Google Meet slot is available on {slot_str}.\n"
        f"Write 2-3 warm sentences:\n"
        f"- Congratulate them on deciding to move forward\n"
        f"- Share this exact slot: *{slot_str}*\n"
        f"- Ask them to reply with their *email address* to confirm the invite\n"
        f"Use *bold*. Output the message only.",
        f"🎉 Great to hear, *{name}*! Let's lock in a Google Meet for *{service}*.\n\n"
        f"📅 Next available slot: *{slot_str}*\n\n"
        f"Please reply with your *email address* to confirm the invite. ✅"
    )


# ── Matching helpers ──────────────────────────────────────────────────────────

def _match_service(text: str) -> Optional[str]:
    t = text.strip().lower()
    if t in SERVICES:
        return SERVICES[t]
    for val in SERVICES.values():
        if val.lower() in t:
            return val
    keyword_map = {
        "ai":         "AI Consulting",
        "consult":    "AI Consulting",
        "consulting": "AI Consulting",
        "app":        "App Development",
        "mobile":     "App Development",
        "develop":    "App Development",
        "security":   "Digital Security",
        "cyber":      "Digital Security",
        "secure":     "Digital Security",
        "marketing":  "Digital Marketing",
        "digital":    "Digital Marketing",
        "seo":        "Digital Marketing",
        "sap":        "SAP & Machine Learning",
        "machine":    "SAP & Machine Learning",
        "ml":         "SAP & Machine Learning",
        "learning":   "SAP & Machine Learning",
    }
    for keyword, service in keyword_map.items():
        if keyword in t:
            return service
    return None


def _match_action(text: str) -> Optional[str]:
    t = text.strip().lower()
    for action in CFG["actions"]:
        if t == action["key"] or t in action["label"].lower():
            return action["key"]
    return None


# ── Main flow controller ──────────────────────────────────────────────────────

def handle_flow(phone: str, text: str) -> Optional[str]:
    state = get_state(phone)
    t     = text.strip()
    tl    = t.lower()
    name  = state.get("name")

    # ── CEO intercept (highest priority) ─────────────────────────────────────
    if _is_ceo_question(t):
        delay = random.randint(15, 20)
        print(f"[CEO INTERCEPT] Sleeping {delay}s")
        time.sleep(delay)
        return _CEO_ANSWER

    # ── Greeting intercept — instant hardcoded, no LLM ───────────────────────
    if _is_greeting(tl):
        print(f"[GREETING] '{tl}' → instant reply")
        return GREETING_MSG

    # ── ✅ Real question intercept — skip flow, go straight to RAG ────────────
    # If user sends 3+ words AND it's not a reset command, go to RAG immediately.
    # This prevents "tell me about ai consulting" from getting stuck in flow.
    reset_cmds = {"menu", "main menu", "restart", "reset", "start over", "back"}
    if _is_real_question(t) and tl not in reset_cmds:
        print(f"[QUESTION INTERCEPT] '{t}' → straight to RAG")
        state["stage"] = "qa"
        state["msg_count"] = state.get("msg_count", 0) + 1
        # Try to detect service from the question and save it
        detected_service = _match_service(tl)
        if detected_service:
            state["service"] = detected_service
        return None  # → RAG pipeline

    # ── Increment message counter ─────────────────────────────────────────────
    state["msg_count"] = state.get("msg_count", 0) + 1

    # ── Convinced check ───────────────────────────────────────────────────────
    if (
        not state.get("meet_offered")
        and state["stage"] not in {"new", "awaiting_name", "awaiting_meet_email"}
        and _is_convinced(t, state["msg_count"])
    ):
        state["meet_offered"] = True
        state["stage"]        = "awaiting_convinced_email"
        service = state.get("service") or "our services"
        return _convinced_meet_reply(name or "there", service)

    # ── Reset commands ────────────────────────────────────────────────────────
    if tl in reset_cmds:
        state = _reset_stage(phone)
        return _welcome_back(state["name"]) if state.get("name") else _ask_name()

    # ── Stage: new ────────────────────────────────────────────────────────────
    if state["stage"] == "new":
        if name:
            state["stage"] = "menu"
            return _welcome_back(name)
        state["stage"] = "awaiting_name"
        return _ask_name()

    # ── Stage: awaiting_name ──────────────────────────────────────────────────
    if state["stage"] == "awaiting_name":
        if name:
            state["stage"] = "menu"
            return _welcome_back(name)
        # 1-2 word input that isn't a junk word → treat as name
        if len(t.split()) <= 2 and not t.isdigit() and tl not in _NOT_A_NAME:
            captured = t.title()
            save_name(phone, captured)
            state["name"]  = captured
            state["stage"] = "menu"
            return _welcome_new(captured)
        state["attempts"] += 1
        return _name_not_caught()

    # ── Stage: menu ───────────────────────────────────────────────────────────
    if state["stage"] == "menu":
        display = name or "there"
        service = _match_service(tl)
        if service:
            state["service"]  = service
            state["stage"]    = "qa"
            state["attempts"] = 0
            return None  # → RAG
        state["attempts"] += 1
        return f"Koi bhi sawaal puchein, *{display}*! 😊"

    # ── Stage: awaiting_action ────────────────────────────────────────────────
    if state["stage"] == "awaiting_action":
        display = name or "there"
        service = state.get("service", f"{CFG['company_name']} services")
        action  = _match_action(tl)
        if action == "1":
            state["stage"] = "done"
            return _demo_reply(display, service)
        if action == "2":
            state["stage"] = "done"
            return _expert_reply(display, service)
        if action == "3":
            state["stage"] = "done"
            return _website_reply(display, service)
        if action == "4":
            state["stage"] = "qa"
            return _qa_invite(display, service)
        if action == "5":
            state["stage"] = "awaiting_meet_email"
            return _meet_invite(display, service)
        state["attempts"] += 1
        return _action_menu(display, service)

    # ── Stage: awaiting_meet_email ────────────────────────────────────────────
    if state["stage"] == "awaiting_meet_email":
        display = name or "there"
        service = state.get("service", f"{CFG['company_name']} services")
        if re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", t):
            state["stage"] = "done"
            return _meet_confirm(display, service, t)
        return _meet_invalid_email(display)

    # ── Stage: awaiting_convinced_email ──────────────────────────────────────
    if state["stage"] == "awaiting_convinced_email":
        display = name or "there"
        service = state.get("service", f"{CFG['company_name']} services")
        if re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", t):
            slot = find_next_free_slot()
            meet_link = None
            slot_str  = ""
            if slot:
                meet_link = create_meet_event(display, t, service, slot)
                slot_str  = format_slot(slot)
            if meet_link and slot_str:
                state["stage"] = "done"
                return _llm(
                    f"You are Swaran AI for {CFG['company_name']}.\n"
                    f"{display} confirmed their email {t} for a Google Meet about *{service}*.\n"
                    f"The meet is booked for {slot_str}.\n"
                    f"Write 2-3 sentences: confirm the event is created, share the Meet link "
                    f"{meet_link}, mention a calendar invite was emailed to {t}.\n"
                    f"End: _(Type *menu* to explore other services)_\n"
                    f"Use *bold*. Output the message only.",
                    f"✅ All set, *{display}*! Your Google Meet for *{service}* is confirmed.\n\n"
                    f"📅 *{slot_str}*\n"
                    f"🔗 Join here: {meet_link}\n\n"
                    f"A calendar invite has been sent to *{t}*. See you there! 🎉\n\n"
                    f"_(Type *menu* to explore other services)_"
                )
            else:
                state["stage"] = "done"
                return _meet_confirm(display, service, t)
        return _meet_invalid_email(display)

    # ── Stage: qa — fall through to RAG ──────────────────────────────────────
    if state["stage"] == "qa":
        return None

    # ── Stage: done ───────────────────────────────────────────────────────────
    if state["stage"] == "done":
        display = name or "there"
        short_words = {
            "yes", "no", "ok", "okay", "sure", "yep", "nope", "great",
            "thanks", "thank you", "got it", "noted", "alright", "perfect",
            "awesome", "sounds good", "cool", "fine", "good", "nice",
        }
        if tl in short_words or len(t) <= 6:
            state["stage"] = "menu"
            return GREETING_MSG
        return _anything_else(display)

    return None
