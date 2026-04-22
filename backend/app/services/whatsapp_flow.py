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

# ── In-memory stage store ─────────────────────────────────────────────────────
_flow_state: dict[str, dict] = {}
SESSION_TIMEOUT_S = 30 * 60

CALENDLY_URL = "https://calendly.com/gignaati/discovery-call"


def _meet_link_reply(name: str, service: str) -> str:
    """Direct Calendly link — shown after 3 QA answers or on meeting keywords."""
    cfg = BOT_CONFIG
    return (
        f"📅 Ready to connect, *{name or 'there'}*?\n\n"
        f"Book a free 15-min discovery call here:\n"
        f"{CALENDLY_URL}\n\n"
        f"📞 {cfg['phone_india']} (India) | {cfg['phone_uae']} (UAE)\n"
        f"📧 {cfg['email']}\n\n"
        f"You can keep chatting below anytime! 😊"
    )


def _convinced_meet_reply(name: str, service: str) -> str:
    cfg = BOT_CONFIG
    return (
        f"Great, *{name or 'there'}*! 🎉\n\n"
        f"📅 Book your slot here:\n"
        f"{CALENDLY_URL}\n\n"
        f"Our team will confirm within 2 business hours.\n"
        f"📞 {cfg['phone_india']} (India) | {cfg['phone_uae']} (UAE)\n"
        f"📧 yogesh@gignaati.com\n\n"
        f"You can keep chatting below anytime! 😊"
    )


# ── Hardcoded CEO / Founder answer ───────────────────────────────────────────
_CEO_ANSWER = (
    "*Yogesh Huja* is the *Founder, CEO & AI Architect* of *Swaran Soft*.\n\n"
    "He holds a *B.Sc (Hons) in Mathematics* and brings over *25 years* of enterprise IT experience, "
    "with a focused mission on building *India's Edge AI ecosystem*. "
)

_CEO_KEYWORDS = [
    "ceo", "founder", "who is the ceo", "who is ceo", "who is founder",
    "who founded", "who started", "who built", "who created",
    "head of", "chief executive",
    "who runs", "who leads", "leadership", "who is the owner", "owner",
    "who is behind", "who is in charge", "managing director",
    "kaun hai ceo", "kaun hai founder", "company ka head", "company ka malik",
    "malik kaun hai", "ceo kaun hai", "founder kaun hai", "head kaun hai",
    "company ke founder", "company ke ceo", "swaran soft ka ceo",
    "swaran soft ke founder", "swaran soft ka founder", "swaran soft ceo",
    "swaran soft founder", "company ki leadership", "top person",
    "in charge", "who is leading", "who is running",
]

# ── Meeting keywords — direct Calendly link, no yes/no ───────────────────────
_MEETING_KEYWORDS = [
    "book", "booking", "schedule", "meeting", "meet", "call",
    "appointment", "slot", "calendly", "demo call", "discovery call",
    "book a call", "book a meeting", "book meeting", "book now", "schedule a call",
    "schedule meeting", "i want to meet", "want to connect",
    "connect with team", "talk to team", "speak with team",
    "book karna", "meeting chahiye", "call chahiye", "slot chahiye",
    "appointment chahiye", "baat karni hai", "milna hai","give me a demo","give me demo",
    "i need demo","i need a demo", "need demo","book a demo","book demo",
]

# ── Greeting keywords ─────────────────────────────────────────────────────────
_GREETING_WORDS = {
    "hi", "hii", "hiii", "hiiii", "hello", "hey", "helo", "heyy",
    "hola", "namaste", "namaskar", "yo", "sup", "greetings", "heyyy",
}

# ── Words that are NOT a name ─────────────────────────────────────────────────
_NOT_A_NAME = {
    "ok", "okay", "yes", "no", "sure", "thanks", "bye", "good", "nice",
    "great", "cool", "fine", "alright", "yep", "nope", "noted", "perfect",
    "awesome", "got it", "sounds good",
}

# ── Name-related keywords ─────────────────────────────────────────────────────
_NAME_KEYWORDS = {
    "my name", "mera naam", "what is my name", "mere naam",
    "what's my name", "what my name", "tell me my name", "aap jaante ho mera naam",
    "do you know my name", "naam kya hai", "naam bata",
}


