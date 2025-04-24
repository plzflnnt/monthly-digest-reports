# test_charts.py
from modules.chart_generator import create_trend_chart, create_devices_chart
import json

# Carregar dados de exemplo
with open("api_data_analytics.json", "r") as f:
    analytics_data = json.load(f)

# Testar geração de gráfico
chart_url = create_trend_chart(analytics_data.get('daily_metrics', []), save_debug=True)
print(f"Gráfico gerado: {'Sim' if chart_url else 'Não'}")