from app import (
    app,
    mongo,
    s3_client,
    mail,
    stripe_secret_key,
    apply_mail_config_by_website,
    get_mail_sender_by_website
)
from flask import request, jsonify, session, render_template_string
from flask_mail import Message
# from dotenv import load_dotenv
import string
import random
import datetime
import pytz
import stripe
import json
import io
from io import BytesIO
import os

from app.model_login import Login
from app.model_webinar import Webinar
from app.model_speaker import Speaker
from app.model_utility import Utility
from app.model_order import Order
from app.model_newsletter import Newsletter


# load_dotenv()
# stripe.api_key = os.environ.get("stripe_secret_key")
stripe.api_key = stripe_secret_key

VALID_WEBSITES = ["HEALTHPROFS", "PHARMAPROFS", "HRPROFS"]

WEBSITE_URLS = {
    "HEALTHPROFS": "https://healthprofs.com/",
    "PHARMAPROFS": "https://pharmaprofs.com/",
    "HRPROFS": "https://hrprofs.com/",
}

WEBSITE_SUPPORT_EMAILS = {
    "HEALTHPROFS": "support@healthprofs.com",
    "PHARMAPROFS": "support@pharmaprofs.com",
    "HRPROFS": "support@hrprofs.com",
}

WEBSITE_QUERY_EMAILS = {
    "HEALTHPROFS": "support@healthprofs.com",
    "PHARMAPROFS": "support@pharmaprofs.com",
    "HRPROFS": "support@hrprofs.com",
}


def normalize_website(website):
    if not website:
        return None
    return str(website).upper().strip()


def validate_website(website):
    website = normalize_website(website)

    if not website:
        return None

    if website not in VALID_WEBSITES:
        return None

    return website


def get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return {}


def get_request_value(key, default=None):
    """
    Reads value from:
    1. request.form
    2. request.json
    3. request.args

    This keeps existing form-based APIs working and also supports JSON/GET routes.
    """
    value = request.form.get(key)

    if value is not None:
        return value

    data = get_request_data()
    value = data.get(key)

    if value is not None:
        return value

    value = request.args.get(key)

    if value is not None:
        return value

    return default


def get_website_from_request():
    """
    Frontend should send Website.

    Supported:
    - form-data: Website=PHARMAPROFS
    - json: {"Website": "PHARMAPROFS"}
    - query param for GET: ?Website=PHARMAPROFS

    Also supports lowercase website for existing frontend compatibility.
    """
    website = (
        get_request_value("Website")
        or get_request_value("website")
    )

    return validate_website(website)


def invalid_website_response():
    return jsonify({
        "success": False,
        "message": "Invalid or missing Website. Allowed values: HEALTHPROFS, PHARMAPROFS, HRPROFS"
    }), 400


def get_website_url(website):
    return WEBSITE_URLS.get(website)


def get_support_email(website):
    return WEBSITE_SUPPORT_EMAILS.get(website)


def get_query_email(website):
    return WEBSITE_QUERY_EMAILS.get(website)


def prepare_mail_for_website(website):
    """
    Applies website-specific mail credentials from app/__init__.py.
    """
    if not apply_mail_config_by_website(website):
        return None

    sender = get_mail_sender_by_website(website)

    if not sender:
        return None

    return sender


# --------------------------------------------------
# Payment
# --------------------------------------------------

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    data = request.json or {}

    try:
        customer = stripe.Customer.create(
            email=data['email'],
            name=data['name'],
            address={
                'line1': "Address",
                'city': "City",
                'state': "State",
                'country': data['country'],
                'postal_code': 75201
            },
            source=data['stripeToken']
        )

        charge = stripe.Charge.create(
            customer=customer.id,
            amount=data['amount'] * 100,
            currency='inr',
            description=data['invoice_number']
        )

        created_time = datetime.datetime.fromtimestamp(
            customer['created']
        ).astimezone()

        return jsonify({
            'success': True,
            'amount': data['amount'],
            'date_time': created_time,
            'website': website
        })

    except stripe.error.CardError as e:
        return jsonify({'success': False, 'error': str(e)})
    except stripe.error.StripeError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify(error=str(e)), 403


# --------------------------------------------------
# Public website data
# --------------------------------------------------

@app.route('/')
def home():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    response = Utility.update_live_status()
    webinar_list = Webinar.view_webinar(website)
    # speaker_list = Speaker.view_speaker(website)

    return jsonify(webinar_list), 200


