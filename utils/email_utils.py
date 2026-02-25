import re
from bs4 import BeautifulSoup

def optimize_html_for_email(html_content):
    """
    Otimiza o HTML para ser exibido em clientes de e-mail.
    Simplifica o CSS e adapta o layout para melhor compatibilidade.
    
    Args:
        html_content: Conteúdo HTML original
        
    Returns:
        str: HTML otimizado para e-mail
    """
    try:
        # Parse o HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Adicionar meta tags para compatibilidade com e-mail
        head = soup.head
        if head:
            # Adicionar meta tags para viewport e compatibilidade
            meta_viewport = soup.new_tag("meta")
            meta_viewport["name"] = "viewport"
            meta_viewport["content"] = "width=device-width, initial-scale=1.0"
            
            meta_format = soup.new_tag("meta")
            meta_format["http-equiv"] = "Content-Type"
            meta_format["content"] = "text/html; charset=UTF-8"
            
            head.insert(0, meta_viewport)
            head.insert(0, meta_format)
        
        # 2. Substituir variáveis CSS por valores diretos
        css_variables = {
            "--primary": "#111218",
            "--secondary": "#935FA7",
            "--light": "#FDF7FA",
            "--accent": "#F2C354",
            "--chart-accent1": "#FF6B6C",
            "--chart-accent2": "#A1E8CC"
        }
        
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            css_content = style_tag.string
            if css_content:
                # Substituir variáveis CSS por valores diretos
                for var_name, hex_value in css_variables.items():
                    css_content = css_content.replace(f"var({var_name})", hex_value)
                
                # Atualizar o conteúdo da tag style
                style_tag.string = css_content
        
        # 3. Mover alguns estilos críticos para inline
        # Processar cards de destaque (highlight-cards)
        highlight_cards = soup.select('.highlight-cards')
        for card_container in highlight_cards:
            # Adicionar CSS inline para o contêiner
            card_container['style'] = "display: block; margin-bottom: 40px;"
            
            # Processar cada card individualmente
            cards = card_container.select('.card')
            for card in cards:
                card['style'] = "background: white; border-radius: 8px; padding: 25px; border: 1px solid #eee; margin: 10px 0; position: relative; overflow: hidden;"
                
                # Processar elementos dentro do card
                h3 = card.select_one('h3')
                if h3:
                    h3['style'] = "font-size: 15px; color: #935FA7; margin-bottom: 8px;"
                
                value_div = card.select_one('.value')
                if value_div:
                    value_div['style'] = "font-size: 28px; font-weight: bold; color: #111218; margin-bottom: 5px;"
                
                change_div = card.select_one('.change')
                if change_div:
                    base_style = "font-size: 14px; display: block;"
                    if 'positive' in change_div.get('class', []):
                        change_div['style'] = base_style + " color: #2ecc71;"
                    elif 'negative' in change_div.get('class', []):
                        change_div['style'] = base_style + " color: #e74c3c;"
                    else:
                        change_div['style'] = base_style
        
        # 4. Otimizar gráficos e imagens
        # Garantir que imagens nos gráficos tenham largura máxima
        charts = soup.select('.chart-container')
        for chart in charts:
            chart['style'] = "margin: 20px 0; display: block;"
            
            # Processar imagens dentro dos gráficos
            images = chart.find_all('img')
            for img in images:
                img['style'] = "width: 100%; max-width: 100%; height: auto; display: block;"
                # Garantir que img tenha alt text
                if not img.get('alt'):
                    img['alt'] = "Gráfico de dados"
        
        # 5. Otimizar tabelas de dados
        tables = soup.select('.data-table')
        for table in tables:
            table['style'] = "width: 100%; border-collapse: collapse; margin: 20px 0;"
            table['cellspacing'] = "0"
            
            # Processar cabeçalhos e células da tabela
            ths = table.find_all('th')
            for th in ths:
                th['style'] = "padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; background-color: #f9f9f9; color: #111218; font-weight: 600;"
            
            tds = table.find_all('td')
            for td in tds:
                td['style'] = "padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee;"
            
            # Processar rankings
            ranks = table.select('.rank')
            for rank in ranks:
                rank['style'] = "width: 40px; height: 25px; background-color: #111218; color: white; border-radius: 4px; display: inline-block; text-align: center; line-height: 25px; font-weight: 600;"
        
        # 6. Otimizar seções do relatório
        sections = soup.select('.report-section')
        for section in sections:
            section['style'] = "background: white; border-radius: 8px; padding: 25px; margin-bottom: 40px; border: 1px solid #eee;"
            
            # Processar cabeçalhos de seção
            section_header = section.select_one('.section-header')
            if section_header:
                section_header['style'] = "display: block; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid #eee;"
                
                # Processar ícone
                icon = section_header.select_one('.icon')
                if icon:
                    icon['style'] = "width: 40px; height: 40px; background-color: #935FA7; border-radius: 50%; display: inline-block; text-align: center; line-height: 40px; margin-right: 15px; color: white; font-size: 18px;"
                
                # Processar título
                h2 = section_header.select_one('h2')
                if h2:
                    h2['style'] = "font-size: 22px; font-weight: 600; display: inline-block; vertical-align: middle;"
        
        # 7. Otimizar caixas de resumo
        summary_boxes = soup.select('.summary-box')
        for box in summary_boxes:
            box['style'] = "background-color: #f9f9f9; border-left: 4px solid #935FA7; padding: 15px 20px; margin: 20px 0; border-radius: 0 4px 4px 0;"
            
            # Processar título
            h3 = box.select_one('h3')
            if h3:
                h3['style'] = "font-size: 16px; margin-bottom: 8px; color: #935FA7;"
            
            # Processar texto
            p = box.select_one('p')
            if p:
                p['style'] = "font-size: 14px; line-height: 1.6;"
        
        # 8. Otimizar destaques anuais
        highlights = soup.select('.year-highlight')
        for highlight in highlights:
            highlight['style'] = "background-color: #111218; color: white; padding: 25px; border-radius: 8px; margin: 30px 0; text-align: center;"
            
            # Processar título
            h3 = highlight.select_one('h3')
            if h3:
                h3['style'] = "font-size: 18px; margin-bottom: 10px; color: #F2C354;"
            
            # Processar contador
            counter = highlight.select_one('.counter')
            if counter:
                counter['style'] = "font-size: 36px; font-weight: bold; margin: 15px 0;"
        
        # 9. Adicionar wrapper para garantir compatibilidade
        body = soup.body
        if body:
            # Criar um novo div para envolver todo o conteúdo
            wrapper = soup.new_tag('div')
            wrapper['style'] = "width: 100%; max-width: 800px; margin: 0 auto; font-family: Arial, Helvetica, sans-serif; color: #333;"
            
            # Mover todo o conteúdo do body para o wrapper
            for child in list(body.children):
                wrapper.append(child)
            
            # Adicionar o wrapper ao body
            body.append(wrapper)
        
        # 10. Adicionar rodapé de e-mail para evitar respostas
        if body:
            footer = soup.new_tag('div')
            footer['style'] = "text-align: center; padding: 30px 0; color: #777; font-size: 12px; border-top: 1px solid #eee; margin-top: 30px;"
            footer.string = "Este é um e-mail automático. Por favor, não responda diretamente a este e-mail."
            body.append(footer)
        
        # Retornar o HTML otimizado
        return str(soup)
    
    except Exception as e:
        import logging
        logging.error(f"Erro ao otimizar HTML para e-mail: {str(e)}")
        # Em caso de erro, retornar o HTML original
        return html_content