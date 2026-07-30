# Order Component
from app import mongo
from datetime import datetime, timedelta
import pytz

class Order():

    @staticmethod
    def update_corporateorder(order_data):

        try:
            mongo.db.corporate_order.insert_one(order_data)
            return ({"success": True, "message": "order placed successfully"}),201
        except Exception as e:
            return ({"success": False, "message": str(e)}), 403
    
    @staticmethod
    def update_order(order_data):
        return_data = order_data.copy()
        try:
            # When completing a purchase, update the existing pending document
            # so there is one canonical order record instead of two.
            invoice_number = order_data.get("invoice_number", "")
            if (order_data.get("paymentstatus") == "purchased"
                    and invoice_number
                    and invoice_number.startswith("PT")):
                pending_id = invoice_number[len("PT"):]
                fields = {k: v for k, v in order_data.items() if k not in ("_id", "id")}
                result = mongo.db.order_data.update_one(
                    {"id": pending_id, "paymentstatus": "Pending"},
                    {"$set": fields}
                )
                if result.matched_count > 0:
                    updated = mongo.db.order_data.find_one({"id": pending_id}, {"_id": 0})
                    return ({"success": True, "message": updated or return_data}), 201

            mongo.db.order_data.insert_one(order_data)
            return ({"success": True, "message": return_data}), 201
        except Exception as e:
            return ({"success": False, "message": str(e)}), 403
    @staticmethod
    def update_newsletterorder(order_data):

        try:
            mongo.db.newsletter_order.insert_one(order_data)
            return ({"success": True, "message": "order placed successfully"}),201
        except Exception as e:
            return ({"success": False, "message": str(e)}), 403
    @staticmethod
    def find_newsletterorder(customeremail, website=None):

        dashboard_list = []
        newsletter_purchased = []
        newsletter_pending = []
        try:
            query = {"customeremail": customeremail}
            if website:
                query["website"] = website
            orders = list(mongo.db.newsletter_order.find(query))

            user_query = {"email": customeremail}
            if website:
                user_query["website"] = website
            user_data = list(mongo.db.user_data.find(user_query))
            if user_data:
                user = user_data[0]
                newsletter_purchased = user.get("newsletter_purchased", [])
                newsletter_pending = user.get("newsletter_pending", [])
                
                
                for order in orders:
                    
                    o_id = order.get("id")
                    topic = order.get("topic")
                    customeremail = order.get("customeremail")
                    paymentstatus = order.get("paymentstatus")
                    customername = order.get("customername")
                    document = order.get("document")

                    if paymentstatus == "purchased":
                        projection ={"_id":0}
                        newsletter_data  = list(mongo.db.newsletter_data.find({"topic":topic}, projection))
                        if newsletter_data:
                            newsletter = newsletter_data[0]
                            w_id = newsletter.get("id")
                            topic = newsletter.get("topic"),
                            published_date = newsletter.get("published_date"),
                            newsletter_doc = newsletter.get("document")
                            
                            
                            
                            dashboard_dict = {
                            "o_id":o_id,
                            "w_id":w_id,
                            "newsletter" : topic[0],
                            "document" : document,
                            "published_date":published_date[0],
                            "newsletter_doc":newsletter_doc    
                            }

                            dashboard_list.append(dashboard_dict)

                        
        except Exception as e:

                dashboard_list=[str(e)]

        return dashboard_list, newsletter_purchased, newsletter_pending
    @staticmethod
    def find_order(customeremail, website=None):

        dashboard_list = []
        history_pending = []
        history_purchased = []
        try:
            query = {"customeremail": customeremail}
            if website:
                query["website"] = website
            orders = list(mongo.db.order_data.find(query))

            user_query = {"email": customeremail}
            if website:
                user_query["website"] = website
            user_data = list(mongo.db.user_data.find(user_query))
            if user_data:
                user = user_data[0]
                history_pending = user.get("history_pending", [])
                history_purchased = user.get("history_purchased", [])
                
                
                for order in orders:

                    o_id = order.get("id")
                    topic = order.get("topic")
                    customeremail = order.get("customeremail")
                    paymentstatus = order.get("paymentstatus")
                    customername = order.get("customername")
                    document = order.get("document")
                    order_type = order.get("order_type")
                    total_attendee = order.get("total_attendee")

                    if paymentstatus == "purchased":
                        projection = {"_id": 0}
                        webinars_in_order = order.get("webinars") or []

                        if webinars_in_order and webinars_in_order[0].get("trainingOptions") is not None:
                            # New-format order: one dashboard card per webinar
                            for w in webinars_in_order:
                                w_topic = w.get("topic", "")
                                if not w_topic:
                                    continue
                                option_names = {
                                    opt.get("optionName", "")
                                    for opt in w.get("trainingOptions", [])
                                }
                                live_url = recording_url = digitaldownload_url = transcript_url = None
                                w_data_list = list(mongo.db.webinar_data.find({"topic": w_topic}, projection))
                                if w_data_list:
                                    wd = w_data_list[0]
                                    date_time = str(wd.get("date_time", ""))
                                    timeZone = wd.get("timeZone")
                                    if "Live Session" in option_names and handle_timezone(date_time, timeZone):
                                        live_url = wd.get("urlLive")
                                    if "Recording" in option_names:
                                        recording_url = wd.get("urlRecording")
                                    if "Digital Download" in option_names:
                                        digitaldownload_url = wd.get("urlDigitalDownload")
                                    if "Transcript PDF" in option_names:
                                        transcript_url = wd.get("urlTranscript")
                                    dashboard_dict = {
                                        "o_id": o_id,
                                        "w_id": wd.get("id"),
                                        "customername": customername,
                                        "webinar": wd.get("topic", w_topic),
                                        "speaker": wd.get("speaker"),
                                        "date": wd.get("date"),
                                        "time": wd.get("time"),
                                        "timeZone": timeZone,
                                        "duration": wd.get("duration"),
                                        "live_url": live_url,
                                        "recording_url": recording_url,
                                        "digitaldownload_url": digitaldownload_url,
                                        "transcript_url": transcript_url,
                                        "document": document,
                                        "order_type": order_type,
                                        "total_attendee": total_attendee
                                    }
                                else:
                                    # Webinar not yet in webinar_data; show basic entry
                                    dashboard_dict = {
                                        "o_id": o_id,
                                        "w_id": None,
                                        "customername": customername,
                                        "webinar": w_topic,
                                        "speaker": None,
                                        "date": w.get("webinardate"),
                                        "time": None,
                                        "timeZone": None,
                                        "duration": None,
                                        "live_url": None,
                                        "recording_url": None,
                                        "digitaldownload_url": None,
                                        "transcript_url": None,
                                        "document": document,
                                        "order_type": order_type,
                                        "total_attendee": total_attendee
                                    }
                                dashboard_list.append(dashboard_dict)
                        else:
                            # Old-format order: uses flat sessionLive/sessionRecording fields
                            sessionLive = order.get("sessionLive")
                            sessionRecording = order.get("sessionRecording")
                            sessionDigitalDownload = order.get("sessionDigitalDownload")
                            sessionTranscript = order.get("sessionTranscript")
                            live_url = recording_url = digitaldownload_url = transcript_url = None
                            webinar_data = list(mongo.db.webinar_data.find({"topic": topic}, projection))
                            if webinar_data:
                                webinar = webinar_data[0]
                                date_time = str(webinar.get("date_time"))
                                timeZone = webinar.get("timeZone")
                                handle_live = handle_timezone(date_time, timeZone)
                                if sessionLive == "true" and handle_live:
                                    live_url = webinar.get("urlLive")
                                if sessionRecording == "true":
                                    recording_url = webinar.get("urlRecording")
                                if sessionDigitalDownload == "true":
                                    digitaldownload_url = webinar.get("urlDigitalDownload")
                                if sessionTranscript == "true":
                                    transcript_url = webinar.get("urlTranscript")
                                dashboard_dict = {
                                    "o_id": o_id,
                                    "w_id": webinar.get("id"),
                                    "customername": customername,
                                    "webinar": webinar.get("topic", topic),
                                    "speaker": webinar.get("speaker"),
                                    "date": webinar.get("date"),
                                    "time": webinar.get("time"),
                                    "timeZone": timeZone,
                                    "duration": webinar.get("duration"),
                                    "live_url": live_url,
                                    "recording_url": recording_url,
                                    "digitaldownload_url": digitaldownload_url,
                                    "transcript_url": transcript_url,
                                    "document": document,
                                    "order_type": order_type,
                                    "total_attendee": total_attendee
                                }
                                dashboard_list.append(dashboard_dict)

                        
        except Exception as e:

                dashboard_list=[str(e)]

        return dashboard_list, history_pending, history_purchased