@app.route('/speaker')
def speaker():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    # response = Utility.update_live_status()
    # webinar_list = Webinar.view_webinar(website)
    speaker_list = Speaker.view_speaker(website)

    return jsonify(speaker_list), 200

@app.route('/coupon')
def coupon():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    coupon_list = Utility.view_coupon(website)

    return jsonify(coupon_list), 200


@app.route('/<w_id>', methods=['GET'])
def view_webinar(w_id):
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    webinar_data = Webinar.data_webinar(w_id, website)

    return webinar_data, 200


@app.route('/speaker/<s_id>', methods=['GET'])
def view_speakerdetails(s_id):
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    speaker_data = Speaker.data_speaker(s_id, website)

    return jsonify(speaker_data), 200


# --------------------------------------------------
# Register and login
# --------------------------------------------------

@app.route('/register', methods=['POST'])
def user_register():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    register_name = request.form.get("Name")
    register_email = request.form.get("Email")
    register_role = request.form.get("Role")
    register_number = request.form.get("Contact")
    register_password = request.form.get("Password")
    register_type = request.form.get("UserType")

    response = Login.register(
        register_name,
        register_email,
        register_role,
        register_number,
        register_password,
        register_type,
        website
    )

    return response


@app.route('/login', methods=['POST'])
def user_login():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    login_email = request.form.get("Email")
    login_password = request.form.get("Password")
    login_type = request.form.get("UserType")

    response_login = Login.authenticate(
        login_email,
        login_password,
        login_type,
        website
    )

    return response_login


@app.route('/forgotpassword', methods=['POST'])
def forgot_password():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    email = get_request_value("Email")

    response = Utility.forgotpassword(email, website)

    return response


# --------------------------------------------------
# Utilities
# --------------------------------------------------

@app.route('/subscribe', methods=['POST'])
def subscriber():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    data = request.json or {}

    subscriber_email = data.get("Subscriber")
    subscriber_name = data.get("subscriber_name")
    subscription_type = data.get("subscription_type")
    subscriber_jobtitle = data.get("subscriber_jobtitle")

    response = Utility.subscribe_list(
        subscriber_email,
        subscriber_name,
        subscription_type,
        subscriber_jobtitle,
        website
    )

    return response


@app.route('/unsubscribe', methods=['POST'])
def unsubscriber():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    data = request.json or {}

    unsubscriber_email = data.get("email")

    response = Utility.unsubscribe_list(unsubscriber_email, website)

    return response


@app.route('/contactus', methods=['POST'])
def contact_us():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    sender = prepare_mail_for_website(website)

    if not sender:
        return jsonify({
            "Message": "Mail configuration not found for selected Website."
        }), 400

    data = request.json or {}

    query_email = get_query_email(website)
    name = data.get("Name")
    email = data.get("Email")
    message_content = data.get("Message")

    try:
        msg = Message(
            'Query',
            sender=sender,
            recipients=[query_email]
        )

        msg.body = f"""
        Dear Team,

        We have received a query from:

        Name: {name}
        Email: {email}
        Website: {website}
        Message: {message_content}

        Best regards
        """

        msg.html = render_template_string("""
        <p>Dear Team,</p>
        <p>We have received a query from:</p>
        <ul>
            <li><b>Name:</b> {{ name }}</li>
            <li><b>Email:</b> {{ email }}</li>
            <li><b>Website:</b> {{ website }}</li>
        </ul>
        <p><b>Message:</b></p>
        <p>{{ message_content }}</p>
        <p>Best regards<br></p>
        """, name=name, email=email, website=website, message_content=message_content)

        mail.send(msg)

        return {
            "Message": "Thanks for contacting us. Our team will reach out to you shortly."
        }

    except Exception as e:
        return {
            "Message": "Failed to receive your request. Please try again later.",
            "error": str(e)
        }


