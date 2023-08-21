import os
import openai
import PyPDF2
import re
from chromadb import Client, Settings
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get('OPENAI_API_KEY')
openai.api_key = key
# ef = embedding_functions.OpenAIEmbeddingFunction(api_key=key)
ef = embedding_functions.ONNXMiniLM_L6_V2()
messages = []

# collection = CreateClient.create_collection()

client = Client(settings = Settings(persist_directory="./", is_persistent=True))
collection_ = client.get_or_create_collection(name="test", embedding_function=ef)

def clear_coll():
    client.delete_collection(collection_.name)
    print("Collection deleted successfully")
 

def verify_pdf_path(file_path):
    try:
        print(file_path)
        with open(file_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            if len(pdf_reader.pages) > 0:
                pass
            else:
                raise("PDF file is empty")
    except PyPDF2.errors.PdfReadError:
        raise PyPDF2.errors.PdfReadError("Invalid PDF file")
    except FileNotFoundError:
        raise FileNotFoundError("File not found, check file address again")
    except Exception as e:
        raise(f"Error: {e}")

def get_text_chunks(text: str, word_limit: int) -> List[str]:
    """
    Divide a text into chunks with a specified word limit while ensuring each chunk contains complete sentences.
    
    Parameters:
        text (str): The entire text to be divided into chunks.
        word_limit (int): The desired word limit for each chunk.
    
    Returns:
        List[str]: A list containing the chunks of texts with the specified word limit and complete sentences.
    """
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    chunks = []
    current_chunk = []

    for sentence in sentences:
        words = sentence.split()
        if len(" ".join(current_chunk + words)) <= word_limit:
            current_chunk.extend(words)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = words

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def load_pdf(file: str, word: int) -> Dict[int, List[str]]:
    reader = PdfReader(file)
    documents = {}
    for page_no in range(len(reader.pages)):
        page = reader.pages[page_no]
        texts = page.extract_text()
        text_chunks = get_text_chunks(texts, word)
        documents[page_no] = text_chunks
    return documents


def add_text_to_collection(file: str, word: int = 200) -> None:
    docs = load_pdf(file, word)
    docs_strings = []
    ids = []
    metadatas = []
    id = 0
    for page_no in docs.keys():      
        for doc in docs[page_no]:
            docs_strings.append(doc)
            metadatas.append({'page_no':page_no})
            ids.append(id)
            id+=1

    collection_.add(
        ids = [str(id) for id in ids],
        documents = docs_strings,
        metadatas = metadatas,
    )
    return "PDF embeddings successfully added to collection"

def query_collection(texts: str, n: int) -> List[str]:
    result = collection_.query(
                  query_texts = texts,
                  n_results = n,
                 )
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    resulting_strings = []
    for page_no, text_list in zip(metadatas, documents):
        resulting_strings.append(f"Page {page_no['page_no']}: {text_list}")
    # print(resulting_strings)
    return resulting_strings

def get_response(queried_texts: List[str],) -> List[Dict]:
    global messages
    messages = [
                {"role": "system", "content": "You are a helpful assistant. And will always answer the question asked in 'ques:' and \
                  will quote the page number while answering to any questions, It is always at the start of the prompt in the format 'page n'."},
                {"role": "user", "content": ''.join(queried_texts)}
          ]

    response = openai.ChatCompletion.create(
                            model = "gpt-3.5-turbo",
                            messages = messages,
                            temperature=0.2,               
                     )
    response_msg = response.choices[0].message.content
    messages = messages + [{"role":'assistant', 'content': response_msg}]
    return response_msg

def get_answer(query: str, n: int):
    queried_texts = query_collection(texts = query, n = n)
    queried_string = [''.join(text) for text in queried_texts]
    queried_string = queried_string[0] + f"ques: {query}"
    answer = get_response(queried_texts = queried_string,)
    return answer


    

