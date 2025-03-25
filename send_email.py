import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email():
    sender_email = os.getenv("GMAIL_SENDER")
    receiver_email = os.getenv("GMAIL_RECIPIENT")
    password = os.getenv("GMAIL_APP_PW")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = 'GitHub Actions - Teste de Envio de E-mail'

    body = f"O workflow do GitHub Actions foi executado com sucesso!"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

if __name__ == "__main__":
    send_email()
