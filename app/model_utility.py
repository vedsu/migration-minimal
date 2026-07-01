# Utilities

from app import (
    mongo,
    mail,
    s3_client,
    normalize_website,
    get_website_url,
    get_website_name,
    get_support_email,
    apply_mail_config_by_website,
    get_mail_sender_by_website
)
from datetime import datetime, timedelta
import pytz
from flask import render_template_string
from flask_mail import Message
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO


class Utility:

    @staticmethod
    def view_coupon(website=None):
        coupon_list = []

        try:
            website = normalize_website(website)

            query = {}

            # if website:
            #     query["website"] = website

            coupon_data = list(mongo.db.coupon_data.find(query))

            for coupon in coupon_data:
                coupon_dict = {
                    "id": coupon.get("id"),
                    "coupon": coupon.get("coupon"),
                    "type": coupon.get("type"),
                    "amount": coupon.get("amount"),
                    "status": coupon.get("status"),
                    "website": coupon.get("website")
                }

                coupon_list.append(coupon_dict)

        except Exception as e:
            coupon_list = {"error": str(e)}

        return coupon_list

    @staticmethod
    def update_live_status(website=None):
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)

        try:
            website = normalize_website(website)

            query = {
                "date_time": {
                    "$lt": current_time_est
                },
                "sessionLive": True
            }

            # if website:
            #     query["website"] = website

            mongo.db.webinar_data.update_many(
                query,
                {
                    "$set": {
                        "sessionLive": False
                    }
                }
            )

            return {
                "success": True,
                "message": "live session updated"
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    @staticmethod
    def generate_pdf(
        Webinar,
        customername,
        country,
        websiteUrl,
        billingemail,
        date_time_str,
        orderamount,
        invoice_number,
        discount,
        zip_code,
        orderID,
        website=None
    ):
        website = normalize_website(website)
        website_name = get_website_name(website)
        support_email = get_support_email(website)

        total_price = int(orderamount) + int(discount)

        def wrap_text(text, max_chars_per_line):
            words = text.split()
            lines = []
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars_per_line:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            return lines

        documentTitle = website_name
        title = "Invoice Details"

        leftSection = [
            f'Invoice Number # {invoice_number}',
            f'Date : {date_time_str}',
        ]

        rightSection1 = [
            support_email,
            websiteUrl
        ]

        customerDetails = [
            'Recipient Details:',
            f'Name : {customername}',
            f'Email : {billingemail}',
            f'Country : {country}',
            f'Zip Code : {zip_code}'
        ]

        orderDetails = [
            f'#{orderID}'
        ]

        webinarDetails = [
            'Description'
        ]

        max_chars_per_line = 60
        wrapped_webinar_details = wrap_text(Webinar, max_chars_per_line)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)

        pdf.setFont("Helvetica-Bold", 79)
        pdf.setFillColorRGB(0.9, 0.9, 0.9)
        pdf.saveState()
        pdf.translate(width / 2, height / 2)
        pdf.rotate(45)
        pdf.drawCentredString(0, 0, website_name)
        pdf.restoreState()
        pdf.setFillColor(colors.black)

        y_shift = 50

        pdf.setFont('Helvetica-Bold', 17)
        pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)

        pdf.setFont('Helvetica-Bold', 15)
        pdf.drawCentredString(width / 2, height - 75 - y_shift, title)

        pdf.setFont("Helvetica-Bold", 11)
        text = pdf.beginText(40, height - 105 - y_shift)

        for line in leftSection:
            text.textLine(line)

        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 105 - y_shift)

        for line in rightSection1:
            text.textLine(line)

        pdf.drawText(text)

        pdf.line(40, height - 170 - y_shift, width - 40, height - 170 - y_shift)

        text = pdf.beginText(40, height - 190 - y_shift)
        text.setFont("Helvetica-Bold", 13)
        text.textLine(customerDetails[0])
        text.setFont("Helvetica", 11)
        text.moveCursor(0, 18)

        for line in customerDetails[1:]:
            text.textLine(line)

        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 190 - y_shift)

        for line in orderDetails:
            text.textLine(line)

        pdf.drawText(text)

        pdf.line(40, height - 320 - y_shift, width - 40, height - 320 - y_shift)

        text = pdf.beginText(40, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(webinarDetails[0])

        for line in wrapped_webinar_details:
            text.textLine(line)

        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine('Total Price')
        text.textLine(f'${total_price}')
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 420 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(f'Subtotal: ${int(total_price)}')
        if int(discount) > 0:
            text.textLine(f'Discount: -${int(discount)}')
            text.textLine(f'Grand Total: ${int(orderamount)}')
        pdf.drawText(text)

        thankYouNote = 'Thank you for your Purchase'
        queryNote = f'Query? Reach out to us at {support_email} !'
        signature = 'Webinar Organizer Team'

        pdf.setFont("Helvetica-Oblique", 11)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, 125, thankYouNote)
        pdf.drawCentredString(width / 2, 105, queryNote)
        pdf.drawCentredString(width / 2, 85, signature)

        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(width / 2, 65, f'Website - {websiteUrl}')

        pdf.save()
        buffer.seek(0)

        bucket_name = "webinarprof"
        object_key = f'websiteorderist/{invoice_number}.pdf'

        s3_client.put_object(
            Body=buffer,
            Bucket=bucket_name,
            Key=object_key
        )

        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        return s3_url

    @staticmethod
    def generatelocal_pdf(
        Webinar,
        customername,
        country,
        websiteUrl,
        billingemail,
        date_time_str,
        orderamount,
        invoice_number,
        discount,
        zip_code,
        orderID,
        website=None
    ):
        website = normalize_website(website)
        website_name = get_website_name(website)
        support_email = get_support_email(website)

        total_price = int(orderamount) + int(discount)

        def wrap_text(text, max_chars_per_line):
            words = text.split()
            lines = []
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars_per_line:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            return lines

        documentTitle = website_name
        title = "Invoice Details"

        leftSection = [
            f'Invoice Number # {invoice_number}',
            f'Date : {date_time_str}',
        ]

        rightSection1 = [
            support_email,
            websiteUrl
        ]

        customerDetails = [
            'Recipient Details:',
            f'Name : {customername}',
            f'Email : {billingemail}',
            f'Country : {country}',
            f'Zip Code : {zip_code}'
        ]

        orderDetails = [
            f'#{orderID}'
        ]

        webinarDetails = [
            'Description'
        ]

        max_chars_per_line = 60
        wrapped_webinar_details = wrap_text(Webinar, max_chars_per_line)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)

        pdf.setFont("Helvetica-Bold", 79)
        pdf.setFillColorRGB(0.9, 0.9, 0.9)
        pdf.saveState()
        pdf.translate(width / 2, height / 2)
        pdf.rotate(45)
        pdf.drawCentredString(0, 0, website_name)
        pdf.restoreState()
        pdf.setFillColor(colors.black)

        y_shift = 50

        pdf.setFont('Helvetica-Bold', 17)
        pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)

        pdf.setFont('Helvetica-Bold', 15)
        pdf.drawCentredString(width / 2, height - 75 - y_shift, title)

        pdf.setFont("Helvetica-Bold", 11)
        text = pdf.beginText(40, height - 105 - y_shift)

        for line in leftSection:
            text.textLine(line)

        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 105 - y_shift)

        for line in rightSection1:
            text.textLine(line)

        pdf.drawText(text)

        pdf.line(40, height - 170 - y_shift, width - 40, height - 170 - y_shift)

        text = pdf.beginText(40, height - 190 - y_shift)
        text.setFont("Helvetica-Bold", 13)
        text.textLine(customerDetails[0])
        text.setFont("Helvetica", 11)
        text.moveCursor(0, 18)

        for line in customerDetails[1:]:
            text.textLine(line)

        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 190 - y_shift)

        for line in orderDetails:
            text.textLine(line)

        pdf.drawText(text)

        pdf.line(40, height - 320 - y_shift, width - 40, height - 320 - y_shift)

        text = pdf.beginText(40, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(webinarDetails[0])

        for line in wrapped_webinar_details:
            text.textLine(line)

        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine('Total Price')
        text.textLine(f'${total_price}')
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 420 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(f'Subtotal: ${int(total_price)}')
        if int(discount) > 0:
            text.textLine(f'Discount: -${int(discount)}')
            text.textLine(f'Grand Total: ${int(orderamount)}')
        pdf.drawText(text)

        thankYouNote = 'Thank you for your Purchase'
        queryNote = f'Query? Reach out to us at {support_email} !'
        signature = 'Webinar Organizer Team'

        pdf.setFont("Helvetica-Oblique", 11)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, 125, thankYouNote)
        pdf.drawCentredString(width / 2, 105, queryNote)
        pdf.drawCentredString(width / 2, 85, signature)

        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(width / 2, 65, f'Website - {websiteUrl}')

        pdf.save()
        buffer.seek(0)

        bucket_name = "webinarprof"
        object_key = f'websiteorder/{invoice_number}.pdf'

        s3_client.put_object(
            Body=buffer,
            Bucket=bucket_name,
            Key=object_key
        )

        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        return s3_url

    @staticmethod
    def subscribe_list(
        subscriber_email,
        subscriber_name,
        subscriber_phone,
        subscriber_jobtitle,
        subscriber_country,
        subscription_type,
        website = None
    ):
        current_datetime = datetime.now()

        try:
            website = normalize_website(website)

            subscriber_data = {
                "email": subscriber_email,
                "name": subscriber_name,
                "phone": subscriber_phone,
                "jobtitle": subscriber_jobtitle,
                "country": subscriber_country,
                "subscription_type": subscription_type,
                "type": "subscriber",
                "date": current_datetime
            }

            if website:
                subscriber_data["website"] = website

            mongo.db.subscriber_list.insert_one(subscriber_data)

            return ({
                "success": True,
                "message": "subscribed successfully"
            }), 201

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 403

    @staticmethod
    def unsubscribe_list(unsubscriber, website=None):
        current_datetime = datetime.now()

        try:
            website = normalize_website(website)

            unsubscriber_data = {
                "email": unsubscriber,
                "type": "unsubscriber",
                "date": current_datetime
            }

            if website:
                unsubscriber_data["website"] = website

            mongo.db.subscriber_list.insert_one(unsubscriber_data)

            return ({
                "success": True,
                "message": "unsubscribed successfully"
            }), 201

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 403

    @staticmethod
    def forgotpassword(email, website="PHARMAPROFS"):
        try:
            website = normalize_website(website)

            if not website:
                return ({
                    "success": False,
                    "message": "Invalid or missing Website"
                }), 400

            usercredentails = list(
                mongo.db.user_data.find({
                    "email": email,
                    "website": website
                })
            )

            if usercredentails:
                try:
                    if not apply_mail_config_by_website(website):
                        return ({
                            "success": False,
                            "message": "Mail configuration not found for selected Website"
                        }), 400

                    sender = get_mail_sender_by_website(website)

                    usercredentail = usercredentails[0]
                    email = usercredentail.get("email")
                    password = usercredentail.get("password")
                    websiteUrl = usercredentail.get("websiteUrl") or get_website_url(website)

                    msg = Message(
                        'Your Account Credentials',
                        sender=sender,
                        recipients=[email]
                    )

                    msg.body = f"""
                    Dear Customer,

                    Welcome to our website!

                    Here are your account credentials:

                    Email: {email}
                    Password: {password}
                    Website: {websiteUrl}

                    Please keep this information secure and do not share it with anyone.

                    Thanks & Regards!
                    Webinar Organizer Team
                    """

                    msg.html = render_template_string("""
                    <p>Dear Customer,</p>
                    <p>Welcome to our website!</p>
                    <p>Here are your account credentials:</p>
                    <ul>
                        <li><b>Email:</b> {{ email }}</li>
                        <li><b>Password:</b> {{ password }}</li>
                        <li><b>Website:</b> <a href="{{ website }}">{{ website }}</a></li>
                    </ul>
                    <p>Please keep this information secure and do not share it with anyone.</p>
                    <p>Thanks & Regards!<br>Webinar Organizer Team</p>
                    """, email=email, password=password, website=websiteUrl)

                    mail.send(msg)

                    return ({
                        "success": True,
                        "message": "email sent successfully"
                    }), 200

                except Exception as e:
                    return ({
                        "success": False,
                        "message": str(e)
                    }), 403

            return ({
                "success": False,
                "message": "User doesnot exists"
            }), 200

        except Exception as e:
            return ({
                "success": False,
                "message": str(e)
            }), 403