def _is_ceo_question(text: str) -> bool:
    tl = text.strip().lower()
    return any(kw in tl for kw in _CEO_KEYWORDS)


def _is_greeting(text: str) -> bool:
    return text.strip().lower() in _GREETING_WORDS


def _is_asking_name(text: str) -> bool:
    tl = text.strip().lower()
    return any(kw in tl for kw in _NAME_KEYWORDS)


def _is_meeting_request(text: str) -> bool:
    """Check if user is asking to book/schedule a meeting — direct Calendly link."""
    tl = text.strip().lower()
    return any(kw in tl for kw in _MEETING_KEYWORDS)


def get_state(phone: str) -> dict:
    now_ts = time.time()
    if phone not in _flow_state:
        _flow_state[phone] = {
            "stage":        "new",
            "service":      None,
            "attempts":     0,
            "msg_count":    0,
            "meet_offered": False,
            "qa_count":     0,
            "append_meet_link": False,
            "last_seen_ts": now_ts,
        }
    else:
        last_seen_ts = _flow_state[phone].get("last_seen_ts", now_ts)
        if (now_ts - last_seen_ts) > SESSION_TIMEOUT_S:
            # Inactivity timeout: keep known name, reset conversation stage.
            state = _reset_stage(phone)
            state["last_seen_ts"] = now_ts
            return state

    _flow_state[phone]["name"] = get_name(phone)
    _flow_state[phone]["last_seen_ts"] = now_ts
    return _flow_state[phone]


def _reset_stage(phone: str) -> dict:
    name = get_name(phone)
    _flow_state[phone] = {
        "stage":            "menu" if name else "awaiting_name",
        "service":          None,
        "attempts":         0,
        "msg_count":        0,
        "meet_offered":     False,
        "qa_count":         0,
        "append_meet_link": False,
        "name":             name,
        "last_seen_ts":     time.time(),
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
    return (
        f"Hi! Welcome to *{CFG['company_name']}* \n\n"
        f"We are happy to help you!\n\n"
        f"To get started, please tell me your *name*."
    )


def _welcome_new(name: str) -> str:
    return (
        f"Great to meet you, *{name}*! \n\n"
        f"Welcome to *{CFG['company_name']}* — {CFG['tagline']}.\n\n"
        f"What would you like to know? Feel free to ask any question! "
    )


def _welcome_back(name: str) -> str:
    return f"Hi *{name}*! Welcome back to *Swaran Soft*. What can I help you with today?"


def _action_menu(name: str, service: str) -> str:
    actions = _actions_text()
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} chose *{service}*. Write 1-2 sentences confirming their choice "
        f"and asking what they'd like to do.\n"
        f"Then append EXACTLY:\n\n{actions}\n\n(Reply with a number)\n\n"
        f"Use *bold*. Output the message only.",
        f"Great choice, *{name}*! You selected *{service}*. 🎯\n\n"
        f"{actions}\n\n(Reply with a number)"
    )


def _demo_reply(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants a demo for *{service}*.\n"
        f"Write {MAX_S} sentences: confirm enthusiasm, give booking link "
        f"{CFG['website']}/contact, phones {CFG['phone_india']} (India) / "
        f"{CFG['phone_uae']} (UAE), say team confirms in 24 hours.\n"
        f"Use *bold*. Output the message only.",
        f"📅 Let's book a demo for *{service}*, *{name}*!\n\n"
        f"👉 {CFG['website']}/contact\n"
        f"📞 {CFG['phone_india']} (India) | {CFG['phone_uae']} (UAE)\n\n"
        f"Team confirms within 24 hours. ✅\n\n"
    )


def _expert_reply(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants to talk to an expert about *{service}*.\n"
        f"Write {MAX_S} sentences: say expert will reach out, give "
        f"email yogesh@gignaati.com, phones {CFG['phone_india']} / {CFG['phone_uae']}, "
        f"mention 2-business-hour response.\n"
        f"Use *bold*. Output the message only.",
        f"💬 A *{service}* expert will reach you soon, *{name}*!\n\n"
        f"📧 yogesh@gignaati.com\n"
        f"📞 {CFG['phone_india']} (India) | {CFG['phone_uae']} (UAE)\n\n"
        f"Response within *2 business hours*. 🚀\n\n"
    )


