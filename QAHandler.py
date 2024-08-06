import logging
from langchain.chains import RetrievalQA
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Cohere
from langchain_community.retrievers import TFIDFRetriever
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter


class QAHandler:
    def __init__(self, cohere_api_key, docs_path, model="command-nightly", temperature=0, max_tokens=400, chunk_size=500, chunk_overlap=0):
        self.cohere_api_key = cohere_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.docs_path = docs_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
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
            template=self.prompt_template,
            input_variables=["context", "question"]
        )

        self.documents = self.load_documents()
        self.load_db()
        self.load_llm_model()
        self.load_qa()

    def load_db(self):
        self.db = TFIDFRetriever.from_documents(self.documents)

    def load_llm_model(self):
        self.llm_model = Cohere(
            model=self.model,
            temperature=self.temperature,
            cohere_api_key=self.cohere_api_key,
            max_tokens=self.max_tokens
        )
    
    def load_qa(self):
        self.qa = RetrievalQA.from_chain_type(
            llm=self.llm_model,
            chain_type="stuff",
            retriever=self.db,
            verbose=False,
            chain_type_kwargs={
                "verbose": False,
                "prompt": self.prompt
            }
        )

    def load_documents(self):
        try:
            loader = PyPDFDirectoryLoader(self.docs_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
            texts = text_splitter.split_documents(docs)
            return texts
        except Exception as e:
            logging.error(f"Error loading documents: {e}")
            return []

    def update_documents(self):
        self.documents = self.load_documents()
        self.db = TFIDFRetriever.from_documents(self.documents)
        self.load_qa()
        
    def get_answer(self, question):
        try:
            return self.qa.run({"query": question})
        except Exception as e:
            logging.error(f"Error getting answer: {e}")
            return {"error": "An error occurred while processing the request."}