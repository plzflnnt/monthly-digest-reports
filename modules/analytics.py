from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from utils.secrets_utils import get_service_account_credentials
from utils.data_processing import calculate_growth

def get_search_console_data(site_url, start_date, end_date):
    """Extrai dados do Search Console para o período especificado."""
    try:
        # Obter credenciais com escopo para Search Console
        credentials = get_service_account_credentials(
            ['https://www.googleapis.com/auth/webmasters.readonly']
        )
        
        # Construir serviço do Search Console
        search_console = build('searchconsole', 'v1', credentials=credentials)
        
        # Métricas gerais por dia
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
            'rowLimit': 20
        }
        
        top_queries = search_console.searchanalytics().query(siteUrl=site_url, body=query_terms).execute()
        
        # Páginas com melhor desempenho
        top_pages_query = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['page'],
            'rowLimit': 20
        }
        
        top_pages = search_console.searchanalytics().query(siteUrl=site_url, body=top_pages_query).execute()
        
        # Verificar problemas de indexação
        indexing_issues = search_console.urlInspection().index().list(
            body={
                'siteUrl': site_url,
                'inspectionUrl': site_url,
                'pageSize': 10
            }
        ).execute()
        
        # Processar resultados
        results = {
            'performance_by_date': _process_performance_by_date(response),
            'top_queries': _process_top_queries(top_queries),
            'top_pages': _process_top_pages(top_pages),
            'indexing_issues': _process_indexing_issues(indexing_issues)
        }
        
        # Calcular métricas agregadas
        agg_metrics = _calculate_aggregate_metrics(response)
        results.update(agg_metrics)
        
        return results
        
    except Exception as e:
        logging.error(f"Erro ao obter dados do Search Console: {str(e)}")
        # Se a API de inspeção de URL falhar, ainda retornamos os outros dados
        try:
            # Processar resultados sem os dados de indexação
            results = {
                'performance_by_date': _process_performance_by_date(response),
                'top_queries': _process_top_queries(top_queries),
                'top_pages': _process_top_pages(top_pages)
            }
            
            # Calcular métricas agregadas
            agg_metrics = _calculate_aggregate_metrics(response)
            results.update(agg_metrics)
            
            return results
        except Exception as inner_e:
            logging.error(f"Erro secundário ao processar dados do Search Console: {str(inner_e)}")
            raise

def _process_performance_by_date(response):
    """Processa dados de desempenho diário."""
    performance = []
    for row in response.get('rows', []):
        date = row['keys'][0]
        # Formatar data para YYYY-MM-DD
        date_formatted = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        
        metrics = {
            'clicks': row['clicks'],
            'impressions': row['impressions'],
            'ctr': row['ctr'],
            'position': row['position']
        }
        performance.append({'date': date_formatted, **metrics})
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

def _process_indexing_issues(response):
    """Processa problemas de indexação."""
    issues = []
    
    # Verificar se a resposta contém dados de inspeção
    if 'urlInspectionResult' in response:
        inspections = response.get('urlInspectionResult', [])
        
        for inspection in inspections:
            index_status = inspection.get('indexStatusResult', {})
            coverage_state = index_status.get('coverageState', '')
            
            # Verificar problemas comuns
            if coverage_state not in ['Submitted and indexed', 'Indexed, not submitted in sitemap']:
                verdict = index_status.get('verdict', '')
                last_crawl = index_status.get('lastCrawlTime', '')
                
                issues.append({
                    'url': inspection.get('inspectionUrl', ''),
                    'status': coverage_state,
                    'verdict': verdict,
                    'last_crawl': last_crawl
                })
    
    return issues

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

def get_previous_month_data(site_url, start_date, end_date):
    """
    Obtém dados do mês anterior para comparação.
    
    Args:
        site_url: URL do site no Search Console
        start_date: Data de início do mês atual no formato YYYY-MM-DD
        end_date: Data de fim do mês atual no formato YYYY-MM-DD
    
    Returns:
        dict: Dados do Search Console para o mês anterior
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
    return get_search_console_data(site_url, prev_start_str, prev_end_str)