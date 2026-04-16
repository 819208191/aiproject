from langchain_huggingface.llms import HuggingFacePipeline
from langchain import PromptTemplate
from langchain.chains import LLMChain,LLMRequestsChain
from transformers import AutoModelForCausalLM, AutoTokenizer,pipeline
from langchain.embeddings import HuggingFaceEmbeddings
import torch
from config import *


import os

device = "cuda" if torch.cuda.is_available() else "cpu"

def get_embeddings_model():
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_PATH,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"batch_size": 16}
    )
    return embedding
