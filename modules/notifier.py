import os
import base64
import logging
from mailjet_rest import Client
import json
from utils.secrets_utils import get_mailjet_credentials

def send_email(to, subject, message_html, chart_buffers=None, pdf_buffer=None, report_html=None, sender=None):
    """
    Envia um e-mail com o relatório em anexo usando o Mailjet.
    
    Args:
        to: Endereço de e-mail do destinatário
        subject: Assunto do e-mail
        message_html: Corpo do e-mail em HTML
        chart_buffers: Dicionário com buffers de imagens dos gráficos
        pdf_buffer: Buffer com o conteúdo do PDF (opcional por enquanto)
        report_html: Conteúdo HTML do relatório (opcional)
        sender: Configuração do remetente (opcional, usa o padrão do secret se não fornecido)
    """
    try:
        # Obter credenciais do Mailjet
        credentials = get_mailjet_credentials()
        
        # Configurar cliente do Mailjet
        mailjet = Client(auth=(credentials['api_key'], credentials['secret_key']), version='v3.1')
        
        # Definir remetente
        if not sender:
            sender_email = credentials['sender_email']
            sender_name = credentials['sender_name']
        else:
            sender_email = sender
            sender_name = "Relatórios Mensais"
        
        # Se o HTML do relatório estiver disponível, usá-lo como corpo do e-mail
        # Se não, usar o message_html original
        email_body = report_html if report_html else message_html
        
        # Preparar anexos
        attachments = []
        inlined_attachments = []
        # (codificar PDF em base64) PDF removido portemporariamente
        #pdf_buffer.seek(0)  # Garantir que o cursor está no início do buffer
        #pdf_content = pdf_buffer.read()
        #pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Adicionar gráficos como anexos inline
        if chart_buffers:
            for chart_name, buffer in chart_buffers.items():
                if buffer:
                    # Resetar buffer para o início
                    buffer.seek(0)
                    chart_content = buffer.read()
                    chart_base64 = base64.b64encode(chart_content).decode('utf-8')
                    
                    # Criar anexo inline
                    inline_attachment = {
                        'ContentType': 'image/png',
                        'Filename': f'{chart_name}.png',
                        'ContentID': f'chart_{chart_name}',
                        'Base64Content': chart_base64
                    }
                    
                    inlined_attachments.append(inline_attachment)
        
        # Temporariamente removemos o PDF como anexo, conforme solicitado
        # [Código do PDF comentado]
        
        # Construir payload da mensagem
        data = {
            'Messages': [
                {
                    'From': {
                        'Email': sender_email,
                        'Name': sender_name
                    },
                    'To': [
                        {
                            'Email': to,
                            'Name': ''
                        }
                    ],
                    'Subject': subject,
                    'HTMLPart': email_body,
                    'InlinedAttachments': inlined_attachments
                }
            ]
        }

        # Temporariamente removemos o PDF como anexo

        #'Attachments': [
        #                {
        #                    'ContentType': 'application/pdf',
        #                    'Filename': 'relatorio_mensal.pdf',
        #                    'Base64Content': pdf_base64
        #                }
        #            ]
        
        # Enviar e-mail
        result = mailjet.send.create(data=data)
        
        # Verificar resposta
        if result.status_code == 200:
            response_data = result.json()
            message_id = response_data['Messages'][0]['To'][0]['MessageID']
            return True, f"E-mail enviado com sucesso. ID da mensagem: {message_id}"
        else:
            return False, f"Erro ao enviar e-mail: {result.status_code} - {result.reason}"
    
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {str(e)}")
        return False, f"Erro ao enviar e-mail: {str(e)}"

def notify_client(client, report_url, month, year, pdf_buffer, report_html=None, chart_buffers=None):
    """
    Notifica o cliente sobre o relatório.
    
    Args:
        client: Configuração do cliente
        report_url: URL do relatório no Cloud Storage
        month: Mês do relatório (1-12)
        year: Ano do relatório
        pdf_buffer: Buffer com o conteúdo do PDF
        report_html: Conteúdo HTML do relatório (opcional)
        chart_buffers: Dicionário com buffers de imagens dos gráficos
    """
    # Meses em português
    month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    month_name = month_names[month - 1]
    
    # Criar assunto do e-mail
    subject = f"Seu Mês na Internet - {client['name']} - {month_name} {year}"
    
    # Se o HTML do relatório for fornecido, usá-lo diretamente como corpo do e-mail
    if report_html:
        # Enviar e-mail com o HTML do relatório como corpo
        return send_email(
            to=client['report_config']['email'],
            subject=subject,
            message_html="",  # Não usado quando report_html está presente
            pdf_buffer=pdf_buffer,
            report_html=report_html,
            chart_buffers=chart_buffers
        )
    else:
        # Criar corpo do e-mail padrão quando report_html não for fornecido
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #dddddd; border-radius: 5px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2C3E50;">Relatório Mensal de Marketing Digital</h2>
                    <p style="font-size: 18px;">{month_name} {year}</p>
                </div>
                
                <p>Olá equipe da <strong>{client['name']}</strong>,</p>
                
                <p>Esperamos que este e-mail encontre você bem! Anexamos o relatório mensal de Marketing Digital referente ao mês de {month_name} de {year}.</p>
                
                <p>O relatório inclui dados detalhados de desempenho do seu site, incluindo:</p>
                
                <ul style="background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
                    <li>Análise de tráfego e comportamento dos usuários</li>
                    <li>Desempenho nas buscas orgânicas</li>
                    <li>Palavras-chave e consultas principais</li>
                    <li>Páginas com melhor desempenho</li>
                </ul>
                
                <p>Para acessar todos os seus relatórios anteriores, utilize o link abaixo:</p>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://console.cloud.google.com/storage/browser/{report_url.split('/')[2]}/{client['id']}" 
                       style="background-color: #3498DB; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Acessar Repositório de Relatórios
                    </a>
                </div>
                
                <p>Caso tenha alguma dúvida sobre o relatório ou queira discutir estratégias baseadas nestes dados, não hesite em entrar em contato.</p>
                
                <p>Atenciosamente,<br>Equipe de Marketing Digital</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #777777; text-align: center;">
                    <p>Este é um e-mail automático. Por favor, não responda diretamente a este e-mail.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Enviar e-mail com o corpo padrão
        return send_email(
            to=client['report_config']['email'],
            subject=subject,
            message_html=html_content,
            pdf_buffer=pdf_buffer,
            chart_buffers=chart_buffers
        )