@app.route('/speakeropportunity', methods=['POST'])
def speaker_opportunity():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    sender = prepare_mail_for_website(website)

    if not sender:
        return jsonify({
            "Message": "Mail configuration not found for selected Website."
        }), 400

    query_email = "brian@profstraining.com"

    name = request.form.get("Name")
    email = request.form.get("Email")
    education = request.form.get("Education")
    country = request.form.get("Country")
    phone = request.form.get("Phone")
    industries = request.form.get("Industries")
    bio = request.form.get("Bio")

    try:
        msg = Message(
            'Speaker Opportunity',
            sender=sender,
            recipients=[query_email]
        )

        msg.body = f"""
        Dear Team,

        We have received a new speaker opportunity query from:

        Name: {name}
        Email: {email}
        Education: {education}
        Country: {country}
        Phone: {phone}
        Industries: {industries}
        BIO: {bio}
        Website: {website}

        Best regards
        """

        msg.html = render_template_string("""
        <p>Dear Team,</p>
        <p>We have received a new speaker opportunity query from:</p>
        <ul>
            <li><b>Name:</b> {{ name }}</li>
            <li><b>Email:</b> {{ email }}</li>
            <li><b>Education:</b> {{ education }}</li>
            <li><b>Country:</b> {{ country }}</li>
            <li><b>Phone:</b> {{ phone }}</li>
            <li><b>Industries:</b> {{ industries }}</li>
            <li><b>BIO:</b> {{ bio }}</li>
            <li><b>Website:</b> {{ website }}</li>
        </ul>
        <p>Best regards,<br></p>
        """, name=name, email=email, education=education, country=country,
             phone=phone, industries=industries, bio=bio, website=website)

        mail.send(msg)

        return {
            "Message": "Your query has been successfully received. Our team will reach out to you shortly."
        }

    except Exception as e:
        return {
            "Message": "Failed to receive your query. Please try again later.",
            "error": str(e)
        }


# --------------------------------------------------
# Time utility
# --------------------------------------------------

def get_current_time_ist():
    ist_timezone = pytz.timezone('Asia/Kolkata')
    utc_now = datetime.datetime.utcnow()
    ist_now = pytz.utc.localize(utc_now).astimezone(ist_timezone)
    formatted_ist_now = ist_now.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_ist_now


# --------------------------------------------------
# Orders
# --------------------------------------------------

