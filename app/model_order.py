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
            mongo.db.order_data.insert_one(order_data)
           
            return ({"success": True, "message": return_data}),201
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
                    
                    live_url, recording_url, digitaldownload_url, transcript_url = None, None, None, None
                    o_id = order.get("id")
                    topic = order.get("topic")
                    customeremail = order.get("customeremail")
                    paymentstatus = order.get("paymentstatus")
                    sessionLive = order.get("sessionLive") #True /False
                    sessionRecording = order.get("sessionRecording") # True/ False
                    sessionDigitalDownload = order.get('sessionDigitalDownload') # True or False
                    sessionTranscript = order.get("sessionTranscript") # True or False
                    customername = order.get("customername")
                    document = order.get("document")
                    order_type = order.get("order_type")
                    total_attendee = order.get("total_attendee")

                    if paymentstatus == "purchased":
                        projection ={"_id":0}
                        webinar_data  = list(mongo.db.webinar_data.find({"topic":topic}, projection))
                        if webinar_data:
                            webinar = webinar_data[0]
                            w_id = webinar.get("id")
                            date = webinar.get("date")
                            time = webinar.get("time")
                            topic = webinar.get("topic")
                            speaker = webinar.get("speaker")
                            date_time = str(webinar.get("date_time"))
                            timeZone = webinar.get("timeZone")
                            duration = webinar.get("duration")
                            urlLive = webinar.get("urlLive")
                            urlRecording = webinar.get("urlRecording")
                            urlDigitalDownload = webinar.get("urlDigitalDownload")
                            urlTranscript = webinar.get("urlTranscript")
                            handle_live = handle_timezone(date_time, timeZone)
                            handle_other = handle_othertimezone(date_time, timeZone)
                            
                            if sessionLive == "true" and handle_live:
                                live_url =  urlLive
                            if sessionRecording == "true":
                                # if sessionRecording == "true" and handle_other:
                                recording_url = urlRecording
                            if sessionDigitalDownload == "true":
                                # if sessionDigitalDownload == "true" and handle_other:
                                digitaldownload_url = urlDigitalDownload
                            if sessionTranscript == "true":
                            # if sessionTranscript == "true" and handle_other:
                                transcript_url = urlTranscript
                            
                            dashboard_dict = {
                            "o_id":o_id,
                            "w_id":w_id,
                            "customername":customername ,
                            "webinar" : topic,
                            "speaker" : speaker ,
                            "date" : date,
                            "time" : time,
                            "timeZone" : timeZone,
                            "duration" : duration,
                            "live_url" : live_url,
                            "recording_url": recording_url,
                            "digitaldownload_url": digitaldownload_url,
                            "transcript_url" : transcript_url,
                            "document" : document,
                            "order_type":order_type,
                            "total_attendee":total_attendee
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
