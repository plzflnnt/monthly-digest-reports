# test_client.py
import logging
from modules import analytics as analytics_module
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_client_analytics():
    # Dados do cliente com problema
    property_id = "366744888"  # ID do Estrelinhas No Céu
    
    # Período para teste (último mês)
    end_date = datetime.today().replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    logger.info(f"Testando cliente Estrelinhas No Céu para o período: {start_date_str} a {end_date_str}")
    
    try:
        # Extrair dados brutos para verificar estrutura
        analytics_data = analytics_module.get_analytics_data(
            property_id, 
            start_date_str, 
            end_date_str
        )
        
        # Verificar estrutura dos dados
        logger.info(f"Chaves no retorno: {analytics_data.keys()}")
        
        # Verificar métricas básicas
        if 'basic_metrics' in analytics_data:
            logger.info(f"Métricas básicas: {analytics_data['basic_metrics']}")
        else:
            logger.error("Métricas básicas não encontradas!")
            
        # Tentativa de acesso à chave sessions
        if 'basic_metrics' in analytics_data and 'sessions' in analytics_data['basic_metrics']:
            logger.info(f"Sessions: {analytics_data['basic_metrics']['sessions']}")
        else:
            logger.error("Chave 'sessions' não encontrada nas métricas básicas!")
            
    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_client_analytics()