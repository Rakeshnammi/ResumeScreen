import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

class EmailNotifier:
    """Handles email notifications for shortlisted candidates"""
    
    def __init__(self):
        self.smtp_configured = False
    
    def configure_smtp(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str) -> bool:
        """
        Configure SMTP settings for sending emails
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (usually 587 for TLS)
            sender_email: Sender email address
            sender_password: Sender email password or app password
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
            self.sender_email = sender_email
            self.sender_password = sender_password
            
            # Test the connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            
            self.smtp_configured = True
            return True
        except Exception as e:
            print(f"SMTP configuration failed: {str(e)}")
            self.smtp_configured = False
            return False
    
    def send_notification_email(self, 
                                candidate: Dict, 
                                job_title: str,
                                company_name: str,
                                custom_message: str = "") -> bool:
        """
        Send notification email to a shortlisted candidate
        
        Args:
            candidate: Candidate dictionary with email and name
            job_title: Job title for the position
            company_name: Company name
            custom_message: Optional custom message to include
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.smtp_configured:
            return False
        
        recipient_email = candidate.get('email', '')
        if not recipient_email or recipient_email == 'Not Found':
            return False
        
        candidate_name = candidate.get('name', 'Candidate')
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Application Update - {job_title} Position"
            
            # Create HTML content
            html_content = self._create_email_template(
                candidate_name=candidate_name,
                job_title=job_title,
                company_name=company_name,
                score=candidate.get('overall_score', 0),
                custom_message=custom_message
            )
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    def send_batch_notifications(self, 
                                 candidates: List[Dict],
                                 job_title: str,
                                 company_name: str,
                                 custom_message: str = "") -> Dict[str, int]:
        """
        Send notification emails to multiple candidates
        
        Args:
            candidates: List of candidate dictionaries
            job_title: Job title for the position
            company_name: Company name
            custom_message: Optional custom message to include
            
        Returns:
            Dictionary with success and failure counts
        """
        results = {'success': 0, 'failed': 0}
        
        for candidate in candidates:
            if self.send_notification_email(candidate, job_title, company_name, custom_message):
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def _create_email_template(self, 
                               candidate_name: str,
                               job_title: str,
                               company_name: str,
                               score: float,
                               custom_message: str = "") -> str:
        """Create HTML email template"""
        
        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
                .score-badge {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Application Update</h2>
                </div>
                <div class="content">
                    <p>Dear {candidate_name},</p>
                    
                    <p>We are pleased to inform you that your application for the <strong>{job_title}</strong> position at <strong>{company_name}</strong> has been shortlisted for the next stage of our recruitment process.</p>
                    
                    <p>Your application scored <span class="score-badge">{score:.1f}%</span> in our initial screening.</p>
                    
                    {f'<p>{custom_message}</p>' if custom_message else ''}
                    
                    <p>We will contact you shortly regarding the next steps in the recruitment process.</p>
                    
                    <p>Thank you for your interest in joining our team!</p>
                    
                    <p>Best regards,<br>
                    {company_name} Recruitment Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Resume Screening System.<br>
                    Sent on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template
