import json
import os
from datetime import datetime
from google.cloud import storage
import importlib
import logging

# Importar módulos
from modules import analytics, search_console
from modules import report_generator, notifier
from utils import date_utils

def generate_monthly_reports(event, context):
    """Função principal para gerar os relatórios mensais."""
    try:
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info("Iniciando geração de relatórios mensais...")
        
        # Obter período do mês anterior
        start_date, end_date, month, year = date_utils.get_previous_month_dates()
        logger.info(f"Gerando relatórios para o período: {start_date} a {end_date}")
        
        # Carregar configuração dos clientes
        with open('config/clients.json', 'r') as f:
            clients_config = json.load(f)
        
        # Processar cada cliente
        for client in clients_config['clients']:
            logger.info(f"Processando cliente: {client['name']}")
            
            try:
                # 1. Extrair dados do Google Analytics
                analytics_data = analytics.get_analytics_data(
                    client['analytics']['property_id'], 
                    start_date, 
                    end_date
                )
                logger.info(f"Dados do Analytics extraídos com sucesso")
                
                # 2. Extrair dados do Search Console
                search_console_data = search_console.get_search_console_data(
                    client['search_console']['site_url'], 
                    start_date, 
                    end_date
                )
                logger.info(f"Dados do Search Console extraídos com sucesso")
                
                # 3. Gerar relatório
                logger.info(f"Gerando relatório PDF...")
                report = report_generator.ReportGenerator(
                    client,
                    'config/report_template.json',
                    month,
                    year,
                    client['report_config'].get('language', 'pt-BR')
                )
                
                # Adicionar dados ao relatório
                report.add_data('analytics', analytics_data)
                report.add_data('search_console', search_console_data)
                
                # Gerar PDF
                pdf_buffer = report.generate_pdf()
                
                # 4. Fazer upload do relatório para o Cloud Storage
                report_url = report_generator.upload_report(
                    pdf_buffer, 
                    client['id'], 
                    year, 
                    month
                )
                logger.info(f"Relatório enviado para: {report_url}")
                
                # 5. Notificar cliente
                pdf_buffer.seek(0)  # Resetar buffer para o início
                success, message = notifier.notify_client(
                    client, 
                    report_url, 
                    month, 
                    year, 
                    pdf_buffer
                )
                
                if success:
                    logger.info(f"Cliente notificado com sucesso: {message}")
                else:
                    logger.error(f"Erro ao notificar cliente: {message}")
                
            except Exception as e:
                logger.error(f"Erro ao processar cliente {client['name']}: {str(e)}")
                continue
        
        return "Relatórios mensais gerados com sucesso!"
    
    except Exception as e:
        logger.error(f"Erro na geração de relatórios: {str(e)}")
        return f"Erro: {str(e)}"

# Para teste local
if __name__ == "__main__":
    print(generate_monthly_reports(None, None))