# ./chatbot/RAG/utils.py

import json
import logging
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_community.retrievers import TFIDFRetriever

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """
    Loads the configuration from a JSON file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: A dictionary containing the loaded configuration.
    """
    with open(config_path, 'r') as config_file:
        logger.info("Configuración 'config' cargada correctamente.")
        return json.load(config_file)

def load_documents_database(directory: str, chunk_size: int, chunk_overlap: int) -> TFIDFRetriever:
    """
    Loads and prepares the document database for retrieval.

    Args:
        directory (str): The path to the directory containing the PDF documents.
        chunk_size (int): The size of chunks when splitting documents.
        chunk_overlap (int): The overlap size between chunks of documents.

    Returns:
        TFIDFRetriever: A TFIDFRetriever object for document retrieval.
    """
    docs = PyPDFDirectoryLoader(directory).load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    logger.info('Documentos PDF cargados correctamente.')
    
    return TFIDFRetriever.from_documents(text_splitter.split_documents(docs))
