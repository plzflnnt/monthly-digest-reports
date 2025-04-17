import json
from google.cloud import storage

def test_configuration(request):
    """Função para testar a configuração do ambiente."""
    try:
        # Testar acesso ao Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket('monthly-digest-reports')
        
        # Testar leitura dos arquivos de configuração
        with open('config/clients.json', 'r') as f:
            clients = json.load(f)
        
        with open('config/report_template.json', 'r') as f:
            template = json.load(f)
        
        return f"Configuração testada com sucesso! Clientes: {len(clients['clients'])}"
    except Exception as e:
        return f"Erro na configuração: {str(e)}"

# Para teste local
if __name__ == "__main__":
    print(test_configuration(None))