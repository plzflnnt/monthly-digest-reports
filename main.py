import json
import os
from datetime import datetime
from google.cloud import storage
import importlib
import logging
import traceback

# Importar módulos
from modules import analytics as analytics_module
from modules import search_console as search_console_module
from modules import report_generator
from modules import notifier
from utils import date_utils
from utils import email_utils

# Importar verificador de dependências
from check_dependencies import check_dependencies

# Configurar logging detalhado
logging.basicConfig(
#    level=logging.WARNING,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monthly_digest.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_monthly_reports(event, context):
    """Função principal para gerar os relatórios mensais."""
    try:
        # Verificar dependências (opcional, mas útil para diagnóstico)
        if not check_dependencies():
            logger.warning("Algumas dependências podem estar ausentes ou mal configuradas")
            
        logger.info("Iniciando geração de relatórios mensais...")
        
        # Obter período do mês anterior
        start_date, end_date, month, year = date_utils.get_previous_month_dates()
        logger.info(f"Gerando relatórios para o período: {start_date} a {end_date}")
        
        # Carregar configuração dos clientes
        try:
            with open('config/clients.json', 'r', encoding='utf-8') as f:
                clients_config = json.load(f)
                logger.info(f"Configuração de {len(clients_config.get('clients', []))} clientes carregada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração dos clientes: {str(e)}")
            return f"Erro: Não foi possível carregar a configuração dos clientes. {str(e)}"
        
        # Diretório para templates
        template_dir = 'templates'
        os.makedirs(template_dir, exist_ok=True)
        
        # Verificar se o template existe
        template_path = os.path.join(template_dir, 'report_template.html')
        if not os.path.exists(template_path):
            logger.warning(f"Template não encontrado em {template_path}. Verifique se o arquivo existe.")
            return f"Erro: Template não encontrado em {template_path}"
        
        # Processar cada cliente
        processed_clients = 0
        for client in clients_config.get('clients', []):
            logger.info(f"Processando cliente: {client['name']}")
            
            try:
                # Adicionar opção de debug em config do cliente se não existir
                if 'report_config' not in client:
                    client['report_config'] = {}
                
                # Habilitar debug para o primeiro cliente ou para clientes específicos
                if processed_clients == 0 or client.get('id') == 'client_requiring_debug':
                    client['report_config']['enable_debug'] = True
                    logger.info(f"Modo de debug ativado para o cliente: {client['name']}")
                
                # 1. Extrair dados do Google Analytics
                logger.info(f"Obtendo dados do Analytics...")
                try:
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
                    
                    # Salvar dados brutos para debug se necessário
                    if client['report_config'].get('enable_debug', False):
                        debug_dir = f"debug_{client['id']}"
                        os.makedirs(debug_dir, exist_ok=True)
                        with open(f"{debug_dir}/analytics_data.json", "w", encoding='utf-8') as f:
                            json.dump(analytics_data, f, default=str, indent=2)
                        logger.info(f"Dados do Analytics salvos para debug em {debug_dir}/analytics_data.json")
                
                except Exception as e:
                    logger.error(f"Erro ao extrair dados do Analytics: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Usar dados mínimos para não interromper o fluxo
                    analytics_data = {"basic_metrics": {}, "daily_metrics": []}
                    prev_analytics_data = {"basic_metrics": {}, "daily_metrics": []}
                    annual_analytics_data = {}
                
                # 2. Extrair dados do Search Console
                logger.info(f"Obtendo dados do Search Console...")
                try:
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
                    
                    # Salvar dados brutos para debug se necessário
                    if client['report_config'].get('enable_debug', False):
                        debug_dir = f"debug_{client['id']}"
                        os.makedirs(debug_dir, exist_ok=True)
                        with open(f"{debug_dir}/search_console_data.json", "w") as f:
                            json.dump(search_console_data, f, default=str, indent=2)
                        logger.info(f"Dados do Search Console salvos para debug em {debug_dir}/search_console_data.json")
                
                except Exception as e:
                    logger.error(f"Erro ao extrair dados do Search Console: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Usar dados mínimos para não interromper o fluxo
                    search_console_data = {"performance_by_date": [], "total_impressions": 0, "total_clicks": 0}
                    prev_search_console_data = {"performance_by_date": [], "total_impressions": 0, "total_clicks": 0}
                
                # 3. Gerar relatório
                logger.info(f"Gerando relatório...")
                try:
                    # Instanciar o gerador de relatórios
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
                    
                    # Gerar HTML com tratamento de exceções específico para esta etapa
                    try:
                        html_content = report.generate_html()
                        logger.info(f"HTML do relatório gerado com sucesso")

                        # Obter os buffers de imagens dos gráficos
                        chart_buffers = report.get_chart_buffers()
                        
                        # Salvar uma cópia do HTML para debug
                        if client['report_config'].get('enable_debug', False):
                            debug_dir = f"debug_{client['id']}"
                            os.makedirs(debug_dir, exist_ok=True)
                            with open(f"{debug_dir}/report.html", "w", encoding="utf-8") as f:
                                f.write(html_content)
                            logger.info(f"HTML salvo para debug em {debug_dir}/report.html")
                            
                    except Exception as html_error:
                        logger.error(f"Erro ao gerar HTML do relatório: {str(html_error)}")
                        logger.error(traceback.format_exc())
                        # Continuar com HTML mínimo para não interromper fluxo
                        month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                        month_name = month_names[month - 1]
                        html_content = f"""
                        <html><body>
                        <h1>Relatório de {month_name} {year} - {client['name']}</h1>
                        <p>Ocorreu um erro ao gerar o relatório. Por favor, entre em contato com o suporte.</p>
                        <p>Erro: {str(html_error)}</p>
                        </body></html>
                        """
                    
                    # Otimizar HTML para e-mail
                    optimized_html = email_utils.optimize_html_for_email(html_content)
                    logger.info(f"HTML otimizado para e-mail")
                    
                    # Gerar PDF
                    try:
                        logger.info(f"Gerando PDF...")
                        pdf_buffer = report.generate_pdf()
                        logger.info(f"PDF do relatório gerado com sucesso")
                    except Exception as pdf_error:
                        logger.error(f"Erro ao gerar PDF do relatório: {str(pdf_error)}")
                        logger.error(traceback.format_exc())
                        # Criar um buffer vazio para não interromper o fluxo
                        from io import BytesIO
                        pdf_buffer = BytesIO(b"Erro ao gerar PDF")
                
                except Exception as report_error:
                    logger.error(f"Erro ao processar relatório: {str(report_error)}")
                    logger.error(traceback.format_exc())
                    continue  # Pular para o próximo cliente em caso de erro grave
                
                # 4. Fazer upload do relatório para o Cloud Storage
                logger.info(f"Enviando relatório para o Cloud Storage...")
                try:
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
                except Exception as upload_error:
                    logger.error(f"Erro ao fazer upload do relatório: {str(upload_error)}")
                    logger.error(traceback.format_exc())
                    report_url = f"gs://monthly-digest-reports/{client['id']}/report_{year}_{month:02d}.pdf"
                
                # 5. Notificar cliente com o HTML otimizado como corpo do e-mail
                logger.info(f"Notificando cliente...")
                try:
                    pdf_buffer.seek(0)  # Resetar buffer para o início
                    success, message = notifier.notify_client(
                        client, 
                        report_url, 
                        month, 
                        year, 
                        pdf_buffer,
                        report_html=optimized_html,  # Usar o HTML otimizado no corpo do e-mail
                        chart_buffers=chart_buffers  # Passar os buffers de imagens
                    )
                    
                    if success:
                        logger.info(f"Cliente notificado com sucesso: {message}")
                    else:
                        logger.error(f"Erro ao notificar cliente: {message}")
                except Exception as notify_error:
                    logger.error(f"Erro ao notificar cliente: {str(notify_error)}")
                    logger.error(traceback.format_exc())
                
                processed_clients += 1
                logger.info(f"Cliente {client['name']} processado com sucesso")
                
            except Exception as client_error:
                logger.error(f"Erro ao processar cliente {client['name']}: {str(client_error)}")
                logger.error(traceback.format_exc())
                continue
        
        # Resumo final
        if processed_clients > 0:
            logger.info(f"Relatórios mensais gerados com sucesso para {processed_clients} clientes!")
            return f"Relatórios mensais gerados com sucesso para {processed_clients} clientes!"
        else:
            error_msg = "Nenhum cliente foi processado com sucesso."
            logger.error(error_msg)
            return f"Erro: {error_msg}"
    
    except Exception as e:
        logger.error(f"Erro na geração de relatórios: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Erro: {str(e)}"

# Para teste local
if __name__ == "__main__":
    print(generate_monthly_reports(None, None))