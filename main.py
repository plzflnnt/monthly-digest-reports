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
        
        # Criar arquivo de template HTML (na produção, este arquivo já existiria)
        template_path = os.path.join(template_dir, 'report_template.html')
        
        # Verifique se o template existe, caso contrário, crie-o
        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                # Aqui colocamos o HTML do template que criamos anteriormente
                f.write("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Mensal - {{client_name}} - {{month_name}} {{year}}</title>
    <style>
        /* Definindo variáveis com as cores da marca */
        :root {
            --primary: #111218;
            --secondary: #935FA7;
            --light: #FDF7FA;
            --accent: #F2C354;
            --chart-accent1: #FF6B6C;
            --chart-accent2: #A1E8CC;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Helvetica', 'Arial', sans-serif;
        }
        
        body {
            background-color: var(--light);
            color: var(--primary);
            font-size: 14px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Cabeçalho do Relatório */
        .report-header {
            padding: 25px 15px;
            background-color: var(--primary);
            color: white;
            text-align: center;
            border-radius: 8px 8px 0 0;
            margin-bottom: 30px;
            position: relative;
        }
        
        .report-header .logo {
            max-width: 220px;
            margin-bottom: 15px;
        }
        
        .report-header h1 {
            font-size: 28px;
            font-weight: normal;
            margin-bottom: 10px;
        }
        
        .report-header p {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .report-header .period {
            background-color: var(--accent);
            color: var(--primary);
            border-radius: 20px;
            padding: 5px 15px;
            font-weight: bold;
            display: inline-block;
            margin-top: 10px;
        }
        
        /* Cartões de Destaque */
        .highlight-cards {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 40px;
            justify-content: space-between;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            flex: 1;
            min-width: 230px;
            position: relative;
            overflow: hidden;
        }
        
        .card h3 {
            font-size: 15px;
            color: var(--secondary);
            margin-bottom: 8px;
        }
        
        .card .value {
            font-size: 28px;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 5px;
        }
        
        .card .change {
            font-size: 14px;
            display: flex;
            align-items: center;
        }
        
        .card .change.positive {
            color: #2ecc71;
        }
        
        .card .change.negative {
            color: #e74c3c;
        }
        
        .card .change-icon {
            margin-right: 5px;
            font-size: 20px;
        }
        
        .card .accent-bg {
            position: absolute;
            top: 0;
            right: 0;
            width: 40px;
            height: 100%;
            background-color: var(--accent);
            opacity: 0.1;
        }
        
        /* Seções do Relatório */
        .report-section {
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        
        .section-header {
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        
        .section-header .icon {
            width: 40px;
            height: 40px;
            background-color: var(--secondary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            color: white;
            font-size: 18px;
        }
        
        .section-header h2 {
            font-size: 22px;
            font-weight: 600;
        }
        
        /* Gráficos */
        .chart-container {
            margin: 20px 0;
            height: 300px;
        }
        
        .small-chart {
            height: 250px;
        }
        
        .chart-row {
            display: flex;
            gap: 25px;
            margin-bottom: 25px;
        }
        
        .chart-col {
            flex: 1;
        }
        
        /* Tabelas */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .data-table th, .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .data-table th {
            background-color: #f9f9f9;
            color: var(--primary);
            font-weight: 600;
        }
        
        .data-table tr:last-child td {
            border-bottom: none;
        }
        
        .data-table .rank {
            width: 40px;
            height: 25px;
            background-color: var(--primary);
            color: white;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
        }
        
        .data-table tr:nth-child(1) .rank {
            background-color: var(--accent);
        }
        
        /* Seção de Resumo */
        .summary-box {
            background-color: #f9f9f9;
            border-left: 4px solid var(--secondary);
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }
        
        .summary-box h3 {
            font-size: 16px;
            margin-bottom: 8px;
            color: var(--secondary);
        }
        
        .summary-box p {
            font-size: 14px;
            line-height: 1.6;
        }
        
        /* Rodapé do relatório */
        .report-footer {
            text-align: center;
            padding: 30px 0;
            color: var(--primary);
            font-size: 13px;
            opacity: 0.8;
        }
        
        /* Ícones e indicadores */
        .indicator {
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 13px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .indicator.good {
            background-color: rgba(161, 232, 204, 0.2);  /* var(--chart-accent2) com opacidade */
            color: #2ecc71;
        }
        
        .indicator.medium {
            background-color: rgba(242, 195, 84, 0.2);  /* var(--accent) com opacidade */
            color: #f39c12;
        }
        
        .indicator.poor {
            background-color: rgba(255, 107, 108, 0.2);  /* var(--chart-accent1) com opacidade */
            color: #e74c3c;
        }
        
        /* Explicações */
        .explanation-box {
            background-color: rgba(147, 95, 167, 0.05);  /* var(--secondary) com opacidade */
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .explanation-title {
            font-weight: 600;
            color: var(--secondary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }
        
        .explanation-title span {
            margin-right: 8px;
        }
        
        /* Grid layout para cards menores */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        
        .small-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
            border-top: 3px solid var(--secondary);
        }
        
        .small-card h4 {
            font-size: 14px;
            color: var(--primary);
            margin-bottom: 10px;
            opacity: 0.8;
        }
        
        .small-card .value {
            font-size: 22px;
            font-weight: bold;
            color: var(--primary);
        }
        
        /* Barra de progresso para posição */
        .position-bar {
            height: 8px;
            background-color: #eee;
            border-radius: 4px;
            margin: 10px 0;
            overflow: hidden;
        }
        
        .position-bar .fill {
            height: 100%;
            background-color: var(--accent);
            border-radius: 4px;
        }
        
        /* Últimos 12 meses highlight */
        .year-highlight {
            background-color: var(--primary);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
            text-align: center;
        }
        
        .year-highlight h3 {
            font-size: 18px;
            margin-bottom: 10px;
            color: var(--accent);
        }
        
        .year-highlight .counter {
            font-size: 36px;
            font-weight: bold;
            margin: 15px 0;
        }
        
        .year-highlight p {
            font-size: 16px;
            opacity: 0.8;
        }
        
        /* Fonte personalizada para números grandes */
        .big-number {
            font-family: 'Helvetica', 'Arial', sans-serif;
            letter-spacing: -1px;
        }
        
        @page {
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Cabeçalho do relatório -->
        <div class="report-header">
            <img src="{{logo_url}}" alt="Handel Prime" class="logo">
            <h1>Relatório Mensal de Performance Digital</h1>
            <p>Preparado exclusivamente para {{client_name}}</p>
            <div class="period">{{month_name}} {{year}}</div>
        </div>
        
        <!-- Cartões de destaque (métricas principais) -->
        <div class="highlight-cards">
            <div class="card">
                <div class="accent-bg"></div>
                <h3>Visitas Totais</h3>
                <div class="value big-number">{{sessions}}</div>
                <div class="change {{sessions_change_class}}">
                    <span class="change-icon">{{sessions_change_icon}}</span>
                    {{sessions_change}}% em relação ao mês anterior
                </div>
            </div>
            
            <div class="card">
                <div class="accent-bg"></div>
                <h3>Usuários Únicos</h3>
                <div class="value big-number">{{users}}</div>
                <div class="change {{users_change_class}}">
                    <span class="change-icon">{{users_change_icon}}</span>
                    {{users_change}}% em relação ao mês anterior
                </div>
            </div>
            
            <div class="card">
                <div class="accent-bg"></div>
                <h3>Impressões (Google)</h3>
                <div class="value big-number">{{impressions}}</div>
                <div class="change {{impressions_change_class}}">
                    <span class="change-icon">{{impressions_change_icon}}</span>
                    {{impressions_change}}% em relação ao mês anterior
                </div>
            </div>
            
            <div class="card">
                <div class="accent-bg"></div>
                <h3>Cliques (Google)</h3>
                <div class="value big-number">{{clicks}}</div>
                <div class="change {{clicks_change_class}}">
                    <span class="change-icon">{{clicks_change_icon}}</span>
                    {{clicks_change}}% em relação ao mês anterior
                </div>
            </div>
        </div>
        
        <!-- Seção 1: Visão Geral do Site -->
        <div class="report-section">
            <div class="section-header">
                <div class="icon">📊</div>
                <h2>Visão Geral do Site</h2>
            </div>
            
            <p>
                Este mês, seu site alcançou <strong>{{sessions}} visitas</strong> e <strong>{{users}} usuários únicos</strong>. 
                Aqui está uma análise de como seu site tem performado ao longo do mês.
            </p>
            
            <!-- Gráfico de tendência visitas/usuários -->
            <div class="chart-container" id="trend-chart">
                {{trend_chart}}
            </div>
            
            <div class="metrics-grid">
                <div class="small-card">
                    <h4>Tempo Médio no Site</h4>
                    <div class="value">{{avg_session_duration}}</div>
                </div>
                
                <div class="small-card">
                    <h4>Taxa de Rejeição</h4>
                    <div class="value">{{bounce_rate}}%</div>
                </div>
                
                <div class="small-card">
                    <h4>Páginas por Sessão</h4>
                    <div class="value">{{pages_per_session}}</div>
                </div>
                
                <div class="small-card">
                    <h4>Taxa de Conversão</h4>
                    <div class="value">{{conversion_rate}}%</div>
                </div>
            </div>
            
            <!-- Destaque dos últimos 12 meses -->
            <div class="year-highlight">
                <h3>TOTAL DOS ÚLTIMOS 12 MESES</h3>
                <div class="counter big-number">{{annual_visits}}</div>
                <p>visitas ao seu site no último ano</p>
            </div>
        </div>
        
        <!-- Seção 2: Dispositivos e Comportamento -->
        <div class="report-section">
            <div class="section-header">
                <div class="icon">📱</div>
                <h2>Dispositivos e Comportamento</h2>
            </div>
            
            <p>
                Entender como seus visitantes acessam seu site é fundamental para otimizar a experiência do usuário.
                Veja como está a distribuição do tráfego entre dispositivos móveis e desktop:
            </p>
            
            <div class="chart-row">
                <div class="chart-col">
                    <div class="chart-container small-chart" id="devices-chart">
                        {{devices_chart}}
                    </div>
                </div>
                <div class="chart-col">
                    <div class="summary-box">
                        <h3>O que isso significa?</h3>
                        <p>
                            {{device_insight}}
                        </p>
                    </div>
                    
                    <div class="metrics-grid">
                        <div class="small-card">
                            <h4>Tempo (Mobile)</h4>
                            <div class="value">{{mobile_avg_time}}</div>
                        </div>
                        
                        <div class="small-card">
                            <h4>Tempo (Desktop)</h4>
                            <div class="value">{{desktop_avg_time}}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Seção 3: Páginas Mais Visitadas -->
        <div class="report-section">
            <div class="section-header">
                <div class="icon">📄</div>
                <h2>Páginas Mais Visitadas</h2>
            </div>
            
            <p>
                Aqui estão as páginas que receberam mais visitas em seu site durante este mês:
            </p>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Página</th>
                        <th>Visualizações</th>
                        <th>Tempo Médio</th>
                    </tr>
                </thead>
                <tbody>
                    {{top_pages_rows}}
                </tbody>
            </table>
            
            <!-- Destaque dos últimos 12 meses para página principal -->
            <div class="year-highlight">
                <h3>PÁGINA MAIS VISITADA NO ANO</h3>
                <div class="counter">{{top_page_annual}}</div>
                <p>visualizações na página principal no último ano</p>
            </div>
        </div>
        
        <!-- Seção 4: Fontes de Tráfego -->
        <div class="report-section">
            <div class="section-header">
                <div class="icon">🔍</div>
                <h2>Fontes de Tráfego</h2>
            </div>
            
            <p>
                De onde vêm seus visitantes? Esta análise mostra as principais fontes de tráfego para seu site:
            </p>
            
            <div class="chart-container" id="traffic-sources-chart">
                {{traffic_sources_chart}}
            </div>
            
            <div class="explanation-box">
                <div class="explanation-title">
                    <span>💡</span> O que significam essas fontes?
                </div>
                <p>
                    <strong>Orgânico:</strong> Visitantes que chegaram através de buscas no Google e outros buscadores.<br>
                    <strong>Direto:</strong> Pessoas que digitaram seu endereço diretamente ou usaram favoritos.<br>
                    <strong>Referência:</strong> Visitas vindas de links em outros sites.<br>
                    <strong>Social:</strong> Tráfego vindo de redes sociais como Facebook, Instagram, etc.<br>
                    <strong>Email:</strong> Visitantes que clicaram em links em emails enviados.
                </p>
            </div>
        </div>
        
        <!-- Seção 5: Desempenho no Google -->
        <div class="report-section">
            <div class="section-header">
                <div class="icon">🔎</div>
                <h2>Desempenho no Google</h2>
            </div>
            
            <p>
                Seu site apareceu <strong>{{impressions}} vezes</strong> nos resultados de busca do Google este mês, 
                gerando <strong>{{clicks}} cliques</strong> para seu site. Vamos analisar este desempenho:
            </p>
            
            <div class="chart-container" id="search-performance-chart">
                {{search_performance_chart}}
            </div>
            
            <div class="metrics-grid">
                <div class="small-card">
                    <h4>CTR Médio</h4>
                    <div class="value">{{ctr}}%</div>
                </div>
                
                <div class="small-card">
                    <h4>Posição Média</h4>
                    <div class="value">{{avg_position}}</div>
                    <div class="position-bar">
                        <div class="fill" style="width: {{position_percentage}}%;"></div>
                    </div>
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">Palavras-chave Principais</h3>
            <p>Estas são as consultas que trouxeram mais tráfego do Google para seu site:</p>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Palavra-chave</th>
                        <th>Cliques</th>
                        <th>Impressões</th>
                        <th>Posição</th>
                    </tr>
                </thead>
                <tbody>
                    {{top_queries_rows}}
                </tbody>
            </table>
            
            <h3 style="margin-top: 30px;">Páginas com Melhor Desempenho no Google</h3>
            <p>Estas são as páginas do seu site com melhor desempenho nas buscas:</p>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Página</th>
                        <th>Cliques</th>
                        <th>Impressões</th>
                        <th>CTR</th>
                    </tr>
                </thead>
                <tbody>
                    {{top_search_pages_rows}}
                </tbody>
            </table>
        </div>

        <!-- Seção 6: Resumo e Recomendações -->
        <div class="report-section">
            <div class="section-header">
                <div class="icon">📝</div>
                <h2>Resumo e Insights</h2>
            </div>
            
            <div class="summary-box">
                <h3>Resumo do Mês</h3>
                <p>
                    {{monthly_summary}}
                </p>
            </div>
            
            <h3 style="margin-top: 25px;">Principais Insights</h3>
            <ul style="margin: 15px 0; padding-left: 20px;">
                {{insights_list}}
            </ul>
        </div>
        
        <!-- Rodapé do relatório -->
        <div class="report-footer">
            <p>Relatório gerado em {{generation_date}} • Handel Prime • https://handelprime.com.br</p>
        </div>
    </div>
</body>
</html>""")
        
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
                logger.info(f"Gerando relatório PDF...")
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
                
                # Gerar PDF
                pdf_buffer = report.generate_pdf()
                
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