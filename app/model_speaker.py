# Speaker Component

from app import mongo
import pytz
from datetime import datetime, timedelta


def normalize_website(website):
    if not website:
        return None

    return str(website).upper().strip()


class Speaker:

    @staticmethod
    def data_speaker(s_id, website=None):
        try:
            website = normalize_website(website)

            query = {
                "id": s_id
            }

            # if website:
            #     query["website"] = website

            speaker = mongo.db.speaker_data.find_one(query)

            if not speaker:
                return None

            speaker_dict = {
                "id": speaker.get("id"),
                "name": speaker.get("name"),
                "email": speaker.get("email"),
                "industry": speaker.get("industry"),
                "status": speaker.get("status"),
                "bio": speaker.get("bio"),
                "contact": speaker.get("contact"),
                "photo": speaker.get("photo"),
                "history": speaker.get("history"),
                # "website": speaker.get("website")
            }

            return speaker_dict

        except Exception as e:
            return str(e)

    @staticmethod
    def view_speaker(website=None):
        speaker_list = []

        try:
            website = normalize_website(website)

            query = {}

            # if website:
            #     query["website"] = website

            speaker_data = list(
                mongo.db.speaker_data.find(query).sort("name", 1)
            )

            for speaker in speaker_data:
                speaker_dict = {
                    "id": speaker.get("id"),
                    "name": speaker.get("name"),
                    "email": speaker.get("email"),
                    "contact": speaker.get("contact"),
                    "industry": speaker.get("industry"),
                    "status": speaker.get("status"),
                    "bio": speaker.get("bio"),
                    "photo": speaker.get("photo"),
                    # "website": speaker.get("website")
                }

                speaker_list.append(speaker_dict)

        except Exception as e:
            speaker_list = [str(e)]

        return speaker_list

    @staticmethod
    def speakerdashboard_data(email, website=None):
        dashboard_list = []
        history = []
        speaker_data = None

        try:
            website = normalize_website(website)

            projections = {
                "_id": 0
            }

            speaker_query = {
                "email": email
            }

            # if website:
            #     speaker_query["website"] = website

            speaker_data = list(
                mongo.db.speaker_data.find(speaker_query, projections)
            )

            if speaker_data:
                speaker = speaker_data[0]
                history = speaker.get("history", [])
                name = speaker.get("name")
            else:
                return dashboard_list, history

            for topic in history:
                webinar_query = {
                    "topic": topic
                }

                if website:
                    webinar_query["website"] = website

                webinar_data = list(
                    mongo.db.webinar_data.find(webinar_query)
                )

                if webinar_data:
                    webinar = webinar_data[0]

                    if webinar.get("speaker") == name:
                        date = str(webinar.get("date_time"))
                        timezone = webinar.get("timeZone")
                        urlreturn = handle_timezone(date, timezone)

                        urlLive = " "

                        if urlreturn is True:
                            urlLive = webinar.get("urlLive")

                        webinar_dict = {
                            "webinar": topic,
                            "date": webinar.get("date"),
                            "time": webinar.get("time"),
                            "timeZone": timezone,
                            "duration": webinar.get("duration"),
                            "sessionLive": webinar.get("sessionLive"),
                            "urlLive": urlLive,
                            "website": webinar.get("website")
                        }

                        dashboard_list.append(webinar_dict)

        except Exception as e:
            dashboard_list = [str(e)]

        return dashboard_list, history


def handle_timezone(webinar_datetime_str, timeZone):
    try:
        webinar_datetime = datetime.fromisoformat(
            webinar_datetime_str.replace("Z", "+00:00")
        )
    except ValueError:
        return True

    time_zones = {
        'PST': 'America/Los_Angeles',
        'EST': 'America/New_York',
        'IST': 'Asia/Kolkata',
        'UTC': 'UTC',
        'CST': 'America/Chicago'
    }

    if timeZone not in time_zones:
        return True

    webinar_tz = pytz.timezone(time_zones[timeZone])
    webinar_datetime = webinar_datetime.astimezone(webinar_tz)

    webinar_datetime_utc = webinar_datetime.astimezone(pytz.UTC)

    current_datetime_utc = datetime.now(pytz.UTC).replace(
        second=0,
        microsecond=0
    )

    time_difference = webinar_datetime_utc - current_datetime_utc

    is_within_next_48_hours = (
        timedelta(0) < time_difference < timedelta(hours=48)
    )

    return is_within_next_48_hours
