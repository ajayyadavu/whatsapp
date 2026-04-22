# app/services/calendar_service.py
# Google Calendar: check free slots → create Meet event → return join link

import os
import datetime
from typing import Optional

# ── Lazy import so server starts even without google libs installed ──────────
def _get_calendar_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "google_credentials.json")
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    credentials = service_account.Credentials.from_service_account_file(
        creds_file, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Working hours: 9 AM – 6 PM IST (UTC+5:30)
WORK_START_HOUR = 9
WORK_END_HOUR   = 18
SLOT_MINUTES    = 15   # ← 15-minute discovery call


def _ist_offset() -> datetime.timezone:
    return datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def find_next_free_slot() -> Optional[datetime.datetime]:
    """
    Returns the next free IST datetime slot starting from now.
    Checks the next 7 days, skips weekends and busy blocks.
    Returns None if no slot found or on any error.
    """
    try:
        service = _get_calendar_service()
        ist     = _ist_offset()
        now_ist = datetime.datetime.now(tz=ist)

        # Start from next whole hour
        candidate = now_ist.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)

        for _ in range(7 * 24):  # check up to 7 days, hour-by-hour
            if candidate.weekday() >= 5:           # skip weekends (Sat=5, Sun=6)
                candidate += datetime.timedelta(hours=1)
                continue
            if not (WORK_START_HOUR <= candidate.hour < WORK_END_HOUR):
                # Jump to next working day 9 AM if outside work hours
                candidate = (candidate + datetime.timedelta(days=1)).replace(
                    hour=WORK_START_HOUR, minute=0, second=0, microsecond=0
                )
                continue

            slot_end = candidate + datetime.timedelta(minutes=SLOT_MINUTES)

            # Query freeBusy for this slot
            body = {
                "timeMin": candidate.isoformat(),
                "timeMax": slot_end.isoformat(),
                "timeZone": "Asia/Kolkata",
                "items": [{"id": CALENDAR_ID}],
            }
            result    = service.freebusy().query(body=body).execute()
            busy_list = result.get("calendars", {}).get(CALENDAR_ID, {}).get("busy", [])

            if not busy_list:
                return candidate   # ✅ free slot found

            # Slot is busy — try the next hour
            candidate += datetime.timedelta(hours=1)

        return None  # no slot found in 7 days

    except Exception as e:
        print(f"[calendar_service] Error finding slot: {e}")
        return None


def create_meet_event(
    name: str,
    email: str,
    service_name: str,
    slot: datetime.datetime,
) -> Optional[str]:
    """
    Creates a Google Calendar event with a Meet link at `slot` for `email`.
    Returns the Google Meet join URL, or None on failure.
    """
    try:
        calendar_service = _get_calendar_service()
        slot_end = slot + datetime.timedelta(minutes=SLOT_MINUTES)

        host_email = os.getenv("HOST_EMAIL", "yogesh@gignaati.com")

        event = {
            "summary": f"Swaran Soft – {service_name} Discovery Call with {name}",
            "description": (
                f"15-minute discovery call booked via Swaran AI.\n"
                f"Service of interest: {service_name}\n"
                f"Contact: {name} | {email}"
            ),
            "start": {
                "dateTime": slot.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": slot_end.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "attendees": [
                {"email": email},
                {"email": host_email},
            ],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"swaran-{email}-{int(slot.timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        created = calendar_service.events().insert(
            calendarId=CALENDAR_ID,
            body=event,
            conferenceDataVersion=1,
            sendUpdates="all",   # sends email invite to attendees
        ).execute()

        # Extract Meet join link
        meet_link = (
            created.get("conferenceData", {})
                   .get("entryPoints", [{}])[0]
                   .get("uri")
        )
        return meet_link

    except Exception as e:
        print(f"[calendar_service] Error creating event: {e}")
        return None


def format_slot(slot: datetime.datetime) -> str:
    """Human-readable IST slot string e.g. 'Tuesday, 8 Apr at 3:00 PM IST'"""
    return slot.strftime("%A, %-d %b at %-I:%M %p IST")