@app.route('/corportateorder', methods=['POST'])
def corporateorder():
    try:
        website = get_website_from_request()

        if not website:
            return invalid_website_response()

        sender = prepare_mail_for_website(website)

        if not sender:
            return jsonify({
                "success": False,
                "message": "Mail configuration not found for selected Website."
            }), 400

        paymentstatus = None
        current_time_ist = None
        invoice_number = None
        country = None
        zip_code = None
        discount = 0
        total_price = 0
        customername = None
        billingemail = None
        attendees = None
        total_attendee = 0
        session_data = []

        response_confirmationmail = {
            "success": False,
            "message": "Order Not Placed"
        }

        now_utc = datetime.datetime.now(pytz.utc)
        orderdate = now_utc.date()
        ordertime = now_utc.time()
        ordertimezone = now_utc.tzinfo

        id = len(list(mongo.db.corporate_order.find({}))) + 1
        id = str(id) + "_" + "CO"

        customeremail = request.form.get('customeremail')
        paymentstatus = request.form.get("paymentstatus")
        Webinar = request.form.get("topic")
        orderamount = request.form.get("orderamount")
        webinardate = request.form.get("webinardate")

        sessionLive = request.form.get("sessionLive")
        priceLive = request.form.get('priceLive')
        quantityLive = request.form.get('quantityLive')

        if sessionLive == "true":
            total_attendee += int(quantityLive)
            total_price += int(priceLive)
            session_data.append({"Live": priceLive})

        sessionRecording = request.form.get("sessionRecording")
        priceRecording = request.form.get('priceRecording')
        quantityRecording = request.form.get('quantityRecording')

        if sessionRecording == "true":
            total_price += int(priceRecording)
            total_attendee += int(quantityRecording)
            session_data.append({"Recording": priceRecording})

        sessionDigitalDownload = request.form.get('sessionDigitalDownload')
        priceDigitalDownload = request.form.get('priceDigitalDownload')
        quantityDigitalDownload = request.form.get('quantityDigitalDownload')

        if sessionDigitalDownload == "true":
            total_price += int(priceDigitalDownload)
            total_attendee += int(quantityDigitalDownload)
            session_data.append({"DigitalDownload": priceDigitalDownload})

        sessionTranscript = request.form.get("sessionTranscript")
        priceTranscript = request.form.get('priceTranscript')
        quantityTranscript = request.form.get('quantityTranscript')

        if sessionTranscript == "true":
            total_attendee += int(quantityTranscript)
            session_data.append({"Transcript": priceTranscript})

        keys = [list(item.keys())[0] for item in session_data]
        comma_separated_keys = ', '.join(keys)

        discount = int(total_price) - int(orderamount)

        if paymentstatus == "purchased":
            billingemail = request.form.get("billingemail")
            customername = request.form.get("customername")
            country = request.form.get("country")
            attendees = request.form.get("attendees")
            zip_code = request.form.get("zipcode")

            order_datetimezone = request.form.get("order_datetimezone")
            date_time_str = order_datetimezone

            date_time_format = "%a, %d %b %Y %H:%M:%S %Z"
            date_time_obj = datetime.datetime.strptime(date_time_str, date_time_format)

            gmt_timezone = pytz.timezone('GMT')
            est_timezone = pytz.timezone('US/Eastern')

            gmt_datetime = gmt_timezone.localize(date_time_obj)
            est_datetime = gmt_datetime.astimezone(est_timezone)

            orderdate = est_datetime.date()
            ordertime = est_datetime.time()
            ordertimezone = est_datetime.tzinfo
            order_datetime_str = f"{orderdate} {ordertime} EST"

            invoice_number = request.form.get("invoice_number")
            websiteUrl = get_website_url(website)
            current_time_ist = get_current_time_ist()

            document = Utility.generate_pdf(
                Webinar,
                customername,
                country,
                websiteUrl,
                billingemail,
                order_datetime_str,
                orderamount,
                invoice_number,
                discount,
                zip_code,
                id
            )

            document_ist = Utility.generatelocal_pdf(
                Webinar,
                customername,
                country,
                websiteUrl,
                billingemail,
                current_time_ist,
                orderamount,
                invoice_number,
                discount,
                zip_code,
                id
            )

        else:
            websiteUrl = get_website_url(website)
            document = ""
            document_ist = ""

        order_data = {
            "id": id,
            "topic": Webinar,
            "customeremail": customeremail,
            "paymentstatus": paymentstatus,
            "orderdate": str(orderdate),
            "ordertime": str(ordertime),
            "ordertimezone": str(ordertimezone),
            "webinardate": webinardate,
            "session": session_data,
            "sessionLive": request.form.get("sessionLive"),
            "priceLive": request.form.get('priceLive'),
            "quantityLive": request.form.get('quantityLive'),
            "sessionRecording": request.form.get("sessionRecording"),
            "priceRecording": request.form.get('priceRecording'),
            "quantityRecording": request.form.get('quantityRecording'),
            "sessionDigitalDownload": request.form.get('sessionDigitalDownload'),
            "priceDigitalDownload": request.form.get('priceDigitalDownload'),
            "quantityDigitalDownload": request.form.get('quantityDigitalDownload'),
            "sessionTranscript": request.form.get("sessionTranscript"),
            "priceTranscript": request.form.get('priceTranscript'),
            "quantityTranscript": request.form.get('quantityTranscript'),
            "attendees": attendees,
            "customername": customername,
            "billingemail": billingemail,
            "orderamount": orderamount,
            "country": country,
            "website": website,
            "document": document,
            "document_ist": document_ist,
            "ist_time": current_time_ist,
            "invoice_number": invoice_number,
            "total_attendee": total_attendee,
            "order_type": "corporate",
            "zip_code": zip_code
        }

        response_order = Order.update_corporateorder(order_data)
        response_user = Login.user_order(customeremail, paymentstatus, Webinar, website)
        Order.update_order(order_data)

        if paymentstatus == "purchased":
            try:
                msg = Message(
                    'Order Confirmation and Thank You',
                    sender=sender,
                    recipients=[billingemail],
                    bcc=['fulfillmentteam@aol.com']
                )

                msg.body = f"""
                Dear Customer,

                Thank you for your order!

                Here are your Order Details:
                Webinar Name: {Webinar}
                Order Amount: {orderamount}
                Session: {comma_separated_keys}
                Participants: {total_attendee}
                Invoice: {document}
                Website: {websiteUrl}

                We appreciate your business and look forward to seeing you at the webinar.

                Thanks & Regards!
                Fullfillment Team
                """

                msg.html = render_template_string("""
                <p>Dear Customer,</p>
                <p>Thank you for your order!</p>
                <p><b>Here are your Order Details:</b></p>
                <ul>
                    <li><b>Webinar Name:</b> {{ webinar_name }}</li>
                    <li><b>Order Amount:</b> {{ order_amount }}</li>
                    <li><b>Session:</b> {{ session }}</li>
                    <li><b>Participants:</b> {{ total_attendee }}</li>
                    <li><b>Invoice:</b> <a href="{{ s3_link }}">{{ s3_link }}</a></li>
                    <li><b>Website:</b> <a href="{{ website_url }}">{{ website_url }}</a></li>
                </ul>
                <p>We appreciate your business and look forward to seeing you at the webinar.</p>
                <p>Thanks & Regards!<br>Fullfillment Team</p>
                """, webinar_name=Webinar, s3_link=document,
                     session=comma_separated_keys, total_attendee=total_attendee,
                     order_amount=orderamount, website_url=websiteUrl)

                mail.send(msg)

                response_confirmationmail = {
                    "success": True,
                    "message": "Confimation mail delivered"
                }

            except Exception as e:
                response_confirmationmail = {
                    "success": False,
                    "message": str(e)
                }

        return jsonify(response_order, response_user, response_confirmationmail)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/order', methods=['POST'])
