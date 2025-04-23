import json
import os
from datetime import datetime
from google.cloud import storage
import importlib
import logging

# Importar módulos
from modules import analytics as analytics_module
from modules import search_console as search_console_module
from modules import report_generator
from modules import notifier
from utils import date_utils
from utils import email_utils  # Importar o novo módulo de otimização de e-mail

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
        
        # Diretório para templates
        template_dir = 'templates'
        os.makedirs(template_dir, exist_ok=True)
        
        # Verificar se o template existe
        template_path = os.path.join(template_dir, 'report_template.html')
        if not os.path.exists(template_path):
            logger.warning(f"Template não encontrado em {template_path}. Verifique se o arquivo existe.")
            return f"Erro: Template não encontrado em {template_path}"
        
        # Processar cada cliente
        for client in clients_config['clients']:
            logger.info(f"Processando cliente: {client['name']}")
            
            try:
                # 1. Extrair dados do Google Analytics
                # Dados do mês atual
                analytics_data = analytics_module.get_analytics_data(
                    client['analytics']['property_id'], 
                    start_date, 
                    end_date
                )
                logger.info(f"Dados do Analytics extraídos com sucesso")
                
                # Dados do mês anterior para comparação
                prev_analytics_data = analytics_module.get_previous_month_data(
                    client['analytics']['property_id'],
                    start_date,
                    end_date
                )
                logger.info(f"Dados do Analytics do mês anterior extraídos com sucesso")
                
                # Dados anuais para destaques
                annual_analytics_data = analytics_module.get_annual_data(
                    client['analytics']['property_id'],
                    end_date
                )
                logger.info(f"Dados anuais do Analytics extraídos com sucesso")
                
                # 2. Extrair dados do Search Console
                # Dados do mês atual
                search_console_data = search_console_module.get_search_console_data(
                    client['search_console']['site_url'], 
                    start_date, 
                    end_date
                )
                logger.info(f"Dados do Search Console extraídos com sucesso")
                
                # Dados do mês anterior para comparação
                prev_search_console_data = search_console_module.get_previous_month_data(
                    client['search_console']['site_url'],
                    start_date,
                    end_date
                )
                logger.info(f"Dados do Search Console do mês anterior extraídos com sucesso")
                
                # 3. Gerar relatório
                logger.info(f"Gerando relatório...")
                # Instanciar o gerador moderno de relatórios
                report = report_generator.ModernReportGenerator(
                    client,
                    template_path,
                    month,
                    year,
                    client['report_config'].get('language', 'pt-BR')
                )
                
                # Adicionar dados ao relatório
                report.add_data('analytics', analytics_data)
                report.add_data('search_console', search_console_data)
                
                # Adicionar dados do mês anterior para comparação
                report.add_previous_month_data(prev_analytics_data, prev_search_console_data)
                
                # Adicionar dados anuais para destaques
                report.add_annual_data(annual_analytics_data, None)  # Não precisamos de dados anuais do Search Console
                
                # Gerar HTML primeiro para uso no e-mail
                html_content = report.generate_html()
                logger.info(f"HTML do relatório gerado com sucesso")
                
                # Otimizar HTML para e-mail
                optimized_html = email_utils.optimize_html_for_email(html_content)
                logger.info(f"HTML otimizado para e-mail")
                
                # Gerar PDF
                pdf_buffer = report.generate_pdf()
                logger.info(f"PDF do relatório gerado com sucesso")
                
                # 4. Fazer upload do relatório para o Cloud Storage
                pdf_buffer.seek(0)  # Importante: resetar o buffer antes do upload
                from modules.report_generator import ModernReportGenerator
                report_url = ModernReportGenerator.upload_report(
                    pdf_buffer=pdf_buffer, 
                    client_id=client['id'], 
                    year=year, 
                    month=month,
                    bucket_name='monthly-digest-reports'
                )
                logger.info(f"Relatório enviado para: {report_url}")
                
                # 5. Notificar cliente com o HTML otimizado como corpo do e-mail
                pdf_buffer.seek(0)  # Resetar buffer para o início
                success, message = notifier.notify_client(
                    client, 
                    report_url, 
                    month, 
                    year, 
                    pdf_buffer,
                    report_html=optimized_html  # Usar o HTML otimizado no corpo do e-mail
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