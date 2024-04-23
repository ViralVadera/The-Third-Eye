import smtplib
import random

def email(toemail):
    # Generate a random OTP
    otp = random.randint(1000, 9999)

    # SMTP server configuration
    HOST = "smtp-mail.outlook.com"
    PORT = 587

    # Email credentials and addresses
    FROM_EMAIL = "your_safe_house@outlook.com"
    TO_EMAIL = "viralvadera95@gmail.com"
    PASSWORD = "The_third_eye@95"

    # Prepare the email message
    MESSAGE = f"""From: {FROM_EMAIL}
    To: {TO_EMAIL}
    Subject: OTP

    Your OTP is: {otp}.
    """

    # Initialize SMTP client and connect to server
    try:
        smtp = smtplib.SMTP(HOST, PORT)
        smtp.ehlo()  # Identify yourself to the server
        smtp.starttls()  # Secure the connection
        smtp.login(FROM_EMAIL, PASSWORD)  # Log in to the server
        smtp.sendmail(FROM_EMAIL, TO_EMAIL, MESSAGE)  # Send the email
    except Exception as e:
        print(f"Failed to send email: {e}")
   
    smtp.quit()  # Disconnect from the server
    return otp