def order():
    try:
        website = get_website_from_request()

        if not website:
            return invalid_website_response()

        sender = prepare_mail_for_website(website)

        if not sender:
            return jsonify({
                "success": False,
                "message": "Mail configuration not found for selected Website."
            }), 400

        paymentstatus = None
        current_time_ist = None
        invoice_number = None
        country = None
        zip_code = None
        discount = 0
        total_price = 0
        customername = None
        billingemail = None
        session_data = []

        response_confirmationmail = {
            "success": False,
            "message": "Order Not Placed"
        }

        now_utc = datetime.datetime.now(pytz.utc)
        orderdate = now_utc.date()
        ordertime = now_utc.time()
        ordertimezone = now_utc.tzinfo

        id = len(list(mongo.db.order_data.find({}))) + 1
        id = str(id) + "_" + "O"

        customeremail = request.form.get('customeremail')
        paymentstatus = request.form.get("paymentstatus")
        Webinar = request.form.get("topic")
        orderamount = request.form.get("orderamount")
        webinardate = request.form.get("webinardate")

        sessionLive = request.form.get("sessionLive")
        priceLive = request.form.get('priceLive')

        if sessionLive == "true":
            total_price += int(priceLive)
            session_data.append({"Live": priceLive})

        sessionRecording = request.form.get("sessionRecording")
        priceRecording = request.form.get('priceRecording')

        if sessionRecording == "true":
            total_price += int(priceRecording)
            session_data.append({"Recording": priceRecording})

        sessionDigitalDownload = request.form.get('sessionDigitalDownload')
        priceDigitalDownload = request.form.get('priceDigitalDownload')

        if sessionDigitalDownload == "true":
            total_price += int(priceDigitalDownload)
            session_data.append({"DigitalDownload": priceDigitalDownload})

        sessionTranscript = request.form.get("sessionTranscript")
        priceTranscript = request.form.get('priceTranscript')

        if sessionTranscript == "true":
            session_data.append({"Transcript": priceTranscript})

        keys = [list(item.keys())[0] for item in session_data]
        comma_separated_keys = ', '.join(keys)

        discount = int(total_price) - int(orderamount)

        if paymentstatus == "purchased":
            billingemail = request.form.get("billingemail")
            customername = request.form.get("customername")
            country = request.form.get("country")
            zip_code = request.form.get("zipcode")

            order_datetimezone = request.form.get("order_datetimezone")
            date_time_str = order_datetimezone

            date_time_format = "%a, %d %b %Y %H:%M:%S %Z"
            date_time_obj = datetime.datetime.strptime(date_time_str, date_time_format)

            gmt_timezone = pytz.timezone('GMT')
            est_timezone = pytz.timezone('US/Eastern')
            ist_timezone = pytz.timezone('Asia/Kolkata')

            gmt_datetime = gmt_timezone.localize(date_time_obj)
            est_datetime = gmt_datetime.astimezone(est_timezone)
            ist_datetime = gmt_datetime.astimezone(ist_timezone)

            orderdate = est_datetime.date()
            ordertime = est_datetime.time()
            ordertimezone = est_datetime.tzinfo
            order_datetime_str = f"{orderdate} {ordertime} EST"

            invoice_number = request.form.get("invoice_number")
            websiteUrl = get_website_url(website)
            current_time_ist = ist_datetime

            document = Utility.generate_pdf(
                Webinar,
                customername,
                country,
                websiteUrl,
                billingemail,
                order_datetime_str,
                orderamount,
                invoice_number,
                discount,
                zip_code,
                id
            )

            document_ist = Utility.generatelocal_pdf(
                Webinar,
                customername,
                country,
                websiteUrl,
                billingemail,
                current_time_ist,
                orderamount,
                invoice_number,
                discount,
                zip_code,
                id
            )

        else:
            websiteUrl = get_website_url(website)
            document = ""
            document_ist = ""

        order_data = {
            "id": id,
            "topic": Webinar,
            "customeremail": customeremail,
            "paymentstatus": paymentstatus,
            "orderdate": str(orderdate),
            "ordertime": str(ordertime),
            "ordertimezone": str(ordertimezone),
            "webinardate": webinardate,
            "session": session_data,
            "sessionLive": request.form.get("sessionLive"),
            "priceLive": request.form.get('priceLive'),
            "sessionRecording": request.form.get("sessionRecording"),
            "priceRecording": request.form.get('priceRecording'),
            "sessionDigitalDownload": request.form.get('sessionDigitalDownload'),
            "priceDigitalDownload": request.form.get('priceDigitalDownload'),
            "sessionTranscript": request.form.get("sessionTranscript"),
            "priceTranscript": request.form.get('priceTranscript'),
            "customername": customername,
            "billingemail": billingemail,
            "orderamount": orderamount,
            "country": country,
            "website": website,
            "document": document,
            "document_ist": document_ist,
            "ist_time": current_time_ist,
            "invoice_number": invoice_number,
            "order_type": "individual",
            "zip_code": zip_code
        }

        response_order = Order.update_order(order_data)
        response_user = Login.user_order(customeremail, paymentstatus, Webinar, website)

        if paymentstatus == "purchased":
            try:
                msg = Message(
                    'Order Confirmation and Thank You',
                    sender=sender,
                    recipients=[billingemail],
                    bcc=['fulfillmentteam@aol.com']
                )

                msg.body = f"""
                Dear Customer,

                Thank you for your order!

                Here are your Order Details:
                Webinar Name: {Webinar}
                Order Amount: {orderamount}
                Session: {comma_separated_keys}
                Invoice: {document}
                Website: {websiteUrl}

                We appreciate your business and look forward to seeing you at the webinar.

                Thanks & Regards!
                Fullfillment Team
                """

                msg.html = render_template_string("""
                <p>Dear Customer,</p>
                <p>Thank you for your order!</p>
                <p><b>Here are your Order Details:</b></p>
                <ul>
                    <li><b>Webinar Name:</b> {{ webinar_name }}</li>
                    <li><b>Order Amount:</b> {{ order_amount }}</li>
                    <li><b>Session:</b> {{ session }}</li>
                    <li><b>Invoice:</b> <a href="{{ s3_link }}">{{ s3_link }}</a></li>
                    <li><b>Website:</b> <a href="{{ website_url }}">{{ website_url }}</a></li>
                </ul>
                <p>We appreciate your business and look forward to seeing you at the webinar.</p>
                <p>Thanks & Regards!<br>Fullfillment Team</p>
                """, webinar_name=Webinar, s3_link=document,
                     session=comma_separated_keys, order_amount=orderamount,
                     website_url=websiteUrl)

                mail.send(msg)

                response_confirmationmail = {
                    "success": True,
                    "message": "Confimation mail delivered"
                }

            except Exception as e:
                response_confirmationmail = {
                    "success": False,
                    "message": str(e)
                }

        return jsonify(response_order, response_user, response_confirmationmail)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/newsletterorder', methods=['POST'])
