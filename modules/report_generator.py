import json
import os
from datetime import datetime
import io
from google.cloud import storage
import pandas as pd
import numpy as np
import jinja2
from weasyprint import HTML, CSS
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from utils.data_processing import calculate_growth, format_number, format_percentage

# Importar o módulo de geração de gráficos (deve ficar fora da classe)
from modules.chart_generator import (
    create_trend_chart,
    create_devices_chart, 
    create_traffic_sources_chart,
    create_search_performance_chart,
    get_empty_chart_image
)

class ModernReportGenerator:
    def _prepare_time_series_data(self, data_list, date_field='date', value_fields=None):
        """
        Prepara dados de séries temporais para gráficos, tratando corretamente as datas.
        """
        import pandas as pd

        if not data_list or not value_fields:
            return None

        # Criar DataFrame
        df = pd.DataFrame(data_list)

        # Verificar se o campo de data existe
        if date_field not in df.columns:
            return None

        # As datas já estão no formato YYYY-MM-DD, 
        # então não precisamos fazer conversão de formato
        # Apenas converter para datetime
        try:
            df[date_field] = pd.to_datetime(df[date_field])

            # Ordenar por data
            df = df.sort_values(date_field)

            # Selecionar apenas as colunas necessárias
            columns_to_keep = [date_field] + value_fields
            df = df[columns_to_keep]

            return df
        except Exception as e:
            import logging
            logging.error(f"Erro ao preparar dados de série temporal: {str(e)}")
            return None
        

    def __init__(self, client_config, template_path, month, year, language='pt-BR'):
        """
        Inicializa o gerador de relatórios moderno.
        """
        self.client = client_config
        self.month = month
        self.year = year
        self.language = language
        self.report_data = {}
        
        # Configurações para os meses em português
        self.month_names = {
            'pt-BR': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        }
        
        # Carrega o template HTML
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template_source = f.read()
        
        # Configurar o ambiente Jinja2
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(template_path))
        )
        self.template = self.jinja_env.from_string(self.template_source)
        
        # Gerar dados do mês anterior para comparação
        self.prev_month_data = None
        
        # Dados anuais para destaque
        self.annual_data = None

        # Adicionar um dicionário para armazenar os buffers de imagens
        self.chart_buffers = {}
    
    def add_data(self, source, data):
        """Adiciona dados ao relatório."""
        self.report_data[source] = data
    
    def add_previous_month_data(self, analytics_data, search_console_data):
        """Adiciona dados do mês anterior para comparação."""
        self.prev_month_data = {
            'analytics': analytics_data,
            'search_console': search_console_data
        }
    
    def add_annual_data(self, analytics_data, search_console_data):
        """Adiciona dados anuais para destaque."""
        self.annual_data = {
            'analytics': analytics_data,
            'search_console': search_console_data
        }
    
    def _generate_device_insight(self, devices):
        """Gera uma análise sobre o uso de dispositivos."""
        if not devices:
            return "Não há dados suficientes para análise de dispositivos."

        # Converter valores para inteiros (caso sejam strings)
        devices_int = {k: int(v) if isinstance(v, str) else v for k, v in devices.items()}

        # Calcular porcentagens
        total = sum(devices_int.values())
        if total == 0:
            return "Não há dados suficientes para análise de dispositivos."

        percentages = {k: (float(v) / total) * 100 for k, v in devices_int.items()}

        # Verificar qual dispositivo é predominante
        if 'mobile' in percentages and percentages.get('mobile', 0) > 60:
            return ("A maioria dos seus visitantes usa dispositivos móveis. Certifique-se de que seu site "
                   "esteja otimizado para celulares, com botões de fácil acesso e carregamento rápido "
                   "para melhorar a experiência desses usuários.")
        elif 'desktop' in percentages and percentages.get('desktop', 0) > 60:
            return ("A maioria dos seus visitantes usa computadores desktop. Isso pode indicar um público "
                   "mais corporativo ou que acessa seu site durante o horário de trabalho. Considere otimizar "
                   "o conteúdo para telas maiores e experiências mais completas.")
        else:
            return ("Seu tráfego está bem distribuído entre diferentes dispositivos. Mantenha um design "
                   "responsivo que funcione bem em qualquer tamanho de tela para garantir uma boa "
                   "experiência para todos os usuários.")
    
    def _generate_monthly_summary(self, analytics_data, search_console_data):
        """Gera um resumo mensal com base nos dados disponíveis."""
        # Verificar se há dados para comparação
        has_prev_data = self.prev_month_data is not None

        summary_parts = []

        # Analisar visitas e usuários
        if 'basic_metrics' in analytics_data:
            basic_metrics = analytics_data.get('basic_metrics', {})

            # Verificar se as chaves existem antes de acessá-las
            if 'sessions' in basic_metrics and 'total_users' in basic_metrics:
                sessions = int(basic_metrics['sessions'])
                users = int(basic_metrics['total_users'])

                if has_prev_data and 'analytics' in self.prev_month_data:
                    prev_sessions = int(self.prev_month_data['analytics']['basic_metrics']['sessions'])
                    prev_users = int(self.prev_month_data['analytics']['basic_metrics']['total_users'])

                    sessions_growth = calculate_growth(sessions, prev_sessions)
                    users_growth = calculate_growth(users, prev_users)

                    if sessions_growth > 10:
                        summary_parts.append(f"Seu site teve um crescimento expressivo de {sessions_growth:.1f}% nas visitas em relação ao mês anterior.")
                    elif sessions_growth > 0:
                        summary_parts.append(f"As visitas ao seu site aumentaram {sessions_growth:.1f}% em comparação com o mês passado.")
                    elif sessions_growth < -10:
                        summary_parts.append(f"Houve uma redução significativa de {abs(sessions_growth):.1f}% nas visitas em relação ao mês anterior.")
                    else:
                        summary_parts.append("O número de visitas se manteve estável em relação ao mês anterior.")
                else:
                    summary_parts.append(f"Seu site recebeu {sessions} visitas e {users} usuários únicos neste mês.")

            else:
                # Valor padrão caso as chaves não existam
                sessions = 0
                users = 0
                summary_parts.append(f"Seu site recebeu aproximadamente {sessions} visitas e {users} usuários únicos neste mês.") 

        # Analisar desempenho no Google
        if 'total_impressions' in search_console_data:
            impressions = int(search_console_data['total_impressions'])
            clicks = int(search_console_data['total_clicks'])
            ctr = float(search_console_data['avg_ctr']) * 100
            position = float(search_console_data['avg_position'])

            if has_prev_data and 'search_console' in self.prev_month_data:
                prev_impressions = int(self.prev_month_data['search_console']['total_impressions'])
                prev_clicks = int(self.prev_month_data['search_console']['total_clicks'])

                impressions_growth = calculate_growth(impressions, prev_impressions)
                clicks_growth = calculate_growth(clicks, prev_clicks)

                if impressions_growth > 0 and clicks_growth > 0:
                    summary_parts.append(f"A visibilidade nas buscas do Google aumentou, com crescimento de {impressions_growth:.1f}% nas impressões e {clicks_growth:.1f}% nos cliques.")
                elif impressions_growth > 0 and clicks_growth <= 0:
                    summary_parts.append(f"Apesar do aumento de {impressions_growth:.1f}% nas impressões no Google, os cliques diminuíram {abs(clicks_growth):.1f}%.")
                elif impressions_growth <= 0 and clicks_growth > 0:
                    summary_parts.append(f"Mesmo com redução nas impressões, seu site conseguiu {clicks_growth:.1f}% mais cliques do Google.")
                else:
                    summary_parts.append(f"Houve redução de {abs(impressions_growth):.1f}% nas impressões e {abs(clicks_growth):.1f}% nos cliques vindos do Google.")
            else:
                if position < 10:
                    summary_parts.append(f"Seu site apareceu em média na posição {position:.1f} nos resultados de busca, gerando {impressions} impressões e {clicks} cliques.")
                else:
                    summary_parts.append(f"Seu site recebeu {clicks} cliques a partir de {impressions} impressões no Google, com uma taxa de cliques de {ctr:.1f}%.")

        # Analisar fontes de tráfego
        if 'traffic_sources' in analytics_data:
            sources = {}
            for source in analytics_data['traffic_sources'][:3]:
                medium = source['medium']
                # Simplifica as fontes 
                if medium == 'organic':
                    category = 'buscadores orgânicos'
                elif medium == 'referral':
                    category = 'sites que apontam para o seu'
                elif medium == 'social':
                    category = 'redes sociais'
                elif medium == 'email':
                    category = 'campanhas de email'
                elif medium == '(none)' or medium == 'direct':
                    category = 'tráfego direto'
                else:
                    category = medium

                # Garantir que o valor seja inteiro
                session_value = int(source['sessions']) if isinstance(source['sessions'], str) else source['sessions']
                sources[category] = session_value

            if sources:
                top_source = max(sources.items(), key=lambda x: x[1])
                summary_parts.append(f"A principal fonte de visitas foi {top_source[0]}, responsável por {top_source[1]} sessões.")

        # Combinar tudo em um parágrafo coeso
        if summary_parts:
            return " ".join(summary_parts)
        else:
            return "Não há dados suficientes para gerar um resumo detalhado para este mês."
    
    def _generate_insights(self, analytics_data, search_console_data):
        """Gera insights baseados nos dados."""
        insights = []

        # Verificar dados de dispositivos
        if 'devices' in analytics_data:
            devices = analytics_data['devices']
            # Converter valores para inteiros (caso sejam strings)
            devices_int = {k: int(v) if isinstance(v, str) else v for k, v in devices.items()}

            total = sum(devices_int.values())

            if total > 0:  # Evitar divisão por zero
                if 'mobile' in devices_int and (devices_int['mobile'] / total) > 0.6:
                    insights.append("O tráfego móvel representa mais de 60% das visitas. Considere revisar a experiência em dispositivos móveis e adicionar recursos específicos para esses usuários.")

                if 'desktop' in devices_int and 'mobile' in devices_int:
                    desktop_pct = devices_int['desktop'] / total
                    mobile_pct = devices_int['mobile'] / total

                    if abs(desktop_pct - mobile_pct) < 0.1:  # Diferença menor que 10%
                        insights.append("Seu site tem uma distribuição equilibrada entre desktop e mobile. Continue mantendo uma experiência consistente em ambas as plataformas.")

        # Verificar taxa de rejeição
        if 'basic_metrics' in analytics_data and 'bounce_rate' in analytics_data['basic_metrics']:
            bounce_rate = float(analytics_data['basic_metrics']['bounce_rate'])

            if bounce_rate > 70:
                insights.append("A taxa de rejeição está acima de 70%. Considere melhorar o conteúdo inicial ou adicionar elementos que incentivem o visitante a navegar mais pelo site.")
            elif bounce_rate < 40:
                insights.append("A taxa de rejeição está abaixo de 40%, o que é excelente! Os visitantes estão engajados com seu conteúdo.")

        # Verificar posição média nas buscas
        if 'avg_position' in search_console_data:
            position = float(search_console_data['avg_position'])

            if position <= 10:
                insights.append(f"Seu site aparece em média na posição {position:.1f} nas buscas, o que é excelente! Continue otimizando seu conteúdo para manter essas posições.")
            elif position > 20:
                insights.append(f"A posição média nas buscas é {position:.1f}, o que significa que seu site geralmente não aparece na primeira página. Considere uma estratégia de SEO para melhorar o posicionamento.")

        # Verificar CTR
        if 'avg_ctr' in search_console_data:
            ctr = float(search_console_data['avg_ctr']) * 100

            if ctr < 1.5:
                insights.append(f"A taxa de cliques (CTR) de {ctr:.1f}% está abaixo da média. Considere revisar os títulos e descrições das suas páginas para torná-los mais atrativos.")
            elif ctr > 4:
                insights.append(f"A taxa de cliques (CTR) de {ctr:.1f}% está acima da média, o que indica que seus títulos e descrições são eficazes.")

        # Verificar tempo médio no site
        if 'basic_metrics' in analytics_data and 'avg_session_duration' in analytics_data['basic_metrics']:
            duration = analytics_data['basic_metrics']['avg_session_duration']
            duration_seconds = float(duration)

            if duration_seconds < 60:
                insights.append(f"O tempo médio de sessão é de apenas {duration_seconds:.0f} segundos. Considere adicionar mais conteúdo relevante para aumentar o engajamento.")
            elif duration_seconds > 180:
                insights.append(f"Os visitantes passam em média mais de 3 minutos no seu site, o que indica um bom nível de engajamento com o conteúdo.")

        # Verificar crescimento
        if self.prev_month_data and 'analytics' in self.prev_month_data:
            current_sessions = int(analytics_data['basic_metrics']['sessions'])
            prev_sessions = int(self.prev_month_data['analytics']['basic_metrics']['sessions'])

            growth = calculate_growth(current_sessions, prev_sessions)

            if growth > 20:
                insights.append(f"Crescimento impressionante de {growth:.1f}% nas visitas! Analise quais ações podem ter contribuído para este resultado.")
            elif growth < -20:
                insights.append(f"Redução significativa de {abs(growth):.1f}% nas visitas. Verifique se houve mudanças recentes no site ou em estratégias de marketing.")

        # Formatar lista de insights
        formatted_insights = ""
        for insight in insights:
            formatted_insights += f"<li>{insight}</li>\n"

        return formatted_insights
    
    def generate_html(self):
        """Gera o HTML do relatório."""
        # Obter dados de analytics e search console
        analytics_data = self.report_data.get('analytics', {})
        search_console_data = self.report_data.get('search_console', {})
        
        # Preparar dados para o template
        month_name = self.month_names.get(self.language, [])[self.month - 1]
        
        # Processar métricas básicas
        basic_metrics = analytics_data.get('basic_metrics', {})
        sessions = format_number(int(basic_metrics.get('sessions', 0)))
        users = format_number(int(basic_metrics.get('total_users', 0)))
        
        # Calcular mudanças em relação ao mês anterior
        sessions_change = 0
        users_change = 0
        impressions_change = 0
        clicks_change = 0
        
        if self.prev_month_data:
            prev_analytics = self.prev_month_data.get('analytics', {})
            prev_search = self.prev_month_data.get('search_console', {})
            
            prev_basic = prev_analytics.get('basic_metrics', {})
            
            # Calcular mudanças
            sessions_change = calculate_growth(
                int(basic_metrics.get('sessions', 0)),
                int(prev_basic.get('sessions', 0))
            )
            
            users_change = calculate_growth(
                int(basic_metrics.get('total_users', 0)),
                int(prev_basic.get('total_users', 0))
            )
            
            impressions_change = calculate_growth(
                int(search_console_data.get('total_impressions', 0)),
                int(prev_search.get('total_impressions', 0))
            )
            
            clicks_change = calculate_growth(
                int(search_console_data.get('total_clicks', 0)),
                int(prev_search.get('total_clicks', 0))
            )
        
        # Preparar classes para indicadores de crescimento
        sessions_change_class = "positive" if sessions_change >= 0 else "negative"
        users_change_class = "positive" if users_change >= 0 else "negative"
        impressions_change_class = "positive" if impressions_change >= 0 else "negative"
        clicks_change_class = "positive" if clicks_change >= 0 else "negative"
        
        # Preparar ícones para indicadores de crescimento
        sessions_change_icon = "↑" if sessions_change >= 0 else "↓"
        users_change_icon = "↑" if users_change >= 0 else "↓"
        impressions_change_icon = "↑" if impressions_change >= 0 else "↓"
        clicks_change_icon = "↑" if clicks_change >= 0 else "↓"
        
        # Formatar mudanças como números absolutos
        sessions_change = abs(sessions_change)
        users_change = abs(users_change)
        impressions_change = abs(impressions_change)
        clicks_change = abs(clicks_change)
        
        # Processar dados do Search Console
        impressions = format_number(int(search_console_data.get('total_impressions', 0)))
        clicks = format_number(int(search_console_data.get('total_clicks', 0)))
        ctr = format_number(float(search_console_data.get('avg_ctr', 0)) * 100, 1)
        avg_position = format_number(float(search_console_data.get('avg_position', 0)), 1)
        
        # Calcular porcentagem para a barra de posição (1 é ótimo, 50 é ruim)
        position_value = float(search_console_data.get('avg_position', 50))
        position_percentage = max(0, min(100, 100 - ((position_value - 1) * 2)))
        
        # Processar tempo médio no site
        avg_session_duration = basic_metrics.get('avg_session_duration', 0)
        minutes = int(float(avg_session_duration) // 60)
        seconds = int(float(avg_session_duration) % 60)
        avg_session_duration_formatted = f"{minutes}m {seconds}s"
        
        # Calcular taxa de rejeição e páginas por sessão
        bounce_rate = format_number(float(basic_metrics.get('bounce_rate', 0)) * 100, 1)
        pages_per_session = format_number(float(basic_metrics.get('pages_per_session', 0)), 1)
        
        # Calcular taxa de conversão (se disponível)
        conversion_rate = format_number(float(basic_metrics.get('conversion_rate', 0)) * 100, 2)
        
        # Processar dispositivos
        devices = analytics_data.get('devices', {})
        device_insight = self._generate_device_insight(devices)
        
        # Tempo médio por dispositivo
        mobile_avg_time = "N/A"
        desktop_avg_time = "N/A"
        
        if 'devices_metrics' in analytics_data:
            device_metrics = analytics_data.get('devices_metrics', {})
            
            if 'mobile' in device_metrics:
                mobile_seconds = float(device_metrics['mobile'].get('avg_time', 0))
                mobile_minutes = int(mobile_seconds // 60)
                mobile_secs = int(mobile_seconds % 60)
                mobile_avg_time = f"{mobile_minutes}m {mobile_secs}s"
            
            if 'desktop' in device_metrics:
                desktop_seconds = float(device_metrics['desktop'].get('avg_time', 0))
                desktop_minutes = int(desktop_seconds // 60)
                desktop_secs = int(desktop_seconds % 60)
                desktop_avg_time = f"{desktop_minutes}m {desktop_secs}s"
        
        # Processar páginas mais visitadas
        top_pages_rows = ""
        if 'top_pages' in analytics_data:
            for i, page in enumerate(analytics_data['top_pages'][:5], 1):
                title = page.get('title', 'Página sem título')
                path = page.get('path', '/')
                
                # Limitar tamanho do título
                if len(title) > 40:
                    title = title[:37] + "..."
                
                views = format_number(int(page.get('views', 0)))
                
                # Tempo na página
                page_time = page.get('time', 0)
                page_time_min = int(float(page_time) // 60)
                page_time_sec = int(float(page_time) % 60)
                page_time_formatted = f"{page_time_min}m {page_time_sec}s"
                
                top_pages_rows += f"""
                <tr>
                    <td><div class="rank">{i}</div></td>
                    <td><strong>{title}</strong><br><small>{path}</small></td>
                    <td>{views}</td>
                    <td>{page_time_formatted}</td>
                </tr>
                """
        
        # Processar consultas principais
        top_queries_rows = ""
        if 'top_queries' in search_console_data:
            for i, query in enumerate(search_console_data['top_queries'][:5], 1):
                query_text = query.get('query', 'Consulta desconhecida')
                
                # Limitar tamanho da consulta
                if len(query_text) > 40:
                    query_text = query_text[:37] + "..."
                
                clicks = format_number(int(query.get('clicks', 0)))
                impressions = format_number(int(query.get('impressions', 0)))
                position = format_number(float(query.get('position', 0)), 1)
                
                top_queries_rows += f"""
                <tr>
                    <td><div class="rank">{i}</div></td>
                    <td><strong>{query_text}</strong></td>
                    <td>{clicks}</td>
                    <td>{impressions}</td>
                    <td>{position}</td>
                </tr>
                """
        
        # Processar páginas com melhor desempenho no Google
        top_search_pages_rows = ""
        if 'top_pages' in search_console_data:
            for i, page in enumerate(search_console_data['top_pages'][:5], 1):
                page_url = page.get('page', 'URL desconhecida')
                
                # Limpar URL
                page_url = page_url.replace(self.client['search_console']['site_url'], '')
                if page_url == "":
                    page_url = "/"
                
                # Limitar tamanho da URL
                if len(page_url) > 40:
                    page_url = page_url[:37] + "..."
                
                clicks = format_number(int(page.get('clicks', 0)))
                impressions = format_number(int(page.get('impressions', 0)))
                page_ctr = format_number(float(page.get('ctr', 0)) * 100, 1)
                
                top_search_pages_rows += f"""
                <tr>
                    <td><div class="rank">{i}</div></td>
                    <td><strong>{page_url}</strong></td>
                    <td>{clicks}</td>
                    <td>{impressions}</td>
                    <td>{page_ctr}%</td>
                </tr>
                """
        
        # Dados anuais para destaque
        annual_visits = "0"
        top_page_annual = "0"
        
        if self.annual_data and 'analytics' in self.annual_data:
            annual_analytics = self.annual_data['analytics']
            if 'year_metrics' in annual_analytics:
                annual_visits = format_number(int(annual_analytics['year_metrics'].get('total_sessions', 0)))
                
                if 'top_pages_year' in annual_analytics and annual_analytics['top_pages_year']:
                    top_page = annual_analytics['top_pages_year'][0]
                    top_page_annual = format_number(int(top_page.get('views', 0)))
        
        # Gerar resumo mensal e insights
        monthly_summary = self._generate_monthly_summary(analytics_data, search_console_data)
        insights_list = self._generate_insights(analytics_data, search_console_data)
        
        # Data de geração do relatório
        generation_date = datetime.now().strftime("%d/%m/%Y")
        
        # URL do logo
        logo_url = "https://handelprime.com.br/wp-content/uploads/2019/02/logo-white-e1600802257248.png"
        
        # Dados para o template
        template_data = {
            'client_name': self.client['name'],
            'month_name': month_name,
            'year': self.year,
            'logo_url': logo_url,
            'sessions': sessions,
            'users': users,
            'impressions': impressions,
            'clicks': clicks,
            'sessions_change': format_number(sessions_change, 1),
            'users_change': format_number(users_change, 1),
            'impressions_change': format_number(impressions_change, 1),
            'clicks_change': format_number(clicks_change, 1),
            'sessions_change_class': sessions_change_class,
            'users_change_class': users_change_class,
            'impressions_change_class': impressions_change_class,
            'clicks_change_class': clicks_change_class,
            'sessions_change_icon': sessions_change_icon,
            'users_change_icon': users_change_icon,
            'impressions_change_icon': impressions_change_icon,
            'clicks_change_icon': clicks_change_icon,
            'avg_session_duration': avg_session_duration_formatted,
            'bounce_rate': bounce_rate,
            'pages_per_session': pages_per_session,
            'conversion_rate': conversion_rate,
            'annual_visits': annual_visits,
            'top_page_annual': top_page_annual,
            'device_insight': device_insight,
            'mobile_avg_time': mobile_avg_time,
            'desktop_avg_time': desktop_avg_time,
            'top_pages_rows': top_pages_rows,
            'top_queries_rows': top_queries_rows,
            'top_search_pages_rows': top_search_pages_rows,
            'ctr': ctr,
            'avg_position': avg_position,
            'position_percentage': position_percentage,
            'monthly_summary': monthly_summary,
            'insights_list': insights_list,
            'generation_date': generation_date,
        }
        
        # Gerar gráficos com fallback automático
        enable_debug = self.client.get('report_config', {}).get('enable_debug', False)

        # Trend chart
        trend_buffer = create_trend_chart(
            analytics_data.get('daily_metrics', []), 
            save_debug=enable_debug
        )
        if not trend_buffer:
            trend_buffer = get_empty_chart_image("Dados insuficientes para gerar o gráfico de tendência")
        self.chart_buffers['trend'] = trend_buffer

        # Devices chart
        devices_buffer = create_devices_chart(
            analytics_data.get('devices', {}), 
            save_debug=enable_debug
        )
        if not devices_buffer:
            devices_buffer = get_empty_chart_image("Dados insuficientes para gerar o gráfico de dispositivos")
        self.chart_buffers['devices'] = devices_buffer

        # Traffic sources chart
        traffic_buffer = create_traffic_sources_chart(
            analytics_data.get('traffic_sources', []), 
            save_debug=enable_debug
        )
        if not traffic_buffer:
            traffic_buffer = get_empty_chart_image("Dados insuficientes para gerar o gráfico de fontes de tráfego")
        self.chart_buffers['traffic'] = traffic_buffer

        # Search performance chart
        search_buffer = create_search_performance_chart(
            search_console_data.get('performance_by_date', []), 
            save_debug=enable_debug
        )
        if not search_buffer:
            search_buffer = get_empty_chart_image("Dados insuficientes para gerar o gráfico de desempenho nas buscas")
        self.chart_buffers['search'] = search_buffer

        # Adicionar gráficos ao template - usar CIDs para referência em e-mail
        template_data['trend_chart'] = '<img src="cid:chart_trend" alt="Gráfico de tendência de visitas e usuários" style="width:100%;height:auto;">'
        template_data['devices_chart'] = '<img src="cid:chart_devices" alt="Distribuição de dispositivos" style="width:100%;height:auto;">'
        template_data['traffic_sources_chart'] = '<img src="cid:chart_traffic" alt="Fontes de tráfego" style="width:100%;height:auto;">'
        template_data['search_performance_chart'] = '<img src="cid:chart_search" alt="Desempenho nas buscas" style="width:100%;height:auto;">'

        # Renderizar o template
        html = self.template.render(**template_data)
        return html
    
    def get_chart_buffers(self):
        """Retorna os buffers de imagens dos gráficos."""
        return self.chart_buffers
    
    def generate_pdf(self):
        """Gera o relatório em PDF."""
        # Gerar HTML
        html = self.generate_html()

        # Criar PDF a partir do HTML
        pdf_buffer = io.BytesIO()

        try:
            # Método 1: Abordagem direta - pode funcionar com algumas versões
            from weasyprint import HTML
            HTML(string=html).write_pdf(pdf_buffer)
        except TypeError as e1:
            try:
                # Método 2: Abordagem com configuração explícita
                from weasyprint import HTML, CSS
                html_doc = HTML(string=html)
                css = CSS(string='@page { margin: 0; }')
                html_doc.write_pdf(pdf_buffer, stylesheets=[css])
            except TypeError as e2:
                try:
                    # Método 3: Usando um arquivo temporário como intermediário
                    import tempfile
                    import os

                    temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
                    try:
                        temp_html.write(html.encode('utf-8'))
                        temp_html.close()

                        from weasyprint import HTML
                        HTML(temp_html.name).write_pdf(pdf_buffer)
                    finally:
                        # Remover arquivo temporário
                        os.unlink(temp_html.name)
                except Exception as e3:
                    logging.error(f"Todos os métodos falharam. Erro final: {e3}")
                    raise RuntimeError(f"Não foi possível gerar o PDF: {e1}, {e2}, {e3}")

        pdf_buffer.seek(0)
        return pdf_buffer
    
    
    @staticmethod
    def upload_report(pdf_buffer, client_id, year, month, bucket_name='monthly-digest-reports'):
        """Faz upload do relatório para o Cloud Storage.

        Args:
            pdf_buffer: Buffer contendo o PDF do relatório
            client_id: ID do cliente
            year: Ano do relatório
            month: Mês do relatório (1-12)
            bucket_name: Nome do bucket do Cloud Storage

        Returns:
            str: URL do relatório no Cloud Storage
        """
        try:
            from google.cloud import storage

            # Garantir que month seja um inteiro
            month_int = month
            if isinstance(month, str) and month.isdigit():
                month_int = int(month)
            elif not isinstance(month, int):
                month_int = datetime.now().month  # Usar mês atual como fallback

            # Garantir que year seja um inteiro
            year_int = year
            if isinstance(year, str) and year.isdigit():
                year_int = int(year)
            elif not isinstance(year, int):
                year_int = datetime.now().year  # Usar ano atual como fallback

            # client_id deve permanecer como string
            client_id_str = str(client_id)

            client = storage.Client()
            bucket = client.bucket(bucket_name)

            # Formatar o nome do arquivo
            filename = f"{client_id_str}/report_{year_int}_{month_int:02d}.pdf"

            # Fazer upload do arquivo
            blob = bucket.blob(filename)
            blob.upload_from_file(pdf_buffer, content_type='application/pdf')

            return f"gs://{bucket_name}/{filename}"
        except Exception as e:
            import logging
            logging.error(f"Erro ao fazer upload do relatório: {str(e)}")
            # Em caso de erro, ainda retornar um URL fictício para não interromper o fluxo
            return f"gs://{bucket_name}/{client_id}/report_{year}_{month:02d}.pdf"