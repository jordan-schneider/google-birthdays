import os.path
import pickle
import subprocess

import arrow  # type: ignore
import fire  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def auth():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return creds


def send_reminder(event, period: str) -> None:
    person = event["summary"][: len("'s birthday") + 1]
    birthday = event["start"].get("dateTime", event["start"].get("date"))
    print(f"Sending message to {person} for {birthday}")

    subject = f"It's {person}'s birthday {period}, {birthday}."

    if period == "today":
        content = "You should call them!"
    elif period == "tomorrow":
        content = "Send them a late gift!"
    elif period == "next week":
        content = "Send them a gift!"
    elif period == "next month":
        content = "Figure out what to give them!"
    else:
        raise ValueError(
            f'Invalid period "{period}". Must be "today", "tomorrow", "next week", or "next month".'
        )

    dst = "jordan.jack.schneider@gmail.com"

    subprocess.run(f'echo "{content}" | mail -s "{subject}" {dst}', shell=True, check=True)


def main():
    creds = auth()
    service = build("calendar", "v3", credentials=creds)

    now = arrow.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    events_result = (
        service.events()
        .list(
            calendarId="addressbook#contacts@group.v.calendar.google.com",
            timeMin=today,
            timeMax=today.shift(weeks=4, days=1),
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    for event in events:
        # print(event)
        date = arrow.get(event["start"].get("date"))
        if arrow.get(date) == today:
            send_reminder(event, "today")
        elif date == today.shift(days=1):
            send_reminder(event, "tomorrow")
        elif date == today.shift(weeks=1):
            send_reminder(event, "next week")
        elif date == today.shift(weeks=4):
            send_reminder(event, "next month")


if __name__ == "__main__":
    fire.Fire(main)
