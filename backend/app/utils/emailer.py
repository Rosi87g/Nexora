import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def send_verification_code(email: str, code: str):
    """Send email verification code"""
    msg = EmailMessage()
    msg["Subject"] = "Your Nexora Verification Code"
    msg["To"] = email
    msg["From"] = SMTP_EMAIL

    html_content = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 700;">Nexora</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Verify Your Email Address</p>
            </div>
            <div style="background: #f8fafc; padding: 30px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <h2 style="color: #1e293b; margin-bottom: 20px;">Your Verification Code</h2>
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; font-size: 32px; font-weight: 700; letter-spacing: 8px; padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);">
                    {code}
                </div>
                <p style="color: #64748b; margin-bottom: 10px;">This code will expire in <strong>10 minutes</strong></p>
                <p style="color: #64748b; font-size: 14px;">Enter this code in the app to verify your email address.</p>
            </div>
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f1f5f9; border-radius: 12px;">
                <p style="color: #64748b; margin: 0; font-size: 14px;">
                    Didn't request this code? <strong>Ignore this email</strong>
                </p>
            </div>
        </body>
    </html>
    """

    msg.set_content(f"Your Nexora verification code is: {code}")
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.send_message(msg)
        print(f"✅ Verification code sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send verification code to {email}: {e}")

def send_password_reset_email(email: str, token: str, frontend_url: str = "http://localhost:5173"):
    """Send password reset email"""
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    msg = EmailMessage()
    msg["Subject"] = "Reset Your Nexora Password"
    msg["To"] = email
    msg["From"] = SMTP_EMAIL

    html_content = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border-radius: 16px; color: white; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 700;">Reset Password</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;"></p>
            </div>
            <div style="background: #f8fafc; padding: 30px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <h2 style="color: #1e293b; margin-bottom: 20px;">Password Reset Request</h2>
                <p style="color: #475569; margin-bottom: 25px; line-height: 1.6;">
                    You requested to reset your password. Click the button below to create a new one:
                </p>
                <a href="{reset_url}" style="
                    display: inline-block;
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                    padding: 14px 32px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
                    transition: all 0.2s ease;
                ">Reset My Password</a>
                <p style="color: #64748b; margin: 25px 0 10px 0; font-size: 14px;">
                    This link will expire in <strong>1 hour</strong> for security reasons.
                </p>
            </div>
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f1f5f9; border-radius: 12px;">
                <p style="color: #64748b; margin: 0; font-size: 14px;">
                    If you didn't request a password reset, please ignore this email.
                </p>
            </div>
            <div style="text-align: center; margin-top: 25px; padding: 20px; color: #64748b; font-size: 12px; border-top: 1px solid #e2e8f0;">
                <p style="margin: 5px 0 0 0;">© 2025 Nexora. All rights reserved.</p>
            </div>
        </body>
    </html>
    """

    msg.set_content(f"""
    Reset your Nexora password:
    {reset_url}

    This link expires in 1 hour.

    If you didn't request this, ignore this email.
    """)
    
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.send_message(msg)
        print(f"✅ Password reset email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send password reset email to {email}: {e}")