def newsletter_order():
    try:
        website = get_website_from_request()

        if not website:
            return invalid_website_response()

        sender = prepare_mail_for_website(website)

        if not sender:
            return jsonify({
                "success": False,
                "message": "Mail configuration not found for selected Website."
            }), 400

        paymentstatus = None
        current_time_ist = None
        invoice_number = None

        zip_code = "N/A"
        discount = 0
        billingemail = None
        customeremail = None
        country = "N/A"
        customername = "N/A"

        response_confirmationmail = {
            "success": False,
            "message": "Order Not Placed"
        }

        now_utc = datetime.datetime.now(pytz.utc)
        orderdate = now_utc.date()
        ordertime = now_utc.time()
        ordertimezone = now_utc.tzinfo

        id = len(list(mongo.db.newsletter_order.find({}))) + 1
        id = str(id) + "_" + "NO"

        customeremail = request.form.get('customeremail')
        paymentstatus = request.form.get("paymentstatus")
        newsletter = request.form.get("topic")
        orderamount = request.form.get("orderamount")

        if paymentstatus == "purchased":
            billingemail = request.form.get("billingemail")

            if int(orderamount) != 0:
                try:
                    newsletter_data = mongo.db.newsletter_data.find_one(
                        {
                            "topic": newsletter,
                            "website": website
                        },
                        {
                            "price": 1,
                            "_id": 0
                        }
                    )

                    if newsletter_data:
                        price_value = newsletter_data.get("price", 0)
                        discount = int(price_value) - int(orderamount)
                    else:
                        discount = 0

                except Exception:
                    discount = 0

                customername = request.form.get("customername")
                country = request.form.get("country")
                zip_code = request.form.get("zipcode")

            order_datetimezone = request.form.get("order_datetimezone")
            date_time_str = order_datetimezone

            try:
                date_time_format = "%a, %d %b %Y %H:%M:%S %Z"
                date_time_obj = datetime.datetime.strptime(date_time_str, date_time_format)

                gmt_timezone = pytz.timezone('GMT')
                est_timezone = pytz.timezone('US/Eastern')
                ist_timezone = pytz.timezone('Asia/Kolkata')

                gmt_datetime = gmt_timezone.localize(date_time_obj)
                est_datetime = gmt_datetime.astimezone(est_timezone)
                ist_datetime = gmt_datetime.astimezone(ist_timezone)

                orderdate = est_datetime.date()
                ordertime = est_datetime.time()
                ordertimezone = est_datetime.tzinfo
                order_datetime_str = f"{orderdate} {ordertime} EST"
                current_time_ist = ist_datetime

            except Exception:
                date_time_obj = datetime.datetime.fromisoformat(
                    date_time_str.replace("Z", "+00:00")
                )

                orderdate = date_time_obj.date()
                ordertime = date_time_obj.time()
                ordertimezone = pytz.timezone('US/Eastern')
                order_datetime_str = f"{orderdate} {ordertime} EST"

                ist_timezone = pytz.timezone('Asia/Kolkata')
                utc_now = datetime.datetime.utcnow()
                ist_now = pytz.utc.localize(utc_now).astimezone(ist_timezone)
                current_time_ist = ist_now

            invoice_number = request.form.get("invoice_number")
            websiteUrl = get_website_url(website)

            document = Utility.generate_pdf(
                newsletter,
                customername,
                country,
                websiteUrl,
                billingemail,
                order_datetime_str,
                orderamount,
                invoice_number,
                discount,
                zip_code,
                id
            )

            document_ist = Utility.generatelocal_pdf(
                newsletter,
                customername,
                country,
                websiteUrl,
                billingemail,
                current_time_ist,
                orderamount,
                invoice_number,
                discount,
                zip_code,
                id
            )

        else:
            websiteUrl = get_website_url(website)
            document = ""
            document_ist = ""

        order_data = {
            "id": id,
            "topic": newsletter,
            "customeremail": customeremail,
            "paymentstatus": paymentstatus,
            "orderdate": str(orderdate),
            "ordertime": str(ordertime),
            "ordertimezone": str(ordertimezone),
            "customername": customername,
            "billingemail": billingemail,
            "orderamount": orderamount,
            "discount": discount,
            "country": country,
            "website": website,
            "document": document,
            "document_ist": document_ist,
            "ist_time": current_time_ist,
            "invoice_number": invoice_number,
            "order_type": "newsletter",
            "zip_code": zip_code,
        }

        response_order = Order.update_newsletterorder(order_data)
        response_user = Login.user_newsletterorder(
            customeremail,
            paymentstatus,
            newsletter,
            website
        )

        Order.update_order(order_data)

        if paymentstatus == "purchased":
            try:
                msg = Message(
                    'Order Confirmation and Thank You',
                    sender=sender,
                    recipients=[billingemail],
                    bcc=['fulfillmentteam@aol.com']
                )

                msg.body = f"""
                Dear Customer,

                Thank you for your order!

                Here are your Order Details:
                Newsletter Name: {newsletter}
                Order Amount: {orderamount}
                Invoice: {document}
                Website: {websiteUrl}

                We appreciate your business and look forward to seeing you at the webinar.

                Thanks & Regards!
                Fullfillment Team
                """

                msg.html = render_template_string("""
                <p>Dear Customer,</p>
                <p>Thank you for your order!</p>
                <p><b>Here are your Order Details:</b></p>
                <ul>
                    <li><b>Newsletter Name:</b> {{ newsletter_name }}</li>
                    <li><b>Order Amount:</b> {{ order_amount }}</li>
                    <li><b>Invoice:</b> <a href="{{ s3_link }}">{{ s3_link }}</a></li>
                    <li><b>Website:</b> <a href="{{ website_url }}">{{ website_url }}</a></li>
                </ul>
                <p>We appreciate your business and look forward to seeing you at the webinar.</p>
                <p>Thanks & Regards!<br>Fullfillment Team</p>
                """, newsletter_name=newsletter, s3_link=document,
                     order_amount=orderamount, website_url=websiteUrl)

                mail.send(msg)

                response_confirmationmail = {
                    "success": True,
                    "message": "Confimation mail delivered"
                }

            except Exception as e:
                response_confirmationmail = {
                    "success": False,
                    "message": str(e)
                }

        return jsonify(response_order, response_user, response_confirmationmail)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route('/dashboard/<email>/<user_type>', methods=['GET'])
