# === FUNCIONES PARA ENVÍO DE CORREOS ===

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from .config import SMTP_CONFIG

def enviar_correo(destinatario, asunto, cuerpo, archivo_pdf=None):
    remitente = SMTP_CONFIG['user']
    password = SMTP_CONFIG['password']

    # Crear el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Adjuntar el archivo PDF si se pasa como argumento
    if archivo_pdf and os.path.isfile(archivo_pdf):
        try:
            with open(archivo_pdf, 'rb') as file:
                adjunto_pdf = MIMEApplication(file.read(), _subtype='pdf')
                adjunto_pdf.add_header('Content-Disposition', 'attachment', filename=os.path.basename(archivo_pdf))
                mensaje.attach(adjunto_pdf)
        except Exception as e:
            print(f"Error al adjuntar el archivo PDF: {e}")

    try:
        # Configurar el servidor SMTP
        server = smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port'])
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, mensaje.as_string())
        print(f"Correo enviado a {destinatario}")
    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")
    finally:
        server.quit()