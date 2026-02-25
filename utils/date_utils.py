from datetime import datetime, timedelta
import calendar

def get_previous_month_dates():
    """
    Retorna as datas de início e fim do mês anterior.
    
    Returns:
        tuple: (primeiro_dia, ultimo_dia, mes, ano)
    """
    today = datetime.today()
    
    # Se estamos no primeiro mês do ano
    if today.month == 1:
        month = 12
        year = today.year - 1
    else:
        month = today.month - 1
        year = today.year
    
    # Primeiro dia do mês anterior
    first_day = datetime(year, month, 1)
    
    # Último dia do mês anterior
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Formatar para YYYY-MM-DD
    first_day_str = first_day.strftime('%Y-%m-%d')
    last_day_str = last_day.strftime('%Y-%m-%d')
    
    return first_day_str, last_day_str, month, year

def format_date_range(start_date, end_date, language='pt-BR'):
    """
    Formata uma faixa de datas para exibição.
    
    Args:
        start_date: Data de início no formato 'YYYY-MM-DD'
        end_date: Data de fim no formato 'YYYY-MM-DD'
        language: Idioma para formatação
    
    Returns:
        str: Faixa de datas formatada
    """
    # Converter string para datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Meses em diferentes idiomas
    months = {
        'pt-BR': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    }
    
    # Se ambas as datas estão no mesmo mês/ano
    if start.month == end.month and start.year == end.year:
        month_name = months.get(language, [''])[start.month - 1]
        return f"{month_name} {start.year}"
    
    # Caso contrário, mostrar período completo
    start_month = months.get(language, [''])[start.month - 1]
    end_month = months.get(language, [''])[end.month - 1]
    
    if language == 'pt-BR':
        return f"{start.day} de {start_month} a {end.day} de {end_month} de {end.year}"
    
    return f"{start_date} to {end_date}"