from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
import os
from google.cloud import secretmanager

def get_analytics_credentials():
    """Recupera as credenciais do Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR_PROJECT_ID/secrets/analytics-credentials/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return service_account.Credentials.from_service_account_info(
        json.loads(response.payload.data.decode("UTF-8")),
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )

def get_analytics_data(property_id, start_date, end_date):
    """Extrai dados do Google Analytics 4 para o período especificado."""
    credentials = get_analytics_credentials()
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
                {'name': 'averageSessionDuration'}
            ]
        }
    ).execute()
    
    # Páginas mais visitadas
    pages_report = analytics.properties().runReport(
        property=f'properties/{property_id}',
        body={
            'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
            'dimensions': [{'name': 'pagePath'}, {'name': 'pageTitle'}],
            'metrics': [{'name': 'screenPageViews'}],
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
            'metrics': [{'name': 'sessions'}],
            'limit': 10,
            'orderBys': [{'metric': {'metricName': 'sessions'}, 'desc': True}]
        }
    ).execute()
    
    # Dispositivos
    devices_report = analytics.properties().runReport(
        property=f'properties/{property_id}',
        body={
            'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
            'dimensions': [{'name': 'deviceCategory'}],
            'metrics': [{'name': 'sessions'}]
        }
    ).execute()
    
    # Processar os resultados
    results = {
        'basic_metrics': _process_basic_metrics(basic_report),
        'top_pages': _process_pages(pages_report),
        'traffic_sources': _process_sources(sources_report),
        'devices': _process_devices(devices_report)
    }
    
    return results

def _process_basic_metrics(report):
    """Processa métricas básicas do relatório."""
    metrics = {}
    for i, metric_name in enumerate(['total_users', 'sessions', 'engaged_sessions', 
                                      'engagement_rate', 'avg_session_duration']):
        metrics[metric_name] = report['rows'][0]['metricValues'][i]['value']
    return metrics

def _process_pages(report):
    """Processa o relatório de páginas mais visitadas."""
    pages = []
    for row in report.get('rows', []):
        path = row['dimensionValues'][0]['value']
        title = row['dimensionValues'][1]['value']
        views = row['metricValues'][0]['value']
        pages.append({'path': path, 'title': title, 'views': views})
    return pages

def _process_sources(report):
    """Processa o relatório de fontes de tráfego."""
    sources = []
    for row in report.get('rows', []):
        source = row['dimensionValues'][0]['value']
        medium = row['dimensionValues'][1]['value']
        sessions = row['metricValues'][0]['value']
        sources.append({'source': source, 'medium': medium, 'sessions': sessions})
    return sources

def _process_devices(report):
    """Processa o relatório de dispositivos."""
    devices = {}
    for row in report.get('rows', []):
        device = row['dimensionValues'][0]['value']
        sessions = row['metricValues'][0]['value']
        devices[device] = sessions
    return devices