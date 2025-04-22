from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from utils.secrets_utils import get_service_account_credentials

def get_search_console_data(site_url, start_date, end_date):
    """Extrai dados do Search Console para o período especificado."""
    try:
        # Obter credenciais com escopo para Search Console
        credentials = get_service_account_credentials(
            ['https://www.googleapis.com/auth/webmasters.readonly']
        )
        
        # Construir serviço do Search Console
        search_console = build('searchconsole', 'v1', credentials=credentials)
        
        # Métricas gerais
        query = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date'],
            'rowLimit': 31  # Para cobrir um mês inteiro
        }
        
        response = search_console.searchanalytics().query(siteUrl=site_url, body=query).execute()
        
        # Consultas principais
        query_terms = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['query'],
            'rowLimit': 10
        }
        
        top_queries = search_console.searchanalytics().query(siteUrl=site_url, body=query_terms).execute()
        
        # Páginas com melhor desempenho
        top_pages_query = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['page'],
            'rowLimit': 10
        }
        
        top_pages = search_console.searchanalytics().query(siteUrl=site_url, body=top_pages_query).execute()
        
        # Processar resultados
        results = {
            'performance_by_date': _process_performance_by_date(response),
            'top_queries': _process_top_queries(top_queries),
            'top_pages': _process_top_pages(top_pages)
        }
        
        # Calcular métricas agregadas
        agg_metrics = _calculate_aggregate_metrics(response)
        results.update(agg_metrics)
        
        return results
        
    except Exception as e:
        logging.error(f"Erro ao obter dados do Search Console: {str(e)}")
        raise

def _process_performance_by_date(response):
    """Processa dados de desempenho diário."""
    performance = []
    for row in response.get('rows', []):
        date = row['keys'][0]
        metrics = {
            'clicks': row['clicks'],
            'impressions': row['impressions'],
            'ctr': row['ctr'],
            'position': row['position']
        }
        performance.append({'date': date, **metrics})
    return performance

def _process_top_queries(response):
    """Processa dados das principais consultas."""
    queries = []
    for row in response.get('rows', []):
        query = row['keys'][0]
        metrics = {
            'clicks': row['clicks'],
            'impressions': row['impressions'],
            'ctr': row['ctr'],
            'position': row['position']
        }
        queries.append({'query': query, **metrics})
    return queries

def _process_top_pages(response):
    """Processa dados das principais páginas."""
    pages = []
    for row in response.get('rows', []):
        page = row['keys'][0]
        metrics = {
            'clicks': row['clicks'],
            'impressions': row['impressions'],
            'ctr': row['ctr'],
            'position': row['position']
        }
        pages.append({'page': page, **metrics})
    return pages

def _calculate_aggregate_metrics(response):
    """Calcula métricas agregadas para o período."""
    total_clicks = 0
    total_impressions = 0
    sum_ctr = 0
    sum_position = 0
    count = 0
    
    for row in response.get('rows', []):
        total_clicks += row['clicks']
        total_impressions += row['impressions']
        sum_ctr += row['ctr']
        sum_position += row['position']
        count += 1
    
    avg_ctr = sum_ctr / count if count > 0 else 0
    avg_position = sum_position / count if count > 0 else 0
    
    return {
        'total_clicks': total_clicks,
        'total_impressions': total_impressions,
        'avg_ctr': avg_ctr,
        'avg_position': avg_position
    }