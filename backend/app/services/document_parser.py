import logging
import os
import base64
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ParsedElement:
    def __init__(
        self,
        element_id: str,
        category: str,
        text: str,
        metadata: Dict[str, Any],
        table_html: Optional[str] = None,
        image_base64: Optional[str] = None
    ):
        self.element_id = element_id
        self.category = category  # e.g., "Title", "NarrativeText", "Table", "Image"
        self.text = text
        self.metadata = metadata
        self.table_html = table_html
        self.image_base64 = image_base64

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_id": self.element_id,
            "category": self.category,
            "text": self.text,
            "metadata": self.metadata,
            "table_html": self.table_html,
            "has_image": bool(self.image_base64)
        }

class DocumentParser:
    """
    Parses PDF and other documents using Unstructured with multimodal extraction:
    text, titles, tables (HTML), and images (base64).
    """

    def parse_pdf(self, file_path: str) -> List[Any]:
        """
        Partitions PDF using unstructured partition_pdf with fallback if hi_res dependencies
        (e.g., poppler/tesseract) are not present on the OS.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        elements = []
        try:
            from unstructured.partition.pdf import partition_pdf
            logger.info(f"Attempting hi_res partition_pdf on {file_path}")
            elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",
                infer_table_structure=True,
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True
            )
            logger.info(f"Successfully partitioned {len(elements)} elements using hi_res strategy.")
        except Exception as e:
            logger.warning(
                f"hi_res partitioning encountered an error ({type(e).__name__}: {e}). "
                "Falling back to fast/auto strategy..."
            )
            try:
                from unstructured.partition.pdf import partition_pdf
                elements = partition_pdf(
                    filename=file_path,
                    strategy="fast"
                )
                logger.info(f"Successfully partitioned {len(elements)} elements using fast strategy.")
            except Exception as e_fast:
                logger.warning(f"Fast partitioning also failed: {e_fast}. Falling back to pypdf extraction.")
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    logger.info(f"Extracting {len(reader.pages)} pages via pypdf fallback.")
                    class MockElement:
                        def __init__(self, text, page_num):
                            self.text = text
                            self.category = "NarrativeText"
                            self.metadata = type("MockMeta", (), {
                                "to_dict": lambda s: {"page_number": page_num},
                                "page_number": page_num,
                                "text_as_html": None,
                                "image_base64": None
                            })()
                    for p_num, page in enumerate(reader.pages, start=1):
                        p_text = page.extract_text()
                        if p_text:
                            elements.append(MockElement(p_text, p_num))
                except Exception as e_pypdf:
                    logger.error(f"All PDF partition strategies failed: {e_pypdf}")
                    raise e_pypdf

        return elements

    def extract_structured_elements(self, raw_elements: List[Any]) -> List[ParsedElement]:
        """
        Converts unstructured raw elements into standardized ParsedElement objects,
        preserving table HTML and image base64.
        """
        parsed_list: List[ParsedElement] = []

        for idx, el in enumerate(raw_elements):
            category = getattr(el, "category", type(el).__name__)
            text = str(el.text) if hasattr(el, "text") and el.text else str(el)
            meta = getattr(el, "metadata", None)
            meta_dict = meta.to_dict() if meta and hasattr(meta, "to_dict") else {}
            
            # Extract page number
            page_number = meta_dict.get("page_number")
            element_id = getattr(el, "id", f"el_{idx}")

            # Extract table HTML
            table_html = None
            if category.lower() == "table" or "table" in type(el).__name__.lower():
                category = "Table"
                if meta and hasattr(meta, "text_as_html") and meta.text_as_html:
                    table_html = meta.text_as_html
                elif meta_dict.get("text_as_html"):
                    table_html = meta_dict.get("text_as_html")
                else:
                    # Construct basic HTML table representation if missing
                    table_html = f"<table><tr><td>{text}</td></tr></table>"

            # Extract image base64 payload
            image_base64 = None
            if category.lower() == "image" or "image" in type(el).__name__.lower():
                category = "Image"
                if meta and hasattr(meta, "image_base64") and meta.image_base64:
                    image_base64 = meta.image_base64
                elif meta_dict.get("image_base64"):
                    image_base64 = meta_dict.get("image_base64")

            parsed_list.append(ParsedElement(
                element_id=element_id,
                category=category,
                text=text,
                metadata=meta_dict,
                table_html=table_html,
                image_base64=image_base64
            ))

        return parsed_list

document_parser = DocumentParser()
