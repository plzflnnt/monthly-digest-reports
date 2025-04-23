from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import logging
from utils.secrets_utils import get_service_account_credentials
from utils.data_processing import calculate_growth

def get_analytics_data(property_id, start_date, end_date):
    """Extrai dados do Google Analytics 4 para o período especificado."""
    try:
        # Obter credenciais com escopo para Analytics
        credentials = get_service_account_credentials(
            ['https://www.googleapis.com/auth/analytics.readonly']
        )
        
        # Construir serviço do Analytics
        analytics = build('analyticsdata', 'v1beta', credentials=credentials)
        
        # Métricas básicas
        basic_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                'metrics': [
                    {'name': 'totalUsers'},
                    {'name': 'sessions'},
                    {'name': 'engagedSessions'},
                    {'name': 'engagementRate'},
                    {'name': 'averageSessionDuration'},
                    {'name': 'screenPageViewsPerSession'},
                    {'name': 'bounceRate'},
                    {'name': 'conversions'}
                ]
            }
        ).execute()
        
        # Obter métricas diárias para gráficos de tendência
        daily_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                'dimensions': [{'name': 'date'}],
                'metrics': [
                    {'name': 'sessions'},
                    {'name': 'totalUsers'},
                    {'name': 'screenPageViews'},
                    {'name': 'conversions'}
                ],
                'orderBys': [{'dimension': {'dimensionName': 'date'}}]
            }
        ).execute()
        
        # Páginas mais visitadas
        pages_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                'dimensions': [{'name': 'pagePath'}, {'name': 'pageTitle'}],
                'metrics': [
                    {'name': 'screenPageViews'},
                    {'name': 'averageSessionDuration'}
                ],
                'limit': 10,
                'orderBys': [{'metric': {'metricName': 'screenPageViews'}, 'desc': True}]
            }
        ).execute()
        
        # Fontes de tráfego
        sources_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                'dimensions': [{'name': 'sessionSource'}, {'name': 'sessionMedium'}],
                'metrics': [{'name': 'sessions'}, {'name': 'conversions'}],
                'limit': 15,
                'orderBys': [{'metric': {'metricName': 'sessions'}, 'desc': True}]
            }
        ).execute()
        
        # Dispositivos
        devices_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                'dimensions': [{'name': 'deviceCategory'}],
                'metrics': [
                    {'name': 'sessions'},
                    {'name': 'screenPageViews'},
                    {'name': 'averageSessionDuration'},
                    {'name': 'conversions'}
                ]
            }
        ).execute()
        
        # Métricas do último ano (para destaques)
        year_ago = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
        year_start = year_ago
        year_end = end_date
        
        year_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': year_start, 'endDate': year_end}],
                'metrics': [
                    {'name': 'sessions'},
                    {'name': 'totalUsers'},
                    {'name': 'screenPageViews'}
                ]
            }
        ).execute()
        
        # Páginas mais visitadas do ano
        top_pages_year_report = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body={
                'dateRanges': [{'startDate': year_start, 'endDate': year_end}],
                'dimensions': [{'name': 'pagePath'}, {'name': 'pageTitle'}],
                'metrics': [{'name': 'screenPageViews'}],
                'limit': 5,
                'orderBys': [{'metric': {'metricName': 'screenPageViews'}, 'desc': True}]
            }
        ).execute()
        
        # Processar os resultados
        results = {
            'basic_metrics': _process_basic_metrics(basic_report),
            'daily_metrics': _process_daily_metrics(daily_report),
            'top_pages': _process_pages(pages_report),
            'traffic_sources': _process_sources(sources_report),
            'devices': _process_devices(devices_report),
            'devices_metrics': _process_device_metrics(devices_report),
            'year_metrics': _process_year_metrics(year_report),
            'top_pages_year': _process_pages_year(top_pages_year_report)
        }
        
        return results
    
    except Exception as e:
        logging.error(f"Erro ao obter dados do Analytics: {str(e)}")
        raise

def _process_basic_metrics(report):
    """Processa métricas básicas do relatório."""
    metrics = {}
    
    if not report.get('rows'):
        return metrics
    
    metric_names = [
        'total_users', 'sessions', 'engaged_sessions',
        'engagement_rate', 'avg_session_duration',
        'pages_per_session', 'bounce_rate', 'conversions'
    ]
    
    metric_values = report['rows'][0]['metricValues']
    
    for i, name in enumerate(metric_names):
        if i < len(metric_values):
            metrics[name] = metric_values[i]['value']
    
    # Calcular taxa de conversão se disponível
    if 'conversions' in metrics and 'sessions' in metrics:
        if float(metrics['sessions']) > 0:
            conversion_rate = float(metrics['conversions']) / float(metrics['sessions'])
            metrics['conversion_rate'] = str(conversion_rate)
        else:
            metrics['conversion_rate'] = '0'
    
    return metrics

