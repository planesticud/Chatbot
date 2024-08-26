from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.retrievers import TFIDFRetriever
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from .LLM import get_llm

class QAHandler:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(QAHandler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self,
                 llm_provier = 'cohere',
                 temperature = 0,
                 max_tokens = 500,
                 chunk_size = 500,
                 chunk_overlap = 0):
        
        # Evitar la inicialización múltiple en caso de ser llamado varias veces
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.load_prompt_template()
        self.load_documents_database(chunk_size, chunk_overlap)
        self.load_llm(llm_provier, temperature, max_tokens)
        self.load_qa()
        
    def load_prompt_template(self):
        self.prompt_template = """
        You are an AI personal assistant designed to answer document-based questions. You have access to a set of documents but cannot store the chat. Your idea is that you can solve the necessary questions

        Instructions:

        If the user's question requires specific information from the documents provided, respond only on the content of those documents. Please do not generate an answer that is not supported by the documents.
        If you cannot find the answer to the user's question in the documents provided, please respond by inviting the user to visit our website https://planstic.udistrital.edu.co/ or by requesting a ticket on our 'Mesa de Ayuda' si es miembro de la universidad https://mesadeayuda.planestic.udistrital.edu.co/.
        Use bullets only when necessary to create a list.
        Use the following documents and chat history to answer the question:

        Question: {question}

        Documents: {context}
        """
        self.prompt = PromptTemplate(
            template = self.prompt_template,
            input_variables = ["context", "question"]
        )

    def load_documents_database(self,
                                chunk_size,
                                chunk_overlap):
        try:
            docs = PyPDFDirectoryLoader('./chatbot/docs/').load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                           chunk_overlap=chunk_overlap)
            self.tfidf_retriever = TFIDFRetriever.from_documents(text_splitter.split_documents(docs))
            print('INFO: Base de datos con documentos cargada correctamente')
        except Exception as e:
            print('ERROR: Ha ocurrido un error en carga de la base de datos con documentos.')
            print(e)
        
    
    def load_llm(self,
                 llm_provier,
                 temperature,
                 max_tokens):
        try:
            self.llm = get_llm(
                max_tokens=max_tokens,
                temperature=temperature)
            print('INFO: LLM cargado correctamente.')
        except Exception as e:
            print(f'ERROR: Ha ocurrido un error en la carga del LLM {llm_provier}.')
            print(e)
        
    def load_qa(self):
        try:
            self.qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.tfidf_retriever,
                verbose=False,
                chain_type_kwargs={
                    "verbose": False,
                    "prompt": self.prompt
                }
            )
            print(f'INFO: RetrievalQA cargado correctamente.')
        except Exception as e:
            print(f'ERROR: Ha ocurrido un error al cargar el RetrievalQA.')
            print(e)

    def get_answer(self, query):
        try:
            return self.qa.run(
                {'query': query})
        except Exception as e:
            print('ERROR: Ha ocurrido un error en la ejecución del Query')
            print(e)