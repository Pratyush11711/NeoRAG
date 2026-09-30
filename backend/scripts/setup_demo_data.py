import os
import io
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image as PILImage, ImageDraw

def create_demo_image(output_path: str):
    """Creates a diagram image representing the Transformer architecture."""
    img = PILImage.new("RGB", (400, 300), color=(240, 245, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw Encoder box
    draw.rectangle([50, 40, 180, 260], fill=(220, 230, 250), outline=(50, 80, 180), width=2)
    draw.text((75, 50), "Encoder", fill=(20, 30, 80))
    draw.rectangle([65, 80, 165, 130], fill=(255, 255, 255), outline=(100, 100, 100))
    draw.text((70, 95), "Multi-Head Attention", fill=(0, 0, 0))
    draw.rectangle([65, 150, 165, 200], fill=(255, 255, 255), outline=(100, 100, 100))
    draw.text((70, 165), "Feed Forward", fill=(0, 0, 0))

    # Draw Decoder box
    draw.rectangle([220, 40, 350, 260], fill=(250, 230, 220), outline=(200, 80, 50), width=2)
    draw.text((245, 50), "Decoder", fill=(100, 30, 20))
    draw.rectangle([235, 75, 335, 115], fill=(255, 255, 255), outline=(100, 100, 100))
    draw.text((240, 85), "Masked Attention", fill=(0, 0, 0))
    draw.rectangle([235, 130, 335, 170], fill=(255, 255, 255), outline=(100, 100, 100))
    draw.text((240, 140), "Cross Attention", fill=(0, 0, 0))
    draw.rectangle([235, 185, 335, 225], fill=(255, 255, 255), outline=(100, 100, 100))
    draw.text((240, 195), "Feed Forward", fill=(0, 0, 0))

    img.save(output_path)
    return output_path

def generate_attention_pdf(dest_pdf_path: str):
    """Generates a multimodal PDF for 'Attention Is All You Need'."""
    os.makedirs(os.path.dirname(dest_pdf_path), exist_ok=True)
    img_path = str(Path(dest_pdf_path).parent / "transformer_arch.png")
    create_demo_image(img_path)

    doc = SimpleDocTemplate(dest_pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=8
    )
    body_style = styles['Normal']

    # Title & Authors
    story.append(Paragraph("Attention Is All You Need", title_style))
    story.append(Paragraph("Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin", body_style))
    story.append(Spacer(1, 14))

    # Abstract
    story.append(Paragraph("Abstract", heading_style))
    abstract_text = (
        "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks "
        "that include an encoder and a decoder. The best performing models also connect the encoder and decoder "
        "through an attention mechanism. We propose a new simple network architecture, the Transformer, "
        "based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. "
        "Experiments on two machine translation tasks show these models to be superior in quality while being "
        "more parallelizable and requiring significantly less time to train."
    )
    story.append(Paragraph(abstract_text, body_style))
    story.append(Spacer(1, 14))

    # Section 1: Introduction
    story.append(Paragraph("1. Introduction", heading_style))
    intro_text = (
        "Recurrent neural networks, long short-term memory and gated recurrent neural networks have been firmly "
        "established as state of the art approaches in sequence modeling. The fundamental constraint of sequential "
        "computation remains an obstacle to parallel training. In this work we propose the Transformer, a model "
        "architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies "
        "between input and output."
    )
    story.append(Paragraph(intro_text, body_style))
    story.append(Spacer(1, 14))

    # Section 2: Model Architecture
    story.append(Paragraph("2. Model Architecture", heading_style))
    arch_text = (
        "The two main components of the Transformer architecture are the Encoder and the Decoder. "
        "The Encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers: "
        "a multi-head self-attention mechanism, and a simple, position-wise fully connected feed-forward network. "
        "The Decoder is also composed of a stack of N = 6 identical layers with an additional third sub-layer "
        "performing multi-head attention over the output of the encoder stack."
    )
    story.append(Paragraph(arch_text, body_style))
    story.append(Spacer(1, 14))

    # Image
    story.append(Paragraph("Figure 1: The Transformer - Model Architecture Diagram", styles['Italic']))
    story.append(Image(img_path, width=320, height=240))
    story.append(Spacer(1, 14))

    # Section 3: Results Table
    story.append(Paragraph("3. Results and Evaluation", heading_style))
    table_data = [
        ["Model", "BLEU (EN-DE)", "BLEU (EN-FR)", "Training Cost (FLOPs)"],
        ["ByteNet", "23.75", "-", "9.5e18"],
        ["ConvS2S", "25.16", "40.46", "9.6e18"],
        ["Transformer (base model)", "27.3", "38.1", "3.3e18"],
        ["Transformer (big model)", "28.4", "41.8", "2.3e19"]
    ]
    t = Table(table_data, colWidths=[150, 100, 100, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t)

    doc.build(story)
    print(f"Generated demo PDF at: {dest_pdf_path}")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    docs_dir = base_dir / "docs"
    pdf_path = docs_dir / "attention-is-all-you-need.pdf"
    generate_attention_pdf(str(pdf_path))
