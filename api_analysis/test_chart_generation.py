# test_chart_generation.py
import json
import os
import logging
import io
import base64
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chart_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Tentar importar Plotly com tratamento de erro detalhado
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.io as pio
    logger.info("Plotly importado com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar Plotly: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit("Falha ao importar Plotly, verifique a instalação")

# Tentar importar WeasyPrint com tratamento de erro detalhado
try:
    from weasyprint import HTML, CSS
    logger.info("WeasyPrint importado com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar WeasyPrint: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit("Falha ao importar WeasyPrint, verifique a instalação")

def load_test_data():
    """Carrega dados de teste dos arquivos JSON"""
    logger.info("Carregando dados de teste...")
    
    try:
        # Carregar dados do Analytics
        with open('api_analysis/analytics_raw.json', 'r') as f:
            analytics_data = json.load(f)
            logger.info(f"Dados do Analytics carregados: {len(analytics_data['daily_metrics'])} registros diários")
            
        # Carregar dados do Search Console
        with open('api_analysis/search_console_raw.json', 'r') as f:
            search_console_data = json.load(f)
            logger.info(f"Dados do Search Console carregados: {len(search_console_data['performance_by_date'])} registros diários")
            
        return analytics_data, search_console_data
    
    except Exception as e:
        logger.error(f"Erro ao carregar dados de teste: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit("Falha ao carregar dados de teste")

def inspect_date_formats(data_list, source_name, date_field='date'):
    """Inspeciona e registra os formatos de data nos dados"""
    logger.info(f"Inspecionando formatos de data em {source_name}...")
    
    if not data_list:
        logger.warning(f"Lista de dados vazia para {source_name}")
        return
    
    # Verificar se o campo de data existe
    if date_field not in data_list[0]:
        logger.error(f"Campo de data '{date_field}' não encontrado em {source_name}")
        return
    
    # Analisar todas as datas
    for i, item in enumerate(data_list):
        date_str = item.get(date_field)
        logger.debug(f"{source_name} item {i}: {date_field}={date_str}, tipo={type(date_str)}")

def create_trend_chart(analytics_data):
    """Tenta criar um gráfico de tendência com os dados do Analytics"""
    logger.info("Tentando criar gráfico de tendência...")
    
    try:
        # Verificar dados
        if 'daily_metrics' not in analytics_data or not analytics_data['daily_metrics']:
            logger.error("Dados diários ausentes ou vazios")
            return None
            
        daily_data = analytics_data['daily_metrics']
        logger.info(f"Número de registros diários: {len(daily_data)}")
        
        # Examinar dados em detalhes
        for i, day in enumerate(daily_data[:3]):  # Mostrar apenas os primeiros 3 para brevidade
            logger.debug(f"Registro {i}: {json.dumps(day)}")
        
        # Criar DataFrame
        df = pd.DataFrame(daily_data)
        logger.info(f"DataFrame criado com colunas: {df.columns.tolist()}")
        
        # Debug de cada etapa da preparação dos dados
        if 'date' not in df.columns:
            logger.error("Coluna 'date' não encontrada no DataFrame")
            return None
        
        # Examinar os valores de data
        logger.info(f"Valores de data antes da conversão: {df['date'].head().tolist()}")
        
        # Tentar converter para datetime
        try:
            # Registrar o tipo de cada valor de data
            logger.debug("Tipos de valores na coluna 'date':")
            for i, date_val in enumerate(df['date'].head()):
                logger.debug(f"  {i}: {date_val} ({type(date_val)})")
            
            # Converter para datetime
            logger.debug("Tentando converter datas para datetime...")
            df['date'] = pd.to_datetime(df['date'])
            logger.info("Conversão de datas bem-sucedida")
            logger.debug(f"Valores de data após conversão: {df['date'].head().tolist()}")
        except Exception as e:
            logger.error(f"Erro ao converter datas para datetime: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Tentar abordagem alternativa: tratar cada data individualmente
            logger.info("Tentando abordagem alternativa para conversão de datas...")
            date_converted = []
            sessions = []
            users = []
            
            for i, row in df.iterrows():
                try:
                    date_str = row['date']
                    date_val = pd.to_datetime(date_str)
                    date_converted.append(date_val)
                    sessions.append(int(row['sessions']))
                    users.append(int(row['users']))
                    logger.debug(f"Convertido com sucesso: {date_str} -> {date_val}")
                except Exception as e2:
                    logger.warning(f"Falha ao converter data {row['date']}: {str(e2)}")
            
            # Criar novo DataFrame com dados válidos
            if date_converted:
                df = pd.DataFrame({
                    'date': date_converted,
                    'sessions': sessions,
                    'users': users
                })
                logger.info(f"Novo DataFrame criado com {len(date_converted)} datas válidas")
            else:
                logger.error("Nenhuma data pôde ser convertida")
                return None
        
        # Ordenar por data
        df = df.sort_values('date')
        logger.info("DataFrame ordenado por data")
        
        # Converter colunas numéricas
        try:
            df['sessions'] = df['sessions'].astype(int)
            df['users'] = df['users'].astype(int)
            logger.info("Colunas numéricas convertidas")
        except Exception as e:
            logger.error(f"Erro ao converter colunas numéricas: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        
        # Criar gráfico com Plotly
        logger.info("Criando gráfico com Plotly...")
        try:
            fig = make_subplots(specs=[[{"secondary_y": False}]])
            
            # Adicionar linha de visitas
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['sessions'], 
                    name="Visitas",
                    line=dict(color='#935FA7', width=3),
                    mode='lines'
                )
            )
            
            # Adicionar linha de usuários
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['users'], 
                    name="Usuários",
                    line=dict(color='#F2C354', width=3, dash='dot'),
                    mode='lines'
                )
            )
            
            # Atualizar layout
            fig.update_layout(
                title="Tendência de Visitas e Usuários",
                xaxis_title="Data",
                yaxis_title="Número de Visitas/Usuários",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                template="plotly_white",
                height=400,
                margin=dict(l=10, r=10, t=50, b=30)
            )
            
            logger.info("Gráfico criado com sucesso")
            
            # Salvar o gráfico como HTML para verificação
            try:
                fig.write_html("test_trend_chart.html")
                logger.info("Gráfico salvo como HTML")
            except Exception as e:
                logger.error(f"Erro ao salvar gráfico como HTML: {str(e)}")
                logger.error(traceback.format_exc())
            
            # Converter gráfico para imagem
            logger.info("Convertendo gráfico para imagem...")
            try:
                img_bytes = fig.to_image(format="png", width=1000, height=400, scale=2)
                img_base64 = base64.b64encode(img_bytes).decode('ascii')
                logger.info("Gráfico convertido para imagem com sucesso")
                
                # Salvar imagem para verificação
                with open("test_trend_chart.png", "wb") as f:
                    f.write(img_bytes)
                logger.info("Imagem do gráfico salva como PNG")
                
                return f"data:image/png;base64,{img_base64}"
            except Exception as e:
                logger.error(f"Erro ao converter gráfico para imagem: {str(e)}")
                logger.error(traceback.format_exc())
                return None
                
        except Exception as e:
            logger.error(f"Erro ao criar gráfico com Plotly: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    except Exception as e:
        logger.error(f"Erro geral ao criar gráfico de tendência: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def create_search_performance_chart(search_console_data):
    """Tenta criar um gráfico de desempenho com os dados do Search Console"""
    logger.info("Tentando criar gráfico de desempenho nas buscas...")
    
    try:
        # Verificar dados
        if 'performance_by_date' not in search_console_data or not search_console_data['performance_by_date']:
            logger.error("Dados de desempenho ausentes ou vazios")
            return None
            
        performance_data = search_console_data['performance_by_date']
        logger.info(f"Número de registros de desempenho: {len(performance_data)}")
        
        # Examinar dados em detalhes
        for i, day in enumerate(performance_data[:3]):  # Mostrar apenas os primeiros 3 para brevidade
            logger.debug(f"Registro {i}: {json.dumps(day)}")
        
        # Criar DataFrame
        df = pd.DataFrame(performance_data)
        logger.info(f"DataFrame criado com colunas: {df.columns.tolist()}")
        
        # Debug de cada etapa da preparação dos dados
        if 'date' not in df.columns:
            logger.error("Coluna 'date' não encontrada no DataFrame")
            return None
        
        # Examinar os valores de data
        logger.info(f"Valores de data antes da conversão: {df['date'].head().tolist()}")
        
        # Tentar converter para datetime
        try:
            # Registrar o tipo de cada valor de data
            logger.debug("Tipos de valores na coluna 'date':")
            for i, date_val in enumerate(df['date'].head()):
                logger.debug(f"  {i}: {date_val} ({type(date_val)})")
            
            # Converter para datetime
            logger.debug("Tentando converter datas para datetime...")
            df['date'] = pd.to_datetime(df['date'])
            logger.info("Conversão de datas bem-sucedida")
            logger.debug(f"Valores de data após conversão: {df['date'].head().tolist()}")
        except Exception as e:
            logger.error(f"Erro ao converter datas para datetime: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Tentar abordagem alternativa: tratar cada data individualmente
            logger.info("Tentando abordagem alternativa para conversão de datas...")
            date_converted = []
            impressions = []
            clicks = []
            positions = []
            
            for i, row in df.iterrows():
                try:
                    date_str = row['date']
                    date_val = pd.to_datetime(date_str)
                    date_converted.append(date_val)
                    impressions.append(row['impressions'])
                    clicks.append(row['clicks'])
                    positions.append(row['position'])
                    logger.debug(f"Convertido com sucesso: {date_str} -> {date_val}")
                except Exception as e2:
                    logger.warning(f"Falha ao converter data {row['date']}: {str(e2)}")
            
            # Criar novo DataFrame com dados válidos
            if date_converted:
                df = pd.DataFrame({
                    'date': date_converted,
                    'impressions': impressions,
                    'clicks': clicks,
                    'position': positions
                })
                logger.info(f"Novo DataFrame criado com {len(date_converted)} datas válidas")
            else:
                logger.error("Nenhuma data pôde ser convertida")
                return None
        
        # Ordenar por data
        df = df.sort_values('date')
        logger.info("DataFrame ordenado por data")
        
        # Criar gráfico com Plotly
        logger.info("Criando gráfico com Plotly...")
        try:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Adicionar linha de impressões
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['impressions'], 
                    name="Impressões",
                    line=dict(color='#935FA7', width=3),
                    mode='lines'
                ),
                secondary_y=False
            )
            
            # Adicionar linha de cliques
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['clicks'], 
                    name="Cliques",
                    line=dict(color='#F2C354', width=3),
                    mode='lines'
                ),
                secondary_y=False
            )
            
            # Adicionar linha de posição média (eixo secundário, invertido)
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['position'], 
                    name="Posição Média",
                    line=dict(color='#FF6B6C', width=2, dash='dash'),
                    mode='lines'
                ),
                secondary_y=True
            )
            
            # Configurar eixos
            fig.update_yaxes(title_text="Impressões e Cliques", secondary_y=False)
            fig.update_yaxes(title_text="Posição Média", secondary_y=True, autorange="reversed")
            
            # Atualizar layout
            fig.update_layout(
                title="Desempenho nas Buscas",
                xaxis_title="Data",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                template="plotly_white",
                height=400,
                margin=dict(l=10, r=10, t=50, b=30)
            )
            
            logger.info("Gráfico criado com sucesso")
            
            # Salvar o gráfico como HTML para verificação
            try:
                fig.write_html("test_search_chart.html")
                logger.info("Gráfico salvo como HTML")
            except Exception as e:
                logger.error(f"Erro ao salvar gráfico como HTML: {str(e)}")
                logger.error(traceback.format_exc())
            
            # Converter gráfico para imagem
            logger.info("Convertendo gráfico para imagem...")
            try:
                img_bytes = fig.to_image(format="png", width=1000, height=400, scale=2)
                img_base64 = base64.b64encode(img_bytes).decode('ascii')
                logger.info("Gráfico convertido para imagem com sucesso")
                
                # Salvar imagem para verificação
                with open("test_search_chart.png", "wb") as f:
                    f.write(img_bytes)
                logger.info("Imagem do gráfico salva como PNG")
                
                return f"data:image/png;base64,{img_base64}"
            except Exception as e:
                logger.error(f"Erro ao converter gráfico para imagem: {str(e)}")
                logger.error(traceback.format_exc())
                return None
                
        except Exception as e:
            logger.error(f"Erro ao criar gráfico com Plotly: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    except Exception as e:
        logger.error(f"Erro geral ao criar gráfico de desempenho: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def generate_test_report(trend_chart_url, search_chart_url):
    """Gera um relatório de teste simples com os gráficos"""
    logger.info("Gerando relatório de teste...")
    
    try:
        # Template HTML simples
        html_template = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório de Teste de Gráficos</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .chart-container { margin: 20px 0; border: 1px solid #ddd; padding: 10px; }
                img { max-width: 100%; }
            </style>
        </head>
        <body>
            <h1>Relatório de Teste - Verificação de Gráficos</h1>
            
            <div class="chart-container">
                <h2>Gráfico 1: Tendência de Visitas e Usuários</h2>
                <img src="{trend_chart}" alt="Gráfico de tendência">
            </div>
            
            <div class="chart-container">
                <h2>Gráfico 2: Desempenho nas Buscas</h2>
                <img src="{search_chart}" alt="Gráfico de desempenho nas buscas">
            </div>
            
            <p>Gerado em: {datetime}</p>
        </body>
        </html>
        """
        
        # Preencher o template
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = html_template.format(
            trend_chart=trend_chart_url if trend_chart_url else "",
            search_chart=search_chart_url if search_chart_url else "",
            datetime=now
        )
        
        # Salvar HTML
        with open("test_report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("Relatório HTML salvo como test_report.html")
        
        # Tentar converter para PDF
        logger.info("Tentando converter relatório para PDF...")
        try:
            HTML(string=html_content).write_pdf("test_report.pdf")
            logger.info("Relatório PDF salvo como test_report.pdf")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            logger.error(traceback.format_exc())
            
        return True
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de teste: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_kaleido_installation():
    """Testa se o Kaleido (necessário para Plotly to_image) está instalado corretamente"""
    logger.info("Testando instalação do Kaleido...")
    
    try:
        from kaleido.scopes.plotly import PlotlyScope
        scope = PlotlyScope()
        logger.info("Kaleido importado com sucesso")
        
        # Testar com um gráfico simples
        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 3, 2]))
        img_bytes = fig.to_image(format="png")
        
        # Se chegou aqui, o Kaleido está funcionando
        logger.info("Kaleido funcionando corretamente")
        return True
    except Exception as e:
        logger.error(f"Erro ao testar Kaleido: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error("O Kaleido é necessário para converter gráficos Plotly em imagens.")
        logger.error("Tente reinstalar com: pip install -U kaleido")
        return False

def main():
    """Função principal de teste"""
    logger.info("=" * 80)
    logger.info("INICIANDO TESTE DE GERAÇÃO DE GRÁFICOS")
    logger.info("=" * 80)
    
    # Testar Kaleido
    if not test_kaleido_installation():
        sys.exit("Falha na instalação do Kaleido, necessário para geração de imagens")
    
    # Carregar dados
    analytics_data, search_console_data = load_test_data()
    
    # Inspecionar formatos de data
    inspect_date_formats(analytics_data['daily_metrics'], "Analytics")
    inspect_date_formats(search_console_data['performance_by_date'], "Search Console")
    
    # Tentar gerar gráficos
    trend_chart_url = create_trend_chart(analytics_data)
    search_chart_url = create_search_performance_chart(search_console_data)
    
    # Verificar resultados
    if trend_chart_url:
        logger.info("Gráfico de tendência gerado com sucesso")
    else:
        logger.warning("Falha ao gerar gráfico de tendência")
    
    if search_chart_url:
        logger.info("Gráfico de desempenho nas buscas gerado com sucesso")
    else:
        logger.warning("Falha ao gerar gráfico de desempenho nas buscas")
    
    # Gerar relatório
    generate_test_report(trend_chart_url, search_chart_url)
    
    logger.info("=" * 80)
    logger.info("TESTE CONCLUÍDO")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()