# test_integration_new.py
import json
import os
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos atualizados
from modules import analytics as analytics_module
from modules import search_console as search_console_module
from modules.report_generator import ModernReportGenerator
from utils import date_utils

def test_integration():
    """Testa a integração dos módulos atualizados."""
    logger.info("Iniciando teste de integração dos módulos atualizados...")
    
    # Criar diretório para templates e resultados
    os.makedirs('templates', exist_ok=True)
    os.makedirs('test_results', exist_ok=True)
    
    # Definir período para teste (último mês completo)
    end_date = datetime.today().replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    month = start_date.month
    year = start_date.year
    
    logger.info(f"Período de teste: {start_date_str} a {end_date_str}")
    
    # Criar arquivo de template HTML para teste
    template_path = 'templates/test_template.html'
    
    with open('test_in.py', 'r') as f:
        script_exists = True
    
    if script_exists:
        logger.info("Verificando existência do template HTML...")
        
        if not os.path.exists(template_path):
            logger.info("Template HTML não encontrado. Criando template de teste...")
            
            # Aqui você deve incluir o conteúdo do template HTML
            # que foi fornecido anteriormente no main.py
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Mensal - {{client_name}} - {{month_name}} {{year}}</title>
    <style>
        /* Estilos CSS do template */
        /* Definindo variáveis com as cores da marca */
        :root {
            --primary: #111218;
            --secondary: #935FA7;
            --light: #FDF7FA;
            --accent: #F2C354;
            --chart-accent1: #FF6B6C;
            --chart-accent2: #A1E8CC;
        }
        
        /* ... (aqui viriam todos os estilos do template) ... */
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Helvetica', 'Arial', sans-serif;
        }
        
        body {
            font-size: 14px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Template simplificado para teste -->
        <h1>Relatório Mensal - {{client_name}} - {{month_name}} {{year}}</h1>
        
        <!-- Dados básicos -->
        <div>Visitas: {{sessions}}</div>
        <div>Usuários: {{users}}</div>
        <div>Impressões: {{impressions}}</div>
        <div>Cliques: {{clicks}}</div>
        
        <!-- Gráficos -->
        <div>{{trend_chart}}</div>
        <div>{{devices_chart}}</div>
        <div>{{traffic_sources_chart}}</div>
        <div>{{search_performance_chart}}</div>
        
        <!-- Tabelas -->
        <h2>Páginas mais visitadas</h2>
        <div>{{top_pages_rows}}</div>
        
        <h2>Palavras-chave</h2>
        <div>{{top_queries_rows}}</div>
        
        <!-- Resumo -->
        <h2>Resumo</h2>
        <div>{{monthly_summary}}</div>
        
        <h2>Insights</h2>
        <div>{{insights_list}}</div>
    </div>
</body>
</html>""")
        
        # Carregar configuração de cliente de teste
        logger.info("Carregando configuração de cliente de teste...")
        with open('config/clients.json', 'r') as f:
            clients_config = json.load(f)
        
        # Usar o primeiro cliente para teste
        client = clients_config['clients'][0]
        logger.info(f"Cliente de teste: {client['name']}")
        
        try:
            # 1. Extrair dados do Analytics
            logger.info("Extraindo dados do Google Analytics...")
            analytics_data = analytics_module.get_analytics_data(
                client['analytics']['property_id'], 
                start_date_str, 
                end_date_str
            )
            logger.info("✅ Dados do Analytics extraídos com sucesso!")
            
            # Dados do mês anterior
            logger.info("Extraindo dados do Google Analytics do mês anterior...")
            prev_analytics_data = analytics_module.get_previous_month_data(
                client['analytics']['property_id'],
                start_date_str,
                end_date_str
            )
            logger.info("✅ Dados do Analytics do mês anterior extraídos com sucesso!")
            
            # Dados anuais
            logger.info("Extraindo dados anuais do Google Analytics...")
            annual_analytics_data = analytics_module.get_annual_data(
                client['analytics']['property_id'],
                end_date_str
            )
            logger.info("✅ Dados anuais do Analytics extraídos com sucesso!")
            
            # 2. Extrair dados do Search Console
            logger.info("Extraindo dados do Search Console...")
            search_console_data = search_console_module.get_search_console_data(
                client['search_console']['site_url'], 
                start_date_str, 
                end_date_str
            )
            logger.info("✅ Dados do Search Console extraídos com sucesso!")
            
            # Dados do mês anterior
            logger.info("Extraindo dados do Search Console do mês anterior...")
            prev_search_console_data = search_console_module.get_previous_month_data(
                client['search_console']['site_url'],
                start_date_str,
                end_date_str
            )
            logger.info("✅ Dados do Search Console do mês anterior extraídos com sucesso!")
            
            # 3. Gerar relatório HTML
            logger.info("Gerando relatório HTML...")
            report_generator = ModernReportGenerator(
                client,
                template_path,
                month,
                year,
                client['report_config'].get('language', 'pt-BR')
            )
            
            # Adicionar dados ao relatório
            report_generator.add_data('analytics', analytics_data)
            report_generator.add_data('search_console', search_console_data)
            
            # Adicionar dados do mês anterior para comparação
            report_generator.add_previous_month_data(prev_analytics_data, prev_search_console_data)
            
            # Adicionar dados anuais para destaques
            report_generator.add_annual_data(annual_analytics_data, None)
            
            # Gerar HTML
            html_content = report_generator.generate_html()
            
            # Salvar HTML para verificação
            html_output_path = 'test_results/test_report.html'
            with open(html_output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"✅ HTML gerado e salvo em: {html_output_path}")
            
            # 4. Gerar PDF
            logger.info("Gerando relatório PDF...")
            pdf_buffer = report_generator.generate_pdf()
            
            # Salvar PDF localmente para verificação
            pdf_output_path = 'test_results/test_report.pdf'
            with open(pdf_output_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            logger.info(f"✅ PDF gerado e salvo em: {pdf_output_path}")
            
            # 5. Testar upload para Cloud Storage (opcional)
            logger.info("Testando upload para Cloud Storage...")
            try:
                pdf_buffer.seek(0)
                # Importe a função upload_report diretamente
                from modules.report_generator import upload_report
                report_url = upload_report(
                    pdf_buffer, 
                    client['id'], 
                    year, 
                    month,
                    bucket_name='monthly-digest-reports'
                )
                logger.info(f"✅ Relatório enviado para: {report_url}")
            except Exception as e:
                logger.error(f"❌ Erro ao fazer upload do relatório: {str(e)}")
                logger.info("Continuando teste sem upload para Cloud Storage...")
            
            logger.info("Teste de integração concluído com sucesso! ✅")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante o teste de integração: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

if __name__ == "__main__":
    test_integration()