def _website_reply(name: str, service: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"{name} wants to visit the website for *{service}*.\n"
        f"Write {MAX_S} sentences pointing to {CFG['website']} and inviting questions.\n"
        f"Use *bold*. Output the message only.",
        f"🌐 Learn all about *{service}* here, *{name}*:\n\n"
        f"👉 *{CFG['website']}*\n\n"
        f"Feel free to ask me anything! 😊\n\n"
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
        f"Use *bold*. Output the message only.",
        f"✅ Got it, *{name}*! A Google Meet invite for *{service}* will be sent to "
        f"*{email}* within *2 business hours*.\n\n"
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
        f"End: (Type menu anytime to go back)\n"
        f"Use *bold*. Output the message only.",
        f"❓ Go ahead, *{name}* — what would you like to know about *{service}*? 👇\n\n"
        f"(Type menu anytime to go back)"
    )


def _anything_else(name: str) -> str:
    return _llm(
        f"You are Swaran AI for {CFG['company_name']}.\n"
        f"You just finished helping {name}.\n"
        f"Write 1 sentence asking if there's anything else you can help with. "
        f"Mention they can type menu to see services.\n"
        f"Use *bold*. Output the message only.",
        f"Is there anything else I can help you with, *{name}*? "
        f"Type menu to see our services again. 😊"
    )


def _name_not_caught() -> str:
    return (
        f"I didn't catch that 😊 Could you please type just your *name*?\n\n"
        f"For example: *Ajay* or *Priya*"
    )


# ── Convinced detection ───────────────────────────────────────────────────────

_INTEREST_PHRASES = [
    "i'm interested", "im interested", "we are interested", "we're interested",
    "get in touch", "contact you", "reach out",
    "i want to buy", "i want to purchase", "ready to start",
]

_CONVINCED_PHRASES = [
    "let's do it", "lets do it", "sounds good", "i want",
    "i'd like", "id like", "please proceed", "go ahead", "yes please",
    "definitely", "absolutely", "for sure", "count me in", "sign me up",
    "schedule", "when can we", "how do i start", "let's start",
    "let's connect", "lets connect", "great idea", "love to", "would love",
    "yes i want", "yes we need", "i need this", "we need this", "i need it", "we need it",
]


def _is_convinced(text: str, msg_count: int) -> bool:
    tl = text.strip().lower()
    if any(phrase in tl for phrase in _INTEREST_PHRASES):
        return True
    if msg_count < 6:
        return False
    return any(phrase in tl for phrase in _CONVINCED_PHRASES)


