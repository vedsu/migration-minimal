from app import (
    mongo,
    mail,
    apply_mail_config_by_website,
    get_mail_sender_by_website
)
from flask_mail import Message
from flask import render_template_string


WEBSITE_URLS = {
    "HEALTHPROFS": "https://healthprofs.com/",
    "PHARMAPROFS": "https://pharmaprofs.com/",
    "HRPROFS": "https://hrprofs.com/",
}


def normalize_website(website):
    if not website:
        return None

    return str(website).upper().strip()


def get_website_url(website):
    website = normalize_website(website)

    if not website:
        return None

    return WEBSITE_URLS.get(website)


class Login:

#     @staticmethod
#     def register(
#         register_name,
#         register_email,
#         register_role,
#         register_number,
#         register_password,
#         register_type,
#         website
#     ):
#         website = normalize_website(website)
#         websiteUrl = get_website_url(website)

#         if not website or not websiteUrl:
#             return ({
#                 "success": False,
#                 "message": "Invalid or missing Website"
#             }), 400

#         try:
#             user = mongo.db.user_data.find_one({
#                 "email": register_email,
#                 "website": website
#             })

#             if user:
#                 return ({
#                     "success": False,
#                     "message": "User already registered, Please Login"
#                 }), 203
#             if not apply_mail_config_by_website(website):
#                 return ({
#                     "success": False,
#                     "message": "Mail configuration not found for selected Website"
#                 }), 400

#             sender = get_mail_sender_by_website(website)


#             msg = Message(
#                 'Your Account Credentials',
#                 sender=sender,
#                 recipients=[register_email]
#             )

#             msg.body = f"""
#             Dear Customer {register_name},

#             Welcome to our website!

#             Here are your account credentials:

#             Email: {register_email}
#             Password: {register_password}
#             Website: {websiteUrl}

#             Please keep this information secure and do not share it with anyone.

#             Thanks & Regards!
#             Webinar Organizer Team
#             """

#             msg.html = render_template_string("""
#             <p>Dear Customer {{ name }},</p>
#             <p>Welcome to our website!</p>
#             <p>Here are your account credentials:</p>
#             <ul>
#                 <li><b>Email:</b> {{ email }}</li>
#                 <li><b>Password:</b> {{ password }}</li>
#                 <li><b>Website:</b> <a href="{{ website }}">{{ website }}</a></li>
#             </ul>
#             <p>Please keep this information secure and do not share it with anyone.</p>
#             <p>Thanks & Regards!<br>Webinar Organizer Team</p>
#             """, name=register_name, email=register_email,
#                  password=register_password, website=websiteUrl)

#             mail.send(msg)

#             user_response = {
#                 "name": register_name,
#                 "role": register_role,
#                 "email": register_email,
#                 "contact": register_number,
#                 "website": website
#             }

#             user_data = {
#                 "name": register_name,
#                 "role": register_role,
#                 "email": register_email,
#                 "contact": register_number,
#                 "password": register_password,
#                 "UserType": register_type,
#                 "website": website
#             }

#             if register_type == "Attendee":
#                 user_data.update({
#                     "history_purchased": [],
#                     "history_pending": [],
#                     "newsletter_purchased": [],
#                     "newsletter_pending": []
#                 })

#             mongo.db.user_data.insert_one(user_data)

#             return ({
#                 "success": True,
#                 "message": user_response
#             }), 201

