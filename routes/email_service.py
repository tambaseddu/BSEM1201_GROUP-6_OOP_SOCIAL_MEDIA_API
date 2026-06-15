import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_verification_email(email: str, otp_code: str):
    """
    Dispatches a secure 6-digit verification code block directly to the user's inbox.
    """
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "tambarichardseddu@gmail.com"  # ✉️ Your actual email address
    SENDER_PASSWORD = "juimpzhndyryhpie"  # 🔑 Your 16-character Google App Password

    message = MIMEMultipart("alternative")
    message["Subject"] = f"{otp_code} is your Account Verification Code"
    message["From"] = SENDER_EMAIL
    message["To"] = email

    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #4F46E5; text-align: center;">Verify Your Account</h2>
            <p>Thank you for signing up! Use the security verification code below to activate your account identity:</p>
            
            <div style="background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; padding: 15px; text-align: center; margin: 25px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #1e293b;">{otp_code}</span>
            </div>
            
            <p style="font-size: 13px; color: #64748b; text-align: center;">This unique one-time code is highly secure and will automatically expire in 15 minutes.</p>
        </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, message.as_string())
        server.quit()
        print(f"[SMTP SUCCESS] OTP Code {otp_code} dispatched cleanly to {email}")
    except Exception as e:
        print(f"[SMTP ERROR] Failed to deliver token background thread task: {e}")