def clean_response(text: str) -> str:
    unwanted = ["(Type menu to explore other services)"],
    "Here's a 2-sentence answer"
    for u in unwanted:
        text = text.replace(u, "")
    return text


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

    # ── CEO intercept ─────────────────────────────────────────────────────────
    if _is_ceo_question(t):
        delay = random.randint(15, 20)
        print(f"[CEO INTERCEPT] Sleeping {delay}s")
        time.sleep(delay)
        return _CEO_ANSWER

    # ── Meeting keyword intercept — direct Calendly link, no yes/no ──────────
    if _is_meeting_request(tl):
        print(f"[MEETING INTERCEPT] '{tl}'")
        state["meet_offered"] = True
        service = state.get("service") or "our services"
        return _meet_link_reply(name or "there", service)

    # ── "What is my name?" intercept ──────────────────────────────────────────
    if _is_asking_name(tl):
        if name:
            return f"Your name is *{name}*! "
        else:
            return f"i don’t know your name yet. Could you tell me your name?"

    # ── Greeting intercept ────────────────────────────────────────────────────
    if _is_greeting(tl):
        print(f"[GREETING] '{tl}'")
        if name:
            state["stage"] = "menu"
            return _welcome_back(name)
        else:
            state["stage"] = "awaiting_name"
            return _ask_name()

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
    reset_cmds = {"menu", "main menu", "restart", "reset", "start over", "back"}
    if tl in reset_cmds:
        state = _reset_stage(phone)
        return _welcome_back(state["name"]) if state.get("name") else _ask_name()

    # ── Stage: new ────────────────────────────────────────────────────────────
    if state["stage"] == "new":
        if name:
            if len(t.split()) >= 3 or _match_service(tl):
                state["stage"] = "qa"
                return None
            state["stage"] = "menu"
            return _welcome_back(name)
        if len(t.split()) >= 3 or _match_service(tl):
            state["stage"] = "qa"
            return None
        state["stage"] = "awaiting_name"
        return _ask_name()


    #     if state["stage"] == "new":
    # if name:
    #     state["stage"] = "menu"
    #     return _welcome_back(name)

    # # 👇 IMPORTANT: Always ask name first
    # if len(t.split()) >= 3:
    #     state["pending_question"] = t   # save question
    # state["stage"] = "awaiting_name"
    # return _ask_name()

    # ── Stage: awaiting_name ──────────────────────────────────────────────────
    if state["stage"] == "awaiting_name":
        if name:
            pending = state.pop("pending_question", None)
            if pending and len(pending.split()) >= 3:
                state["stage"] = "qa"
                return None
            state["stage"] = "menu"
            return _welcome_back(name)
        if len(t.split()) <= 2 and not t.isdigit() and tl not in _NOT_A_NAME and tl not in _GREETING_WORDS:
            captured = t.title()
            save_name(phone, captured)
            state["name"]  = captured
            state["stage"] = "menu"
            print(f"[NAME SAVED] phone={phone} name={captured}")
            pending = state.pop("pending_question", None)
            if pending and len(pending.split()) >= 3:
                state["stage"] = "qa"
                state["pending_answer"] = pending
                return _welcome_new(captured)
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
            return None
        if len(t.split()) >= 3:
            state["stage"] = "qa"
            return None
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
        display   = name or "there"
        service   = state.get("service", f"{CFG['company_name']} services")
        meet_link = CALENDLY_URL
        if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", t) and len(t.split()) >= 3:
            state["stage"] = "qa"
            return None
        if re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", t):
            slot      = find_next_free_slot()
            slot_str  = ""
            cal_link  = None
            if slot:
                cal_link = create_meet_event(display, t, service, slot)
                slot_str = format_slot(slot)
            if cal_link and slot_str:
                state["stage"] = "done"
                return _llm(
                    f"You are Swaran AI for {CFG['company_name']}.\n"
                    f"{display} confirmed their email {t} for a Google Meet about *{service}*.\n"
                    f"The meet is booked for {slot_str}.\n"
                    f"Write 2-3 sentences: confirm the event is created, share the Meet link "
                    f"{cal_link}, mention a calendar invite was emailed to {t}.\n"
                    f"Use *bold*. Output the message only.",
                    f"✅ All set, *{display}*! Your Google Meet for *{service}* is confirmed.\n\n"
                    f"📅 *{slot_str}*\n"
                    f"🔗 Join here: {cal_link}\n\n"
                    f"A calendar invite has been sent to *{t}*. See you there! \n\n"
                )
            else:
                state["stage"] = "done"
                return (
                    f"✅ Got it, *{display}*!\n\n"
                    f"🔗 Book here: {meet_link}\n\n"
                    f"Our team will reach you at:\n"
                    f"📞 {CFG['phone_india']} (India) | {CFG['phone_uae']} (UAE)\n"
                    f"📧 ajay.yadav@gignaati.com\n\n"
                )
        return _meet_invalid_email(display)

    # ── Stage: qa — fall through to RAG ──────────────────────────────────────
    if state["stage"] == "qa":
        state["qa_count"] = state.get("qa_count", 0) + 1
        # After 3 QA answers → set flag to append direct Calendly link (no yes/no prompt)
        if state["qa_count"] % 3 == 0:
            state["append_meet_link"] = True
        return None

    # ── Stage: done ───────────────────────────────────────────────────────────
    if state["stage"] == "done":
        display = name or "there"
        short_words = {
            "yes", "no", "ok", "okay", "sure", "yep", "nope", "great",
            "thanks", "thank you", "got it", "noted", "alright", "perfect",
            "awesome", "sounds good", "cool", "fine", "good", "nice",
            "hii", "hi", "hello", "hey"
        }
        if tl in short_words or len(t) <= 6:
            state["stage"] = "menu"
            return _welcome_back(display)
        if len(t) > 12 and not t.isdigit():
            state["stage"] = "qa"
            return None
        return _anything_else(display)

    return None
