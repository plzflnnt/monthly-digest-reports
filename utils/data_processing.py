import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def calculate_growth(current_value, previous_value):
    """Calcula o crescimento percentual entre dois valores."""
    if previous_value == 0:
        return 0  # Evitar divisão por zero
    
    growth = ((current_value - previous_value) / previous_value) * 100
    return growth

def format_number(number, decimal_places=0):
    """Formata um número para exibição."""
    if decimal_places == 0:
        return f"{int(number):,}".replace(",", ".")
    else:
        return f"{number:.{decimal_places}f}".replace(".", ",")

def format_percentage(value, decimal_places=2):
    """Formata um valor percentual para exibição."""
    return f"{value:.{decimal_places}f}%".replace(".", ",")

def summarize_time_series(data, date_column, value_column):
    """
    Gera um resumo estatístico de uma série temporal.
    
    Args:
        data: DataFrame com os dados
        date_column: Nome da coluna de data
        value_column: Nome da coluna de valor
    
    Returns:
        dict: Resumo estatístico
    """
    # Converter datas se necessário
    if not pd.api.types.is_datetime64_any_dtype(data[date_column]):
        data[date_column] = pd.to_datetime(data[date_column])
    
    # Ordenar por data
    data = data.sort_values(date_column)
    
    # Calcular estatísticas
    summary = {
        'total': data[value_column].sum(),
        'average': data[value_column].mean(),
        'median': data[value_column].median(),
        'min': data[value_column].min(),
        'max': data[value_column].max(),
        'first_value': data[value_column].iloc[0],
        'last_value': data[value_column].iloc[-1]
    }
    
    # Calcular tendência (crescimento entre primeiro e último valor)
    summary['growth'] = calculate_growth(summary['last_value'], summary['first_value'])
    
    return summary

def filter_outliers(data, column, method='zscore', threshold=3):
    """
    Remove outliers de um conjunto de dados.
    
    Args:
        data: DataFrame com os dados
        column: Nome da coluna para filtrar outliers
        method: Método para detecção de outliers ('zscore' ou 'iqr')
        threshold: Limiar para detecção de outliers
    
    Returns:
        DataFrame: Dados sem outliers
    """
    if method == 'zscore':
        # Usando Z-score
        z_scores = np.abs((data[column] - data[column].mean()) / data[column].std())
        return data[z_scores < threshold]
    
    elif method == 'iqr':
        # Usando IQR (Intervalo Interquartil)
        Q1 = data[column].quantile(0.25)
        Q3 = data[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        return data[(data[column] >= lower_bound) & (data[column] <= upper_bound)]
    
    # Método não reconhecido, retornar dados originais
    return data