# Webinar Component

from app import mongo, normalize_website
from datetime import datetime


class Webinar:

    @staticmethod
    def data_webinar(w_id, website=None):
        try:
            website = normalize_website(website)

            query = {
                # "id": w_id
                "webinar_url": w_id
            }

            if website:
                query["website"] = website

            webinar = mongo.db.webinar_data.find_one(query)

            # Optional fallback for old frontend using webinar_url
            if not webinar:
                fallback_query = {
                    "webinar_url": w_id
                }

                if website:
                    fallback_query["website"] = website

                webinar = mongo.db.webinar_data.find_one(fallback_query)

            if not webinar:
                return None

            speaker = webinar.get("speaker")

            speaker_query = {
                "name": speaker
            }

            # if website:
            #     speaker_query["website"] = website

            speaker_detail = mongo.db.speaker_data.find_one(
                speaker_query,
                {
                    "_id": 0,
                    "photo": 1,
                    "bio":1,
                    "id": 1
                }
            )

            if not speaker_detail:
                speaker_detail = {}

            webinar_data_dict = {
                "id": webinar.get("id"),
                "topic": webinar.get("topic"),
                "industry": webinar.get("industry"),
                "speaker": speaker,
                "speaker_id": speaker_detail.get("id"),
                "speaker_image": speaker_detail.get("photo"),
                "speaker_bio":speaker_detail.get("bio"),
                "website": webinar.get("website"),

                "date": webinar.get("date_time"),
                "time": webinar.get("time"),
                "timeZone": webinar.get("timeZone"),
                "duration": webinar.get("duration"),
                "category": webinar.get("category"),

                "sessionLive": webinar.get("sessionLive"),
                "priceLive": webinar.get("priceLive"),
                "urlLive": webinar.get("urlLive"),

                "sessionRecording": webinar.get("sessionRecording"),
                "priceRecording": webinar.get("priceRecording"),
                "urlRecording": webinar.get("urlRecording"),

                "sessionDigitalDownload": webinar.get("sessionDigitalDownload"),
                "priceDigitalDownload": webinar.get("priceDigitalDownload"),
                "urlDigitalDownload": webinar.get("urlDigitalDownload"),

                "sessionTranscript": webinar.get("sessionTranscript"),
                "priceTranscript": webinar.get("priceTranscript"),
                "urlTranscript": webinar.get("urlTranscript"),

                "status": webinar.get("status"),
                "webinar_url": webinar.get("webinar_url"),
                "description": webinar.get("description"),
            }

            return webinar_data_dict

        except Exception as e:
            return str(e)

    @staticmethod
    def view_webinar(website=None):
        webinar_list = []

        try:
            website = normalize_website(website)

            current_date = datetime.now()

            future_query = {
                "status": "Active",
                "date_time": {
                    "$gte": current_date
                }
            }

            past_query = {
                "status": "Active",
                "date_time": {
                    "$lt": current_date
                }
            }

            if website:
                future_query["website"] = website
                past_query["website"] = website

            future_webinars = list(
                mongo.db.webinar_data.find(future_query).sort("date_time", 1)
            )

            past_webinars = list(
                mongo.db.webinar_data.find(past_query).sort("date_time", -1)
            )

            webinar_data = future_webinars + past_webinars

            for webinar in webinar_data:
                speaker = webinar.get("speaker")

                speaker_query = {
                    "name": speaker
                }

                # if website:
                #     speaker_query["website"] = website

                speaker_photo = mongo.db.speaker_data.find_one(
                    speaker_query,
                    {
                        "_id": 0,
                        "photo": 1
                    }
                )

                if not speaker_photo:
                    speaker_photo = {}

                webinar_dict = {
                    "id": webinar.get("id"),
                    "topic": webinar.get("topic"),
                    "industry": webinar.get("industry"),
                    "speaker": speaker,
                    "speaker_image": speaker_photo.get("photo"),
                    "website": webinar.get("website"),
                    "date": webinar.get("date"),
                    "time": webinar.get("time"),
                    "timeZone": webinar.get("timeZone"),
                    "duration": webinar.get("duration"),
                    "category": webinar.get("category"),

                    "sessionLive": webinar.get("sessionLive"),
                    "priceLive": webinar.get("priceLive"),
                    "urlLive": webinar.get("urlLive"),

                    "sessionRecording": webinar.get("sessionRecording"),
                    "priceRecording": webinar.get("priceRecording"),
                    "urlRecording": webinar.get("urlRecording"),

                    "sessionDigitalDownload": webinar.get("sessionDigitalDownload"),
                    "priceDigitalDownload": webinar.get("priceDigitalDownload"),
                    "urlDigitalDownload": webinar.get("urlDigitalDownload"),

                    "sessionTranscript": webinar.get("sessionTranscript"),
                    "priceTranscript": webinar.get("priceTranscript"),
                    "urlTranscript": webinar.get("urlTranscript"),

                    "status": webinar.get("status"),
                    "webinar_url": webinar.get("webinar_url"),
                    "description": webinar.get("description"),
                }

                webinar_list.append(webinar_dict)

        except Exception:
            webinar_list = []

        return webinar_list
