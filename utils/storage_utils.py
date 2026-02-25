from google.cloud import storage
import io
import os
import logging

def upload_file(file_content, destination_path, bucket_name):
    """
    Faz upload de um arquivo para o Cloud Storage.
    
    Args:
        file_content: Conteúdo do arquivo (bytes ou buffer)
        destination_path: Caminho de destino no bucket
        bucket_name: Nome do bucket
    
    Returns:
        str: URL do arquivo no Cloud Storage
    """
    try:
        # Inicializar cliente do Storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Criar blob e fazer upload
        blob = bucket.blob(destination_path)
        
        # Verificar se file_content é um buffer ou bytes
        if isinstance(file_content, io.BytesIO) or isinstance(file_content, io.StringIO):
            blob.upload_from_file(file_content)
        else:
            blob.upload_from_string(file_content)
        
        # Retornar URL do arquivo
        return f"gs://{bucket_name}/{destination_path}"
    
    except Exception as e:
        logging.error(f"Erro ao fazer upload do arquivo: {str(e)}")
        raise

def download_file(source_path, bucket_name):
    """
    Faz download de um arquivo do Cloud Storage.
    
    Args:
        source_path: Caminho do arquivo no bucket
        bucket_name: Nome do bucket
    
    Returns:
        bytes: Conteúdo do arquivo
    """
    try:
        # Inicializar cliente do Storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Obter blob e fazer download
        blob = bucket.blob(source_path)
        content = blob.download_as_bytes()
        
        return content
    
    except Exception as e:
        logging.error(f"Erro ao fazer download do arquivo: {str(e)}")
        raise

def list_files(prefix, bucket_name):
    """
    Lista arquivos em um bucket do Cloud Storage.
    
    Args:
        prefix: Prefixo para filtrar arquivos
        bucket_name: Nome do bucket
    
    Returns:
        list: Lista de nomes de arquivos
    """
    try:
        # Inicializar cliente do Storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Listar blobs
        blobs = bucket.list_blobs(prefix=prefix)
        
        # Retornar nomes
        return [blob.name for blob in blobs]
    
    except Exception as e:
        logging.error(f"Erro ao listar arquivos: {str(e)}")
        raise