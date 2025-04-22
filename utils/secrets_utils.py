from google.cloud import secretmanager
import json
import logging

def get_service_account_credentials(scopes):
    """
    Obtém as credenciais de serviço do Secret Manager para acesso às APIs do Google.
    
    Args:
        scopes: Lista de escopos necessários para a API
    
    Returns:
        Objeto Credentials configurado com os escopos solicitados
    """
    from google.oauth2 import service_account
    
    try:
        # Inicializar cliente do Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        
        # Nome do secret (caminho completo)
        secret_name = "projects/295924338757/secrets/monthly-digest-service-account/versions/latest"
        
        # Acessar o secret
        response = client.access_secret_version(request={"name": secret_name})
        
        # Decodificar o payload
        secret_content = response.payload.data.decode("UTF-8")
        
        # Converter em JSON
        service_account_info = json.loads(secret_content)
        
        # Criar e retornar credenciais
        return service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )
    
    except Exception as e:
        logging.error(f"Erro ao obter credenciais: {str(e)}")
        raise

def get_mailjet_credentials():
    """
    Obtém as credenciais do Mailjet do Secret Manager.
    
    Returns:
        dict: Dicionário com credenciais do Mailjet (api_key, secret_key, sender_email, sender_name)
    """
    try:
        # Inicializar cliente do Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        
        # Nome do secret (caminho completo)
        secret_name = "projects/295924338757/secrets/mailjet-credentials/versions/latest"
        
        # Acessar o secret
        response = client.access_secret_version(request={"name": secret_name})
        
        # Decodificar o payload
        secret_content = response.payload.data.decode("UTF-8")
        
        # Converter em JSON
        mailjet_credentials = json.loads(secret_content)
        
        return mailjet_credentials
    
    except Exception as e:
        logging.error(f"Erro ao obter credenciais do Mailjet: {str(e)}")
        raise