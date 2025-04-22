# test_integration.py
import json
from datetime import datetime, timedelta
import os
from modules import analytics, search_console, report_generator, notifier
from utils import date_utils

def test_integration():
    """Testa a integração dos módulos."""
    print("Iniciando teste de integração...")
    
    # Definir período para teste (último mês completo)
    end_date = datetime.today().replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    month = start_date.month
    year = start_date.year
    
    print(f"Período de teste: {start_date_str} a {end_date_str}")
    
    # Carregar configuração de cliente de teste
    with open('config/clients.json', 'r') as f:
        clients_config = json.load(f)
    
    # Usar o primeiro cliente para teste
    client = clients_config['clients'][0]
    print(f"Cliente de teste: {client['name']}")
    
    # 1. Testar extração de dados do Analytics
    print("\nTestando extração de dados do Google Analytics...")
    try:
        analytics_data = analytics.get_analytics_data(
            client['analytics']['property_id'], 
            start_date_str, 
            end_date_str
        )
        print("✅ Dados do Analytics extraídos com sucesso!")
        print(f"Métricas básicas: {json.dumps(analytics_data['basic_metrics'], indent=2)}")
    except Exception as e:
        print(f"❌ Erro ao extrair dados do Analytics: {str(e)}")
        return
    
    # 2. Testar extração de dados do Search Console
    print("\nTestando extração de dados do Search Console...")
    try:
        search_console_data = search_console.get_search_console_data(
            client['search_console']['site_url'], 
            start_date_str, 
            end_date_str
        )
        print("✅ Dados do Search Console extraídos com sucesso!")
        print(f"Métricas agregadas: {json.dumps({k: v for k, v in search_console_data.items() if k not in ['performance_by_date', 'top_queries', 'top_pages']}, indent=2)}")
    except Exception as e:
        print(f"❌ Erro ao extrair dados do Search Console: {str(e)}")
        return
    
    # 3. Testar geração de relatório
    print("\nTestando geração de relatório...")
    try:
        report = report_generator.ReportGenerator(
            client,
            'config/report_template.json',
            month,
            year,
            client['report_config'].get('language', 'pt-BR')
        )
        
        # Adicionar dados ao relatório
        report.add_data('analytics', analytics_data)
        report.add_data('search_console', search_console_data)
        
        # Gerar PDF
        pdf_buffer = report.generate_pdf()
        print("✅ Relatório PDF gerado com sucesso!")
        
        # Salvar localmente para verificação
        with open('teste_relatorio.pdf', 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print("Relatório salvo como 'teste_relatorio.pdf'")
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {str(e)}")
        return
    
    # 4. Testar upload para Cloud Storage (opcional)
    print("\nTestando upload para Cloud Storage...")
    try:
        pdf_buffer.seek(0)
        report_url = report_generator.upload_report(
            pdf_buffer, 
            client['id'], 
            year, 
            month,
            bucket_name='monthly-digest-reports'
        )
        print(f"✅ Relatório enviado para: {report_url}")
    except Exception as e:
        print(f"❌ Erro ao fazer upload do relatório: {str(e)}")
    
    # 5. Testar notificação (opcional - remova comentário para testar)
    
    print("\nTestando notificação por e-mail...")
    try:
        pdf_buffer.seek(0)
        success, message = notifier.notify_client(
            client, 
            report_url, 
            month, 
            year, 
            pdf_buffer
        )
        
        if success:
            print(f"✅ Cliente notificado com sucesso: {message}")
        else:
            print(f"❌ Erro ao notificar cliente: {message}")
    except Exception as e:
        print(f"❌ Erro ao notificar cliente: {str(e)}")
    
    
    print("\nTeste de integração concluído!")

if __name__ == "__main__":
    test_integration()