def handle_othertimezone(webinar_datetime_str,timeZone):
        # Parsing the date and time string with timezone information
        try:
            webinar_datetime = datetime.fromisoformat(webinar_datetime_str.replace("Z", "+00:00"))
        except ValueError:
            return True

        # Time zones dictionary
        time_zones = {
            'PST': 'America/Los_Angeles',
            'EST': 'America/New_York',
            'IST': 'Asia/Kolkata',
            'UTC': 'UTC',
            'CST': 'America/Chicago'
        }

        # Validate the timeZone input
        if timeZone not in time_zones:
            return True
        
        # Convert to the specified timezone
        webinar_tz = pytz.timezone(time_zones[timeZone])
        webinar_datetime = webinar_datetime.astimezone(webinar_tz)

        # Convert to UTC
        webinar_datetime_utc = webinar_datetime.astimezone(pytz.UTC)

        # Get the current time in UTC
        current_datetime_utc = datetime.now(pytz.UTC).replace(second=0, microsecond=0)

        # Calculate the time difference
        time_difference = webinar_datetime_utc - current_datetime_utc

        # Check if the webinar is within the next 24 hours
        is_more_than_24_hours = timedelta(hours=24) < time_difference < timedelta(hours=1440)

        return is_more_than_24_hours
          



def handle_timezone(webinar_datetime_str,timeZone):
        
        # Parsing the date and time string with timezone information
        try:
            webinar_datetime = datetime.fromisoformat(webinar_datetime_str.replace("Z", "+00:00"))
        except ValueError:
            return True

        # Time zones dictionary
        time_zones = {
            'PST': 'America/Los_Angeles',
            'EST': 'America/New_York',
            'IST': 'Asia/Kolkata',
            'UTC': 'UTC',
            'CST': 'America/Chicago'
        }

        # Validate the timeZone input
        if timeZone not in time_zones:
            return True
        
        # Convert to the specified timezone
        webinar_tz = pytz.timezone(time_zones[timeZone])
        webinar_datetime = webinar_datetime.astimezone(webinar_tz)

        # Convert to UTC
        webinar_datetime_utc = webinar_datetime.astimezone(pytz.UTC)

        # Get the current time in UTC
        current_datetime_utc = datetime.now(pytz.UTC).replace(second=0, microsecond=0)

        # Calculate the time difference
        time_difference = webinar_datetime_utc - current_datetime_utc

        # Check if the webinar is within the next 24 hours
        is_within_next_24_hours = timedelta(hours=0) < time_difference < timedelta(hours=24)

        return is_within_next_24_hours