def _process_daily_metrics(report):
    """Processa métricas diárias para gráficos de tendência."""
    daily_data = []
    
    for row in report.get('rows', []):
        date_str = row['dimensionValues'][0]['value']  # Formato: YYYYMMDD
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        
        sessions = row['metricValues'][0]['value']
        users = row['metricValues'][1]['value']
        pageviews = row['metricValues'][2]['value']
        conversions = row['metricValues'][3]['value'] if len(row['metricValues']) > 3 else '0'
        
        daily_data.append({
            'date': formatted_date,
            'sessions': sessions,
            'users': users,
            'pageviews': pageviews,
            'conversions': conversions
        })
    
    return daily_data

def _process_pages(report):
    """Processa o relatório de páginas mais visitadas."""
    pages = []
    
    for row in report.get('rows', []):
        path = row['dimensionValues'][0]['value']
        title = row['dimensionValues'][1]['value']
        views = row['metricValues'][0]['value']
        
        # Tempo médio na página
        time_on_page = row['metricValues'][1]['value'] if len(row['metricValues']) > 1 else '0'
        
        pages.append({
            'path': path, 
            'title': title, 
            'views': views,
            'time': time_on_page
        })
    
    return pages

def _process_sources(report):
    """Processa o relatório de fontes de tráfego."""
    sources = []
    
    for row in report.get('rows', []):
        source = row['dimensionValues'][0]['value']
        medium = row['dimensionValues'][1]['value']
        sessions = row['metricValues'][0]['value']
        
        # Conversões
        conversions = row['metricValues'][1]['value'] if len(row['metricValues']) > 1 else '0'
        
        sources.append({
            'source': source, 
            'medium': medium, 
            'sessions': sessions,
            'conversions': conversions
        })
    
    return sources

def _process_devices(report):
    """Processa o relatório de dispositivos para o gráfico de pizza."""
    devices = {}
    
    for row in report.get('rows', []):
        device = row['dimensionValues'][0]['value']
        sessions = row['metricValues'][0]['value']
        devices[device] = sessions
    
    return devices

def _process_device_metrics(report):
    """Processa métricas detalhadas por dispositivo."""
    device_metrics = {}
    
    for row in report.get('rows', []):
        device = row['dimensionValues'][0]['value']
        sessions = row['metricValues'][0]['value']
        pageviews = row['metricValues'][1]['value']
        avg_time = row['metricValues'][2]['value']
        conversions = row['metricValues'][3]['value'] if len(row['metricValues']) > 3 else '0'
        
        # Calcular páginas por sessão
        pages_per_session = 0
        if float(sessions) > 0:
            pages_per_session = float(pageviews) / float(sessions)
        
        device_metrics[device] = {
            'sessions': sessions,
            'pageviews': pageviews,
            'avg_time': avg_time,
            'conversions': conversions,
            'pages_per_session': str(pages_per_session)
        }
    
    return device_metrics

def _process_year_metrics(report):
    """Processa métricas do último ano para destaques."""
    if not report.get('rows'):
        return {}
    
    metric_names = ['total_sessions', 'total_users', 'total_pageviews']
    metrics = {}
    
    metric_values = report['rows'][0]['metricValues']
    
    for i, name in enumerate(metric_names):
        if i < len(metric_values):
            metrics[name] = metric_values[i]['value']
    
    return metrics

def _process_pages_year(report):
    """Processa as páginas mais visitadas do ano."""
    pages = []
    
    for row in report.get('rows', []):
        path = row['dimensionValues'][0]['value']
        title = row['dimensionValues'][1]['value']
        views = row['metricValues'][0]['value']
        
        pages.append({
            'path': path, 
            'title': title, 
            'views': views
        })
    
    return pages

def get_previous_month_data(property_id, start_date, end_date):
    """
    Obtém dados do mês anterior para comparação.
    
    Args:
        property_id: ID da propriedade do Google Analytics
        start_date: Data de início do mês atual no formato YYYY-MM-DD
        end_date: Data de fim do mês atual no formato YYYY-MM-DD
    
    Returns:
        dict: Dados do Analytics para o mês anterior
    """
    # Calcular datas do mês anterior
    current_start = datetime.strptime(start_date, '%Y-%m-%d')
    current_end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calcular duração do período atual em dias
    current_period_days = (current_end - current_start).days + 1
    
    # Calcular início e fim do mês anterior
    prev_end = current_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=current_period_days - 1)
    
    prev_start_str = prev_start.strftime('%Y-%m-%d')
    prev_end_str = prev_end.strftime('%Y-%m-%d')
    
    # Obter dados do mês anterior
    return get_analytics_data(property_id, prev_start_str, prev_end_str)

def get_annual_data(property_id, end_date):
    """
    Obtém dados dos últimos 12 meses.
    
    Args:
        property_id: ID da propriedade do Google Analytics
        end_date: Data de fim no formato YYYY-MM-DD
    
    Returns:
        dict: Dados do Analytics para os últimos 12 meses
    """
    # Calcular data de início (12 meses atrás)
    end = datetime.strptime(end_date, '%Y-%m-%d')
    start = end - timedelta(days=365)
    
    start_str = start.strftime('%Y-%m-%d')
    
    # Obter dados dos últimos 12 meses
    return get_analytics_data(property_id, start_str, end_date)