def dashboard(email, user_type):
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    if user_type == "Speaker":
        dashboard_list, history = Speaker.speakerdashboard_data(email, website)
        return jsonify(dashboard_list, history)

    dashboard_list, history_pending, history_purchased = Order.find_order(email, website)
    newsletter_list, newsletter_purchased, newsletter_pending = Order.find_newsletterorder(email, website)

    return jsonify(
        dashboard_list,
        history_pending,
        history_purchased,
        newsletter_list,
        newsletter_purchased,
        newsletter_pending
    )


# --------------------------------------------------
# Newsletter section
# --------------------------------------------------

@app.route('/newsletter_panel/create_newsletter', methods=['POST'])
def create_newsletter():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    newsletters = Newsletter.count_newsletter(website)
    id = str(len(newsletters) + 1)

    newsletter_topic = request.form.get("topic")
    category = request.form.get("category")
    description = request.form.get("description")
    price = request.form.get("price")
    document = request.form.get("document")
    published_date = request.form.get("published_date")

    dt = datetime.datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    date_str = dt.strftime("%Y-%m-%d")

    thumbnail = request.files.get("thumbnail")

    N = 3
    res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
    n_id = res + "_" + id

    bucket_name = "webinarprofs"
    object_key = ''.join(newsletter_topic.split(" ")) + n_id

    try:
        s3_client.put_object(
            Body=thumbnail,
            Bucket=bucket_name,
            Key=f'newsletter/{object_key}.jpeg'
        )

        s3_url_thumbnail = f"https://{bucket_name}.s3.amazonaws.com/newsletter/{object_key}.jpeg"

    except Exception:
        s3_url_thumbnail = None

    newsletter_data = {
        "id": n_id,
        "topic": newsletter_topic,
        "category": category,
        "description": description,
        "website": website,
        "price": price,
        "status": "Active",
        "thumbnail": s3_url_thumbnail,
        "document": document,
        "published_date": date_str,
    }

    response = Newsletter.create_newsletter(newsletter_data)

    if response.get("success") is True:
        return response, 201

    return response, 400


@app.route('/newsletter_panel', methods=['GET'])
def view_newsletter():
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    response = Newsletter.activelist_newsletter(website)

    return response, 200


@app.route('/webinar/<w_id>')
def webinar_details(w_id):
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    webinar_info = Webinar.data_webinar(w_id, website)

    return webinar_info


@app.route('/newsletter/<n_id>')
def newsletter_details(n_id):
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    newsletter_info = Newsletter.view_newsletter(n_id, website)

    return newsletter_info


@app.route('/newsletter_panel/<n_id>', methods=['GET', 'POST'])
def update_newsletter(n_id):
    website = get_website_from_request()

    if not website:
        return invalid_website_response()

    if request.method == 'GET':
        newsletter_info = Newsletter.view_newsletter(n_id, website)
        return newsletter_info

    if request.method == 'POST':
        data = request.json or {}
        newsletter_status = data.get("status")

        response = Newsletter.edit_newsletter(n_id, newsletter_status, website)

        if response.get("success") is True:
            return response.get("message"), 201

        return response.get("message"), 304
