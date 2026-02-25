# check_dependencies.py
import importlib
import sys
import logging

logger = logging.getLogger(__name__)

def check_dependencies():
    """
    Verifica se todas as dependências necessárias estão instaladas e configuradas corretamente.
    """
    dependencies = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("plotly.graph_objects", "plotly"),
        ("plotly.io", "plotly"),
        ("plotly.express", "plotly"),
        ("kaleido.scopes.plotly", "kaleido"),
        ("weasyprint", "weasyprint")
    ]
    
    missing = []
    
    for module_name, package_name in dependencies:
        try:
            importlib.import_module(module_name)
            logger.info(f"✓ {package_name} está instalado")
        except ImportError:
            logger.error(f"✗ {package_name} não está instalado")
            missing.append(package_name)
    
    if missing:
        logger.error("Dependências ausentes. Instale com:")
        for package in missing:
            logger.error(f"    pip install {package}")
        
        # Verificação especial para kaleido
        if "kaleido" in missing:
            logger.error("\nObservação: O Kaleido é essencial para a conversão de gráficos Plotly em imagens.")
            logger.error("Instale com: pip install -U kaleido")
        
        return False
    
    # Teste especial para kaleido
    try:
        import plotly.graph_objects as go
        from kaleido.scopes.plotly import PlotlyScope
        
        # Testar geração de imagem
        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 3, 2]))
        scope = PlotlyScope()
        scope.transform(fig, format="png")
        logger.info("✓ Kaleido está funcionando corretamente")
    except Exception as e:
        logger.error(f"✗ Problema com Kaleido: {str(e)}")
        logger.error("Tente reinstalar: pip install -U kaleido")
        return False
    
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if check_dependencies():
        print("Todas as dependências estão instaladas e configuradas corretamente.")
        sys.exit(0)
    else:
        print("Algumas dependências estão ausentes ou mal configuradas.")
        sys.exit(1)