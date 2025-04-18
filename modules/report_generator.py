import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import io
from google.cloud import storage

class ReportGenerator:
    def __init__(self, client_config, template_path, month, year, language='pt-BR'):
        """
        Inicializa o gerador de relatórios.
        
        Args:
            client_config: Configuração do cliente
            template_path: Caminho para o template do relatório
            month: Mês do relatório (1-12)
            year: Ano do relatório
            language: Idioma do relatório
        """
        self.client = client_config
        with open(template_path, 'r') as f:
            self.template = json.load(f)
        self.month = month
        self.year = year
        self.language = language
        self.report_data = {}
        
        # Configurações para os meses em português
        self.month_names = {
            'pt-BR': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        }
    
    def add_data(self, source, data):
        """Adiciona dados ao relatório."""
        self.report_data[source] = data
    
    def generate_pdf(self):
        """Gera o relatório em PDF."""
        pdf = FPDF()
        pdf.add_page()
        
        # Configuração da fonte
        pdf.set_font('Arial', 'B', 16)
        
        # Título do relatório
        month_name = self.month_names.get(self.language, [])[self.month - 1]
        title = f"Relatório Mensal - {self.client['name']} - {month_name} {self.year}"
        pdf.cell(0, 10, title, 0, 1, 'C')
        
        # Adicionar cada seção conforme o template
        for section in self.template['sections']:
            self._add_section(pdf, section)
        
        # Salvar o PDF em memória
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer
    
    def _add_section(self, pdf, section):
        """Adiciona uma seção ao relatório."""
        pdf.set_font('Arial', 'B', 14)
        pdf.ln(10)
        pdf.cell(0, 10, section['title'], 0, 1, 'L')
        pdf.set_font('Arial', '', 12)
        
        # Adicionar conteúdo específico para cada tipo de seção
        if section['name'] == 'resumo':
            self._add_summary_section(pdf)
        elif section['name'] == 'analytics':
            self._add_analytics_section(pdf)
        elif section['name'] == 'search_console':
            self._add_search_console_section(pdf)
    
    def _add_summary_section(self, pdf):
        """Adiciona a seção de resumo."""
        pdf.ln(5)
        analytics_data = self.report_data.get('analytics', {})
        search_console_data = self.report_data.get('search_console', {})
        
        # Visitas e usuários
        if 'basic_metrics' in analytics_data:
            pdf.cell(0, 8, f"Usuários únicos: {analytics_data['basic_metrics']['total_users']}", 0, 1)
            pdf.cell(0, 8, f"Sessões: {analytics_data['basic_metrics']['sessions']}", 0, 1)
            pdf.cell(0, 8, f"Taxa de engajamento: {float(analytics_data['basic_metrics']['engagement_rate'])*100:.2f}%", 0, 1)
        
        # Dados de Search Console
        if 'total_impressions' in search_console_data:
            pdf.cell(0, 8, f"Impressões em buscas: {int(search_console_data['total_impressions'])}", 0, 1)
            pdf.cell(0, 8, f"Cliques em buscas: {int(search_console_data['total_clicks'])}", 0, 1)
            pdf.cell(0, 8, f"CTR médio: {float(search_console_data['avg_ctr'])*100:.2f}%", 0, 1)
            pdf.cell(0, 8, f"Posição média: {float(search_console_data['avg_position']):.1f}", 0, 1)
    
    def _add_analytics_section(self, pdf):
        """Adiciona a seção de Analytics."""
        analytics_data = self.report_data.get('analytics', {})
        if not analytics_data:
            pdf.cell(0, 8, "Dados do Google Analytics não disponíveis.", 0, 1)
            return
        
        # Principais páginas
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "Páginas Mais Visitadas:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'top_pages' in analytics_data:
            for i, page in enumerate(analytics_data['top_pages'][:5], 1):
                pdf.cell(0, 6, f"{i}. {page['title']} - {page['views']} visualizações", 0, 1)
        
        # Dispositivos
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "Dispositivos:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'devices' in analytics_data:
            devices = analytics_data['devices']
            for device, sessions in devices.items():
                pdf.cell(0, 6, f"{device}: {sessions} sessões", 0, 1)
            
            # Gráfico de dispositivos
            pie_chart = self._create_device_chart(devices)
            pdf.image(pie_chart, x=10, y=None, w=80)
        
        # Fontes de tráfego
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "Principais Fontes de Tráfego:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'traffic_sources' in analytics_data:
            for i, source in enumerate(analytics_data['traffic_sources'][:5], 1):
                pdf.cell(0, 6, f"{i}. {source['source']} / {source['medium']} - {source['sessions']} sessões", 0, 1)
    
    def _add_search_console_section(self, pdf):
        """Adiciona a seção de Search Console."""
        search_console_data = self.report_data.get('search_console', {})
        if not search_console_data:
            pdf.cell(0, 8, "Dados do Search Console não disponíveis.", 0, 1)
            return
        
        # Consultas principais
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "Consultas Principais:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'top_queries' in search_console_data:
            for i, query in enumerate(search_console_data['top_queries'][:5], 1):
                pdf.cell(0, 6, f"{i}. {query['query']} - {int(query['clicks'])} cliques, posição {query['position']:.1f}", 0, 1)
        
        # Páginas com melhor desempenho
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "Páginas com Melhor Desempenho:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'top_pages' in search_console_data:
            for i, page in enumerate(search_console_data['top_pages'][:5], 1):
                page_url = page['page'].replace(self.client['search_console']['site_url'], '')
                pdf.cell(0, 6, f"{i}. {page_url} - {int(page['impressions'])} impressões, {int(page['clicks'])} cliques", 0, 1)
                
        # Gráfico de desempenho diário
        if 'performance_by_date' in search_console_data:
            performance_chart = self._create_performance_chart(search_console_data['performance_by_date'])
            pdf.image(performance_chart, x=10, y=None, w=180)
    
    def _create_device_chart(self, devices):
        """Cria um gráfico de pizza de dispositivos."""
        plt.figure(figsize=(6, 4))
        labels = list(devices.keys())
        sizes = list(devices.values())
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.axis('equal')
        plt.title('Distribuição de Sessões por Dispositivo')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        return buf
    
    def _create_performance_chart(self, performance_data):
        """Cria um gráfico de desempenho diário."""
        plt.figure(figsize=(10, 5))
        
        # Converter para DataFrame
        df = pd.DataFrame(performance_data)
        
        # Formatar datas
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Plot de impressões e cliques
        plt.subplot(1, 2, 1)
        plt.plot(df['date'], df['impressions'], 'b-', label='Impressões')
        plt.plot(df['date'], df['clicks'], 'r-', label='Cliques')
        plt.title('Impressões e Cliques')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Plot de CTR e posição
        plt.subplot(1, 2, 2)
        plt.plot(df['date'], df['ctr'] * 100, 'g-', label='CTR (%)')
        plt.plot(df['date'], df['position'], 'm-', label='Posição')
        plt.title('CTR e Posição Média')
        plt.xticks(rotation=45)
        plt.legend()
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        return buf

def upload_report(pdf_buffer, client_id, year, month, bucket_name='monthly-digest-reports'):
    """Faz upload do relatório para o Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Formatar o nome do arquivo
    filename = f"{client_id}/report_{year}_{month:02d}.pdf"
    
    # Fazer upload do arquivo
    blob = bucket.blob(filename)
    blob.upload_from_file(pdf_buffer, content_type='application/pdf')
    
    return f"gs://{bucket_name}/{filename}"