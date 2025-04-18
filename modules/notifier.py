import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

def get_gmail_credentials():
    """Recupera as credenciais do Gmail do Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR_PROJECT_ID/secrets/gmail-credentials/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return service_account.Credentials.from_service_account_info(
        json.loads(response.payload.data.decode("UTF-8")),
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )

def send_email(to, subject, message_html, pdf_buffer, sender="monthly-digest@seu-dominio.com"):
    """
    Envia um e-mail com o relatório em anexo.
    
    Args:
        to: Endereço de e-mail do destinatário
        subject: Assunto do e-mail
        message_html: Corpo do e-mail em HTML
        pdf_buffer: Buffer com o conteúdo do PDF
        sender: Endereço de e-mail do remetente
    """
    credentials = get_gmail_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    
    # Criar mensagem
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Adicionar corpo do e-mail
    message.attach(MIMEText(message_html, 'html'))
    
    # Adicionar anexo
    pdf_attachment = MIMEApplication(pdf_buffer.read(), _subtype='pdf')
    pdf_buffer.seek(0)  # Resetar ponteiro do buffer para o início
    
    pdf_attachment.add_header('Content-Disposition', 'attachment', 
                             filename='relatorio_mensal.pdf')
    message.attach(pdf_attachment)
    
    # Codificar mensagem
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    # Enviar mensagem
    try:
        message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return True, f"E-mail enviado com ID: {message['id']}"
    except Exception as e:
        return False, f"Erro ao enviar e-mail: {str(e)}"

def notify_client(client, report_url, month, year, pdf_buffer):
    """
    Notifica o cliente sobre o relatório.
    
    Args:
        client: Configuração do cliente
        report_url: URL do relatório no Cloud Storage
        month: Mês do relatório (1-12)
        year: Ano do relatório
        pdf_buffer: Buffer com o conteúdo do PDF
    """
    # Meses em português
    month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    month_name = month_names[month - 1]
    
    # Criar assunto do e-mail
    subject = f"Relatório Mensal de Marketing Digital - {month_name} {year}"
    
    # Criar corpo do e-mail
    html_content = f"""
    <html>
    <body>
        <h2>Relatório Mensal de Marketing Digital</h2>
        <p>Olá equipe da {client['name']},</p>
        <p>Segue em anexo o relatório mensal de Marketing Digital referente ao mês de {month_name} de {year}.</p>
        <p>O relatório inclui dados de desempenho do seu site, incluindo análise de:</p>
        <ul>
            <li>Tráfego e comportamento dos usuários</li>
            <li>Desempenho nas buscas orgânicas</li>
            <li>Palavras-chave e consultas principais</li>
        </ul>
        <p>Para acessar todos os seus relatórios anteriores, acesse: <a href="https://console.cloud.google.com/storage/browser/{report_url.split('/')[2]}/{client['id']}">Repositório de Relatórios</a></p>
        <p>Em caso de dúvidas, estamos à disposição.</p>
        <p>Atenciosamente,<br>Equipe de Marketing Digital</p>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return send_email(
        to=client['report_config']['email'],
        subject=subject,
        message_html=html_content,
        pdf_buffer=pdf_buffer
    )