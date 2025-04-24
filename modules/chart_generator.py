# chart_generator.py
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json
import logging
import traceback
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.io as pio
from PIL import Image, ImageDraw

# Desativar logging detalhado (descomentar para ativar)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.WARNING)  # Apenas avisos e erros
logger = logging.getLogger(__name__)

def create_trend_chart(daily_metrics, save_debug=False):
    """
    Cria gráfico de tendência de visitas e usuários.
    
    Args:
        daily_metrics: Lista de dicionários com dados diários
        save_debug: Se True, salva arquivos intermediários para debug
    
    Returns:
        BytesIO: Buffer contendo a imagem do gráfico ou None em caso de erro
    """
    logger.info("Gerando gráfico de tendência de visitas e usuários...")
    
    try:
        # Verificar se há dados
        if not daily_metrics:
            logger.warning("Sem dados para gerar gráfico de tendência")
            return None
        
        # Salvar dados brutos para debug se solicitado
        if save_debug:
            with open("debug_trend_data.json", "w") as f:
                json.dump(daily_metrics, f, indent=2)
        
        # Criar DataFrame
        df = pd.DataFrame(daily_metrics)
        
        # Verificar se tem a coluna 'date'
        if 'date' not in df.columns:
            logger.error("Coluna 'date' não encontrada nos dados diários")
            return None
        
        # Converter para datetime
        try:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        except Exception as e:
            logger.error(f"Erro ao converter datas: {str(e)}")
            # Abordagem alternativa: processar cada data individualmente
            valid_data = []
            for item in daily_metrics:
                try:
                    date = pd.to_datetime(item['date'])
                    sessions = int(item['sessions'])
                    users = int(item['users'])
                    valid_data.append({'date': date, 'sessions': sessions, 'users': users})
                except Exception as e2:
                    logger.warning(f"Pulando registro com data inválida: {item['date']}")
            
            if not valid_data:
                logger.error("Nenhum registro válido após tratamento de datas")
                return None
                
            df = pd.DataFrame(valid_data)
        
        # Converter valores para numéricos
        try:
            df['sessions'] = pd.to_numeric(df['sessions'])
            df['users'] = pd.to_numeric(df['users'])
        except Exception as e:
            logger.error(f"Erro ao converter valores numéricos: {str(e)}")
            return None
        
        # Criar gráfico
        fig = make_subplots(specs=[[{"secondary_y": False}]])
        
        fig.add_trace(
            go.Scatter(
                x=df['date'], 
                y=df['sessions'], 
                name="Visitas",
                line=dict(color='#935FA7', width=3),
                mode='lines'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['date'], 
                y=df['users'], 
                name="Usuários",
                line=dict(color='#F2C354', width=3, dash='dot'),
                mode='lines'
            )
        )
        
        fig.update_layout(
            title=None,
            xaxis_title=None,
            yaxis_title="Número de Visitas/Usuários",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_white",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # Salvar HTML para debug se solicitado
        if save_debug:
            fig.write_html("debug_trend_chart.html")
        
        img_buffer = io.BytesIO()
        pio.write_image(fig, img_buffer, format="png", width=1000, height=300, scale=2)
        img_buffer.seek(0)  # Resetar o ponteiro do buffer para o início
        
        # Salvar para debug, se necessário
        if save_debug:
            with open("debug_trend_chart.png", "wb") as f:
                f.write(img_buffer.getvalue())
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de tendência: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def create_devices_chart(devices_data, save_debug=False):
    """
    Cria gráfico de distribuição de dispositivos.
    
    Args:
        devices_data: Dicionário com contagem de sessões por dispositivo
        save_debug: Se True, salva arquivos intermediários para debug
    
    Returns:
        str: BytesIO: Buffer contendo a imagem do gráfico ou None em caso de erro
    """
    logger.info("Gerando gráfico de dispositivos...")
    
    try:
        # Verificar se há dados
        if not devices_data:
            logger.warning("Sem dados para gerar gráfico de dispositivos")
            return None
            
        # Salvar dados brutos para debug se solicitado
        if save_debug:
            with open("debug_devices_data.json", "w") as f:
                json.dump(devices_data, f, indent=2)
        
        # Converter valores para inteiros (caso sejam strings)
        devices_int = {k: int(v) if isinstance(v, str) else v for k, v in devices_data.items()}
        
        # Preparar dados
        labels = list(devices_int.keys())
        values = list(devices_int.values())
        
        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            textinfo='label+percent',
            marker=dict(colors=['#935FA7', '#F2C354', '#111218'])
        )])
        
        fig.update_layout(
            title=None,
            legend=dict(
                orientation="h", 
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_white",
            height=250,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # Salvar HTML para debug se solicitado
        if save_debug:
            fig.write_html("debug_devices_chart.html")
        
        img_buffer = io.BytesIO()
        pio.write_image(fig, img_buffer, format="png", width=1000, height=300, scale=2)
        img_buffer.seek(0)  # Resetar o ponteiro do buffer para o início
        
        # Salvar para debug, se necessário
        if save_debug:
            with open("debug_trend_chart.png", "wb") as f:
                f.write(img_buffer.getvalue())
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de tendência: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def create_traffic_sources_chart(traffic_sources, save_debug=False):
    """
    Cria gráfico de fontes de tráfego.
    
    Args:
        traffic_sources: Lista de dicionários com fontes de tráfego
        save_debug: Se True, salva arquivos intermediários para debug
    
    Returns:
        str: BytesIO: Buffer contendo a imagem do gráfico ou None em caso de erro
    """
    logger.info("Gerando gráfico de fontes de tráfego...")
    
    try:
        # Verificar se há dados
        if not traffic_sources:
            logger.warning("Sem dados para gerar gráfico de fontes de tráfego")
            return None
            
        # Salvar dados brutos para debug se solicitado
        if save_debug:
            with open("debug_traffic_sources_data.json", "w") as f:
                json.dump(traffic_sources, f, indent=2)
        
        # Processa as fontes de tráfego
        sources = {}
        for source in traffic_sources:
            # Garantir que o objeto tenha os campos necessários
            if 'medium' not in source or 'sessions' not in source:
                continue
                
            medium = source['medium']
            # Simplifica as fontes para categorias mais amplas
            if medium == 'organic':
                category = 'Orgânico'
            elif medium == 'referral':
                category = 'Referência'
            elif medium == 'social':
                category = 'Social'
            elif medium == 'email':
                category = 'Email'
            elif medium == '(none)' or medium == 'direct':
                category = 'Direto'
            else:
                category = 'Outros'

            # Garantir que o valor das sessões seja inteiro
            session_value = int(source['sessions']) if isinstance(source['sessions'], str) else source['sessions']

            if category in sources:
                sources[category] += session_value
            else:
                sources[category] = session_value

        # Se não houver categorias válidas, retornar None
        if not sources:
            logger.warning("Nenhuma fonte de tráfego válida encontrada")
            return None

        # Preparar dados para o gráfico
        df = pd.DataFrame({
            'Fonte': list(sources.keys()),
            'Sessões': list(sources.values())
        })
        df = df.sort_values('Sessões', ascending=False)

        # Criar gráfico de barras
        fig = px.bar(
            df, 
            x='Fonte', 
            y='Sessões',
            color='Fonte',
            color_discrete_map={
                'Orgânico': '#935FA7',
                'Direto': '#F2C354',
                'Referência': '#FF6B6C',
                'Social': '#A1E8CC',
                'Email': '#111218',
                'Outros': '#999999'
            },
            text='Sessões'
        )

        # Atualizar layout
        fig.update_layout(
            title=None,
            xaxis_title=None,
            yaxis_title="Número de Sessões",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_white",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )

        fig.update_traces(texttemplate='%{text}', textposition='outside')
        
        # Salvar HTML para debug se solicitado
        if save_debug:
            fig.write_html("debug_traffic_sources_chart.html")
        
        # Converter para imagem
        img_buffer = io.BytesIO()
        pio.write_image(fig, img_buffer, format="png", width=1000, height=300, scale=2)
        img_buffer.seek(0)  # Resetar o ponteiro do buffer para o início
        
        # Salvar para debug, se necessário
        if save_debug:
            with open("debug_trend_chart.png", "wb") as f:
                f.write(img_buffer.getvalue())
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de tendência: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def create_search_performance_chart(performance_data, save_debug=False):
    """
    Cria gráfico de desempenho nas buscas.
    
    Args:
        performance_data: Lista de dicionários com dados de desempenho
        save_debug: Se True, salva arquivos intermediários para debug
    
    Returns:
        str: BytesIO: Buffer contendo a imagem do gráfico ou None em caso de erro
    """
    logger.info("Gerando gráfico de desempenho nas buscas...")
    
    try:
        # Verificar se há dados
        if not performance_data:
            logger.warning("Sem dados para gerar gráfico de desempenho nas buscas")
            return None
            
        # Salvar dados brutos para debug se solicitado
        if save_debug:
            with open("debug_search_performance_data.json", "w") as f:
                json.dump(performance_data, f, indent=2)
        
        # Criar DataFrame
        df = pd.DataFrame(performance_data)
        
        # Verificar se tem as colunas necessárias
        required_columns = ['date', 'impressions', 'clicks', 'position']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Coluna '{col}' não encontrada nos dados de desempenho")
                return None
        
        # Converter para datetime
        try:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        except Exception as e:
            logger.error(f"Erro ao converter datas: {str(e)}")
            # Abordagem alternativa: processar cada data individualmente
            valid_data = []
            for item in performance_data:
                try:
                    date = pd.to_datetime(item['date'])
                    impressions = int(item['impressions'])
                    clicks = int(item['clicks'])
                    position = float(item['position'])
                    valid_data.append({
                        'date': date, 
                        'impressions': impressions, 
                        'clicks': clicks, 
                        'position': position
                    })
                except Exception as e2:
                    logger.warning(f"Pulando registro com dados inválidos: {item}")
            
            if not valid_data:
                logger.error("Nenhum registro válido após tratamento de dados")
                return None
                
            df = pd.DataFrame(valid_data)
        
        # Converter valores para numéricos
        try:
            df['impressions'] = pd.to_numeric(df['impressions'])
            df['clicks'] = pd.to_numeric(df['clicks'])
            df['position'] = pd.to_numeric(df['position'])
        except Exception as e:
            logger.error(f"Erro ao converter valores numéricos: {str(e)}")
            return None
        
        # Criar gráfico
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
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
        
        fig.update_yaxes(title_text="Impressões e Cliques", secondary_y=False)
        fig.update_yaxes(
            title_text="Posição Média", 
            secondary_y=True, 
            autorange="reversed"  # Inverter eixo de posição
        )
        
        fig.update_layout(
            title=None,
            xaxis_title=None,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_white",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # Salvar HTML para debug se solicitado
        if save_debug:
            fig.write_html("debug_search_performance_chart.html")
        
        # Converter para imagem
        img_buffer = io.BytesIO()
        pio.write_image(fig, img_buffer, format="png", width=1000, height=300, scale=2)
        img_buffer.seek(0)  # Resetar o ponteiro do buffer para o início
        
        # Salvar para debug, se necessário
        if save_debug:
            with open("debug_trend_chart.png", "wb") as f:
                f.write(img_buffer.getvalue())
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de tendência: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_empty_chart_image(message="Dados insuficientes para gerar o gráfico", width=700, height=300):
    """
    Cria uma imagem de fallback para gráficos ausentes.
    
    Args:
        message: Mensagem a ser exibida na imagem
        width: Largura da imagem
        height: Altura da imagem
    
    Returns:
        BytesIO: Buffer contendo a imagem de fallback
    """
    try:
        # Criar figura em branco
        fig = go.Figure()
        
        # Configurar layout
        fig.update_layout(
            plot_bgcolor='#f5f5f5',
            paper_bgcolor='#f5f5f5',
            width=width,
            height=height,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # Adicionar texto de mensagem
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(
                family="Arial, sans-serif",
                size=14,
                color="#777777"
            )
        )
        
        # Desabilitar eixos
        fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
        fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)
        
        # Converter para imagem
        img_buffer = io.BytesIO()
        pio.write_image(fig, img_buffer, format="png", scale=2)
        img_buffer.seek(0)
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Erro ao gerar imagem de fallback: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Criar uma imagem mínima em caso de erro completo
        from PIL import Image, ImageDraw
        
        # Criar imagem branca
        fallback = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(fallback)
        draw.text((10, 100), "Não foi possível gerar o gráfico", fill='black')
        
        # Salvar em buffer
        buffer = io.BytesIO()
        fallback.save(buffer, 'PNG')
        buffer.seek(0)
        
        return buffer