from utils import *
from config import *
import os
from glob import glob
from langchain.vectorstores.chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_experimental.text_splitter import SemanticChunker
import re
from uuid import uuid4
import shutil
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from sentence_transformers import CrossEncoder
from langchain.schema import Document

class SmartDocumentProcessor:
    def __init__(self):
        # 初始化嵌入模型，使用HuggingFace的BAAI/bge-small-zh-v1.5模型-这个模型专为RAG而生
        self.embed_model = get_embeddings_model()

    def _detect_content_type(self, text):
        """动态内容类型检测"""
        # 如果文本包含代码相关模式（如def、import、print或代码示例）标记为代码
        if re.search(r'def |import |print\(|代码示例', text):
            return "code"
        elif re.search(r'\|.+\|', text) and '%' in text:  # 如果文本包含表格相关模式（如|和百分比），标记为表格
            return "table"
        return "normal"  # 如果不满足上述条件，标记为普通文本

    def process_documents(self):
        # 加载文档
        # 创建加载器列表，处理知识库中的PDF和文本文件
        loaders = [
            DirectoryLoader(INPUT_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
            DirectoryLoader(INPUT_DIR, glob="**/*.txt", loader_cls=TextLoader)
        ]
        # 初始化空列表，用于存储加载的所有文档
        documents = []
        # 遍历每个加载器，加载文档并添加到documents列表
        for loader in loaders:
            documents.extend(loader.load())

        # 创建语义分块器，使用嵌入模型进行语义分块
        chunker = SemanticChunker(
            embeddings=self.embed_model,  # 使用我们的嵌入模型
            breakpoint_threshold_amount=82,  # 设置断点阈值
            add_start_index=True  # 启用添加起始索引功能
        )
        base_chunks = chunker.split_documents(documents)  # 使用语义分块器将文档分割为基本块

        # 二次动态分块
        # 初始化最终分块列表，用于存储二次分块结果
        final_chunks = []
        # 遍历每个基本块，进行二次动态分块
        for chunk in base_chunks:
            content_type = self._detect_content_type(chunk.page_content)
            if content_type == "code":
                # 如果是代码，设置较小的块大小和重叠，用于保持上下文
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=256, chunk_overlap=64)
            elif content_type == "table":
                # 如果是表格，设置中等块大小和重叠
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=384, chunk_overlap=96)
            else:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=512, chunk_overlap=128)
                # 如果是普通文本，设置较大的块大小和重叠
            final_chunks.extend(splitter.split_documents([chunk]))
            # 使用适当的分割器将块分割为最终块，并添加到列表
        # 遍历最终块列表，为每个块添加元数据
        for i, chunk in enumerate(final_chunks):
            chunk.metadata.update({
                "chunk_id": f"chunk_{i}",
                "content_type": self._detect_content_type(chunk.page_content)
            })  # 更新块的元数据，添加唯一ID和内容类型

        return final_chunks

    def process_singe_file(self,loader):
        documents = loader.load()
        base_chunks = SemanticChunker(
            embeddings=self.embed_model,
            breakpoint_threshold_amount=82,
            add_start_index=True
        ).split_documents(documents)

        final_chunks = []
        for chunk in base_chunks:
            content_type = self._detect_content_type(chunk.page_content)
            if content_type == "code":
                splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=64)
            elif content_type == "table":
                splitter = RecursiveCharacterTextSplitter(chunk_size=384, chunk_overlap=96)
            else:
                splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=128)
            final_chunks.extend(splitter.split_documents([chunk]))

        # 添加元数据
        for i, chunk in enumerate(final_chunks):
            chunk.metadata.update({
                "chunk_id": f"chunk_{uuid4()}",
                "content_type": self._detect_content_type(chunk.page_content)
            })
        return final_chunks
    def save_temp_file(self,file):
        # 创建一个临时目录存储上传文件
        temp_dir = "./temp_upload"
        os.makedirs(temp_dir, exist_ok=True)

        # 生成唯一文件名并保存
        temp_file_path = os.path.join(temp_dir, f"{uuid4()}_{file.filename}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 检测文件类型，选择对应 loader
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(temp_file_path)
        elif file.filename.endswith(".txt"):
            loader = TextLoader(temp_file_path)
        else:
            return {"error": "Unsupported file type. Only PDF and TXT are supported."},temp_file_path
        return loader,temp_file_path

class HybridRetriever:
    def __init__(self, chunks=None, use_existing_db=True):
        embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_PATH)

        if use_existing_db:
            # 加载已有 Chroma 向量数据库
            self.vector_db = Chroma(
                persist_directory=VECTOR_DIR,
                embedding_function=embed_model
            )
            # 从 Chroma 恢复文档内容
            docs_raw = self.vector_db.get()
            chunks = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(docs_raw["documents"], docs_raw["metadatas"])
            ]
        else:
            # 第一次构建数据库
            self.vector_db = Chroma.from_documents(
                chunks,
                embedding=embed_model,
                persist_directory=VECTOR_DIR
            )

        # 初始化 BM25 检索器
        self.bm25_retriever = BM25Retriever.from_documents(chunks, k=5)

        # 混合检索器（向量 + BM25）
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[
                self.vector_db.as_retriever(search_kwargs={"k": 5}),
                self.bm25_retriever
            ],
            weights=[0.6, 0.4]
        )

        # 重排序模型
        self.reranker = CrossEncoder(
            RERANKER_PATH,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

    def retrieve(self, query, top_k=3):
        # 第一阶段：使用混合检索器获取相关文档
        docs = self.ensemble_retriever.get_relevant_documents(query)

        # 第二阶段：为查询和每个文档创建配对，用于重排序
        pairs = [[query, doc.page_content] for doc in docs]
        scores = self.reranker.predict(pairs)
        # 使用重排序模型预测配对的分数
        ranked_docs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

        #过滤低分数文档
        high_ranked_docs = []
        for doc, score in ranked_docs:
            if score<0.8:
                break
            high_ranked_docs.append(doc)

        # 返回top_k结果
        return high_ranked_docs[:min(len(high_ranked_docs),top_k)]


if __name__ == '__main__':
    processor = SmartDocumentProcessor()
    chunks = processor.process_documents()
    retriever = HybridRetriever(chunks,use_existing_db=False)
