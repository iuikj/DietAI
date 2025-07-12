import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from shared.config.settings import get_settings

settings = get_settings()
# ✅ 你的文档路径
DOC_PATH = os.path.join(settings.DOC_PATH, "nutrition_knowledge.txt")

# ✅ Chroma 持久化路径
PERSIST_DIRECTORY = settings.VECTOR_STORE_PATH

# ✅ collection 名称（可自定义）
COLLECTION_NAME = settings.VECTOR_COLLECTION_NAME

# ✅ 读取文档
with open(DOC_PATH, "r", encoding="utf-8") as f:
    raw_text = f.read()

# ✅ 切分 chunk
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
)
chunks = text_splitter.split_text(raw_text)

# ✅ 转换为 Document 对象
docs = [Document(page_content=chunk) for chunk in chunks]

load_dotenv(f".env", override=True)
# ✅ 初始化 Embeddings
embeddings = OpenAIEmbeddings()  # 需要设置 OPENAI_API_KEY

# ✅ 创建 Chroma Vector Store（如果目录存在则会追加）
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIRECTORY,
)

# ✅ 添加文档并持久化
vectorstore.add_documents(docs)

print("✅ Chroma vector store 已保存到：", PERSIST_DIRECTORY)


# ========================
# ✅ 测试检索
# ========================
# 重新加载
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIRECTORY,
)

# 测试查询
query = "怎么平衡蛋白质、碳水和脂肪摄入？"
results = vectorstore.similarity_search(query, k=3)

print("\n=== 🔍 检索结果 ===")
for i, res in enumerate(results):
    print(f"\nChunk {i+1}:\n{res.page_content}")