#         except Exception as e:
#             return ({
#                 "success": False,
#                 "message": str(e)
#             }), 203

    
    @staticmethod
    def register(
        register_name,
        register_email,
        register_role,
        register_number,
        register_password,
        register_type,
        website
    ):
        website = normalize_website(website)
        websiteUrl = get_website_url(website)

        if not website or not websiteUrl:
            return ({
                "success": False,
                "message": "Invalid or missing Website"
            }), 400

        try:
            user = mongo.db.user_data.find_one({
                "email": register_email,
                "website": website
            })

            if user:
                return ({
                    "success": False,
                    "message": "User already registered, Please Login"
                }), 203

            user_response = {
                "name": register_name,
                "role": register_role,
                "email": register_email,
                "contact": register_number,
                "website": website
            }

            user_data = {
                "name": register_name,
                "role": register_role,
                "email": register_email,
                "contact": register_number,
                "password": register_password,
                "UserType": register_type,
                "website": website,
                "websiteUrl": websiteUrl
            }

            if register_type == "Attendee":
                user_data.update({
                    "history_purchased": [],
                    "history_pending": [],
                    "newsletter_purchased": [],
                    "newsletter_pending": []
                })

            mongo.db.user_data.insert_one(user_data)

            mail_status = {
                "success": False,
                "message": "Mail not sent"
            }

            try:
                if apply_mail_config_by_website(website):
                    sender = get_mail_sender_by_website(website)

                    msg = Message(
                        'Your Account Credentials',
                        sender=sender,
                        recipients=[register_email]
                    )

                    msg.body = f"""
                    Dear Customer {register_name},

                    Welcome to our website!

                    Here are your account credentials:

                    Email: {register_email}
                    Password: {register_password}
                    Website: {websiteUrl}

                    Please keep this information secure and do not share it with anyone.

                    Thanks & Regards!
                    Webinar Organizer Team
                    """

                    msg.html = render_template_string("""
                    <p>Dear Customer {{ name }},</p>
                    <p>Welcome to our website!</p>
                    <p>Here are your account credentials:</p>
                    <ul>
                        <li><b>Email:</b> {{ email }}</li>
                        <li><b>Password:</b> {{ password }}</li>
                        <li><b>Website:</b> <a href="{{ website }}">{{ website }}</a></li>
                    </ul>
                    <p>Please keep this information secure and do not share it with anyone.</p>
                    <p>Thanks & Regards!<br>Webinar Organizer Team</p>
                    """, name=register_name, email=register_email,
                         password=register_password, website=websiteUrl)

                    mail.send(msg)

                    mail_status = {
                        "success": True,
                        "message": "Mail sent successfully"
                    }

                else:
                    mail_status = {
                        "success": False,
                        "message": "Mail configuration not found for selected Website"
                    }

            except Exception as mail_error:
                mail_status = {
                    "success": False,
                    "message": str(mail_error)
                }

            return ({
                "success": True,
                "message": user_response,
                "mail_status": mail_status
            }), 201

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 203
    @staticmethod
    def authenticate(login_email, login_password, login_type, website):
        website = normalize_website(website)

        if not website:
            return ({
                "success": False,
                "message": "Invalid or missing Website"
            }), 400

        try:
            user = mongo.db.user_data.find_one(
                {
                    "email": login_email,
                    "password": login_password,
                    "UserType": login_type,
                    "website": website
                },
                {
                    "_id": 0
                }
            )

            if user:
                return ({
                    "success": True,
                    "message": user
                }), 200

            return ({
                "success": False,
                "message": "invalid credentials"
            }), 203

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 203

    @staticmethod
    def user_order(user, order_type, webinar, website=None):
        website = normalize_website(website)

        try:
            query = {
                "email": user
            }

            if website:
                query["website"] = website

            if order_type == "purchased":
                mongo.db.user_data.update_one(
                    query,
                    {
                        "$addToSet": {
                            "history_purchased": webinar
                        }
                    }
                )
            else:
                mongo.db.user_data.update_one(
                    query,
                    {
                        "$addToSet": {
                            "history_pending": webinar
                        }
                    }
                )

            return ({
                "success": True,
                "message": "webinar updated for user"
            }), 200

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 203

    @staticmethod
    def user_newsletterorder(user, order_type, webinar, website=None):
        website = normalize_website(website)

        try:
            query = {
                "email": user
            }

            if website:
                query["website"] = website

            if order_type == "purchased":
                mongo.db.user_data.update_one(
                    query,
                    {
                        "$addToSet": {
                            "newsletter_purchased": webinar
                        }
                    }
                )
            else:
                mongo.db.user_data.update_one(
                    query,
                    {
                        "$addToSet": {
                            "newsletter_pending": webinar
                        }
                    }
                )

            return ({
                "success": True,
                "message": "newsletter updated for user"
            }), 200

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 203
