"""Document parsing, chunking, and embedding services."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentParser:
    """多格式文档解析器"""

    @staticmethod
    def parse(file_path: str, file_type: str) -> str:
        if file_type == 'pdf':
            return DocumentParser._parse_pdf(file_path)
        elif file_type == 'docx':
            return DocumentParser._parse_docx(file_path)
        elif file_type in ('md', 'markdown') or file_type == 'txt':
            return Path(file_path).read_text(encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return '\n\n'.join(pages)

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        from docx import Document
        doc = Document(file_path)
        return '\n\n'.join(p.text for p in doc.paragraphs if p.text.strip())


class ChunkingStrategy:
    """多种分块策略"""

    @staticmethod
    def fixed_size(text: str, size: int = 512, overlap: int = 64) -> list[str]:
        """固定长度分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - overlap
        return chunks

    @staticmethod
    def recursive(text: str, size: int = 512, overlap: int = 64) -> list[str]:
        """递归分块——按段落/句子层级切分"""
        separators = ['\n\n', '\n', '。', '！', '？', '.', '!', '?', ' ', '']

        def _split(text: str, sep_idx: int) -> list[str]:
            if len(text) <= size or sep_idx >= len(separators):
                return [text] if text.strip() else []

            sep = separators[sep_idx]
            parts = text.split(sep)
            chunks = []
            current = ''

            for part in parts:
                candidate = current + sep + part if current else part
                if len(candidate) <= size:
                    current = candidate
                else:
                    if current:
                        chunks.append(current.strip())
                    if len(part) > size:
                        chunks.extend(_split(part, sep_idx + 1))
                        current = ''
                    else:
                        current = part

            if current.strip():
                chunks.append(current.strip())

            # 应用 overlap
            if overlap > 0 and len(chunks) > 1:
                overlapped = [chunks[0]]
                for i in range(1, len(chunks)):
                    prev_tail = chunks[i - 1][-overlap:]
                    overlapped.append(prev_tail + chunks[i])
                return overlapped

            return chunks

        return _split(text, 0)

    @staticmethod
    def semantic(text: str, model=None, threshold: float = 0.5) -> list[str]:
        """语义分块——基于句子 embedding 相似度切分"""
        import re
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return sentences

        from sentence_transformers import SentenceTransformer, util
        if model is None:
            model = SentenceTransformer('BAAI/bge-m3')

        embeddings = model.encode(sentences, normalize_embeddings=True)
        chunks = []
        current_chunk = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = util.cos_sim(embeddings[i - 1], embeddings[i]).item()
            if sim >= threshold:
                current_chunk.append(sentences[i])
            else:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks


class EmbeddingService:
    """本地 Embedding 服务（单例模式）"""

    _model = None

    @classmethod
    def get_model(cls, model_name: str = 'BAAI/bge-m3'):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(model_name)
        return cls._model

    @classmethod
    def encode(cls, texts: list[str], model_name: str = 'BAAI/bge-m3') -> list[list[float]]:
        model = cls.get_model(model_name)
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
