from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import tempfile, os, shutil, subprocess
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
from pikepdf import Pdf
import pytesseract

app = FastAPI()


# Helper: Save uploaded file
def save_temp(upload: UploadFile):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(upload.file.read())
    temp.close()
    return temp.name


# 1️⃣ MERGE PDF
@app.post("/merge")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    writer = PdfWriter()
    for f in files:
        path = save_temp(f)
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    out = "merged.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)



# 2️⃣ SPLIT PDF (Range: 1-3, 6, 8-10)
@app.post("/split")
async def split_pdf(file: UploadFile = File(...), pages: str = Form(...)):
    path = save_temp(file)
    reader = PdfReader(path)
    writer = PdfWriter()

    def parse_pages(p):
        result = []
        parts = p.split(",")
        for part in parts:
            if "-" in part:
                a, b = part.split("-")
                result.extend(range(int(a), int(b) + 1))
            else:
                result.append(int(part))
        return result

    page_nums = parse_pages(pages)

    for p in page_nums:
        writer.add_page(reader.pages[p - 1])

    out = "split.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)



# 3️⃣ COMPRESS PDF (Ghostscript strong compression)
@app.post("/compress-strong")
async def compress_strong(file: UploadFile = File(...)):
    path = save_temp(file)
    out = "compressed.pdf"

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/printer",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={out}",
        path
    ]
    subprocess.run(cmd)

    return FileResponse(out, filename=out)



# 4️⃣ COMPRESS PDF (Light — PikePDF)
@app.post("/compress")
async def compress_light(file: UploadFile = File(...)):
    path = save_temp(file)
    pdf = Pdf.open(path)
    pdf.save("compressed.pdf", optimize_streams=True)
    return FileResponse("compressed.pdf")



# 5️⃣ PDF ➜ IMAGES
@app.post("/pdf-to-img")
async def pdf_to_img(file: UploadFile = File(...)):
    path = save_temp(file)

    pages = convert_from_path(path)
    folder = tempfile.mkdtemp()

    for i, p in enumerate(pages):
        p.save(f"{folder}/page_{i+1}.jpg", "JPEG")

    shutil.make_archive("images", "zip", folder)

    return FileResponse("images.zip", filename="images.zip")



# 6️⃣ IMAGES ➜ PDF
@app.post("/img-to-pdf")
async def img_to_pdf(files: list[UploadFile] = File(...)):
    images = []
    for f in files:
        path = save_temp(f)
        img = Image.open(path).convert("RGB")
        images.append(img)

    out = "images_to_pdf.pdf"
    images[0].save(out, save_all=True, append_images=images[1:])
    return FileResponse(out, filename=out)



# 7️⃣ OCR PDF ➜ TEXT
@app.post("/ocr")
async def ocr_pdf(file: UploadFile = File(...)):
    path = save_temp(file)
    pages = convert_from_path(path)

    text = ""
    for p in pages:
        text += pytesseract.image_to_string(p) + "\n\n"

    open("ocr.txt", "w").write(text)
    return FileResponse("ocr.txt", filename="ocr.txt")


# 8️⃣ PDF ➜ WORD (DOCX)
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    pdf_path = save_temp(file)
    out = "output.docx"

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "docx",
        "--outdir", ".",
        pdf_path
    ]

    subprocess.run(cmd)
    return FileResponse(out, filename=out)



# 9️⃣ WORD ➜ PDF
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    doc_path = save_temp(file)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", ".",
        doc_path
    ]

    subprocess.run(cmd)

    out = os.path.splitext(os.path.basename(doc_path))[0] + ".pdf"
    return FileResponse(out, filename=out)



# 🔟 PDF ➜ POWERPOINT (PPTX)
@app.post("/pdf-to-ppt")
async def pdf_to_ppt(file: UploadFile = File(...)):
    pdf_path = save_temp(file)
    out = "output.pptx"

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pptx",
        "--outdir", ".",
        pdf_path
    ]

    subprocess.run(cmd)
    return FileResponse(out, filename=out)



# 1️⃣1️⃣ POWERPOINT ➜ PDF
@app.post("/ppt-to-pdf")
async def ppt_to_pdf(file: UploadFile = File(...)):
    ppt_path = save_temp(file)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", ".",
        ppt_path
    ]

    subprocess.run(cmd)

    out = os.path.splitext(os.path.basename(ppt_path))[0] + ".pdf"
    return FileResponse(out, filename=out)



# 1️⃣2️⃣ PDF ➜ EXCEL (XLSX)
@app.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    pdf_path = save_temp(file)
    out = "output.xlsx"

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "xlsx",
        "--outdir", ".",
        pdf_path
    ]

    subprocess.run(cmd)
    return FileResponse(out, filename=out)



# 1️⃣3️⃣ EXCEL ➜ PDF
@app.post("/excel-to-pdf")
async def excel_to_pdf(file: UploadFile = File(...)):
    excel_path = save_temp(file)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", ".",
        excel_path
    ]

    subprocess.run(cmd)

    out = os.path.splitext(os.path.basename(excel_path))[0] + ".pdf"
    return FileResponse(out, filename=out)



# 1️⃣4️⃣ PROTECT PDF (Password Lock)
@app.post("/protect")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    path = save_temp(file)

    input_pdf = Pdf.open(path)
    input_pdf.save(
        "protected.pdf",
        encryption=Pdf.Encryption(user=password, owner=password, R=4)
    )

    return FileResponse("protected.pdf", filename="protected.pdf")



# 1️⃣5️⃣ UNLOCK PDF (Remove Password)
@app.post("/unlock")
async def unlock_pdf(file: UploadFile = File(...), password: str = Form(...)):
    path = save_temp(file)

    try:
        pdf = Pdf.open(path, password=password)
        pdf.save("unlocked.pdf")
        return FileResponse("unlocked.pdf", filename="unlocked.pdf")
    except Exception:
        return {"error": "Invalid password or file cannot be unlocked."}


# 1️⃣6️⃣ ADD WATERMARK (Text Watermark)
@app.post("/watermark")
async def watermark_pdf(
    file: UploadFile = File(...),
    text: str = Form(...),
    opacity: float = Form(0.3),
    size: int = Form(40)
):
    path = save_temp(file)

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PyPDF2 import PdfReader, PdfWriter

    # Create watermark PDF
    watermark_file = "watermark_temp.pdf"
    c = canvas.Canvas(watermark_file, pagesize=letter)
    c.setFont("Helvetica", size)
    c.setFillGray(0.5, opacity)
    c.drawString(200, 500, text)
    c.save()

    # Apply watermark
    watermark = PdfReader(watermark_file).pages[0]
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)

    out = "watermarked.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)


# 1️⃣7️⃣ REMOVE WATERMARK (Reprint PDF clean)
@app.post("/remove-watermark")
async def remove_watermark(file: UploadFile = File(...)):
    path = save_temp(file)

    # Converting PDF → images → PDF clears watermark
    pages = convert_from_path(path)
    imgs = []

    for p in pages:
        img = p.convert("RGB")
        imgs.append(img)

    out = "cleaned.pdf"
    imgs[0].save(out, save_all=True, append_images=imgs[1:])

    return FileResponse(out, filename=out)


# 1️⃣8️⃣ ROTATE PDF (90/180/270 degrees)
@app.post("/rotate")
async def rotate_pdf(file: UploadFile = File(...), angle: int = Form(...)):
    path = save_temp(file)
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    out = "rotated.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)


# 1️⃣9️⃣ EXTRACT PDF PAGES (Range)
@app.post("/extract")
async def extract_pages(file: UploadFile = File(...), pages: str = Form(...)):
    path = save_temp(file)
    reader = PdfReader(path)
    writer = PdfWriter()

    def parse_range(r):
        out = []
        for part in r.split(","):
            if "-" in part:
                a, b = part.split("-")
                out.extend(range(int(a), int(b) + 1))
            else:
                out.append(int(part))
        return out

    selected = parse_range(pages)

    for p in selected:
        writer.add_page(reader.pages[p - 1])

    out = "extracted.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import tempfile, os, shutil, subprocess
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
from pikepdf import Pdf
import pytesseract

app = FastAPI()


# Helper: Save uploaded file
def save_temp(upload: UploadFile):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(upload.file.read())
    temp.close()
    return temp.name


# 1️⃣ MERGE PDF
@app.post("/merge")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    writer = PdfWriter()
    for f in files:
        path = save_temp(f)
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    out = "merged.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)



# 2️⃣ SPLIT PDF (Range: 1-3, 6, 8-10)
@app.post("/split")
async def split_pdf(file: UploadFile = File(...), pages: str = Form(...)):
    path = save_temp(file)
    reader = PdfReader(path)
    writer = PdfWriter()

    def parse_pages(p):
        result = []
        parts = p.split(",")
        for part in parts:
            if "-" in part:
                a, b = part.split("-")
                result.extend(range(int(a), int(b) + 1))
            else:
                result.append(int(part))
        return result

    page_nums = parse_pages(pages)

    for p in page_nums:
        writer.add_page(reader.pages[p - 1])

    out = "split.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)



# 3️⃣ COMPRESS PDF (Ghostscript strong compression)
@app.post("/compress-strong")
async def compress_strong(file: UploadFile = File(...)):
    path = save_temp(file)
    out = "compressed.pdf"

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/printer",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={out}",
        path
    ]
    subprocess.run(cmd)

    return FileResponse(out, filename=out)



# 4️⃣ COMPRESS PDF (Light — PikePDF)
@app.post("/compress")
async def compress_light(file: UploadFile = File(...)):
    path = save_temp(file)
    pdf = Pdf.open(path)
    pdf.save("compressed.pdf", optimize_streams=True)
    return FileResponse("compressed.pdf")



# 5️⃣ PDF ➜ IMAGES
@app.post("/pdf-to-img")
async def pdf_to_img(file: UploadFile = File(...)):
    path = save_temp(file)

    pages = convert_from_path(path)
    folder = tempfile.mkdtemp()

    for i, p in enumerate(pages):
        p.save(f"{folder}/page_{i+1}.jpg", "JPEG")

    shutil.make_archive("images", "zip", folder)

    return FileResponse("images.zip", filename="images.zip")



# 6️⃣ IMAGES ➜ PDF
@app.post("/img-to-pdf")
async def img_to_pdf(files: list[UploadFile] = File(...)):
    images = []
    for f in files:
        path = save_temp(f)
        img = Image.open(path).convert("RGB")
        images.append(img)

    out = "images_to_pdf.pdf"
    images[0].save(out, save_all=True, append_images=images[1:])
    return FileResponse(out, filename=out)



# 7️⃣ OCR PDF ➜ TEXT
@app.post("/ocr")
async def ocr_pdf(file: UploadFile = File(...)):
    path = save_temp(file)
    pages = convert_from_path(path)

    text = ""
    for p in pages:
        text += pytesseract.image_to_string(p) + "\n\n"

    open("ocr.txt", "w").write(text)
    return FileResponse("ocr.txt", filename="ocr.txt")


# 8️⃣ PDF ➜ WORD (DOCX)
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    pdf_path = save_temp(file)
    out = "output.docx"

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "docx",
        "--outdir", ".",
        pdf_path
    ]

    subprocess.run(cmd)
    return FileResponse(out, filename=out)



# 9️⃣ WORD ➜ PDF
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    doc_path = save_temp(file)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", ".",
        doc_path
    ]

    subprocess.run(cmd)

    out = os.path.splitext(os.path.basename(doc_path))[0] + ".pdf"
    return FileResponse(out, filename=out)



# 🔟 PDF ➜ POWERPOINT (PPTX)
@app.post("/pdf-to-ppt")
async def pdf_to_ppt(file: UploadFile = File(...)):
    pdf_path = save_temp(file)
    out = "output.pptx"

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pptx",
        "--outdir", ".",
        pdf_path
    ]

    subprocess.run(cmd)
    return FileResponse(out, filename=out)



# 1️⃣1️⃣ POWERPOINT ➜ PDF
@app.post("/ppt-to-pdf")
async def ppt_to_pdf(file: UploadFile = File(...)):
    ppt_path = save_temp(file)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", ".",
        ppt_path
    ]

    subprocess.run(cmd)

    out = os.path.splitext(os.path.basename(ppt_path))[0] + ".pdf"
    return FileResponse(out, filename=out)



# 1️⃣2️⃣ PDF ➜ EXCEL (XLSX)
@app.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    pdf_path = save_temp(file)
    out = "output.xlsx"

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "xlsx",
        "--outdir", ".",
        pdf_path
    ]

    subprocess.run(cmd)
    return FileResponse(out, filename=out)



# 1️⃣3️⃣ EXCEL ➜ PDF
@app.post("/excel-to-pdf")
async def excel_to_pdf(file: UploadFile = File(...)):
    excel_path = save_temp(file)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", ".",
        excel_path
    ]

    subprocess.run(cmd)

    out = os.path.splitext(os.path.basename(excel_path))[0] + ".pdf"
    return FileResponse(out, filename=out)



# 1️⃣4️⃣ PROTECT PDF (Password Lock)
@app.post("/protect")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    path = save_temp(file)

    input_pdf = Pdf.open(path)
    input_pdf.save(
        "protected.pdf",
        encryption=Pdf.Encryption(user=password, owner=password, R=4)
    )

    return FileResponse("protected.pdf", filename="protected.pdf")



# 1️⃣5️⃣ UNLOCK PDF (Remove Password)
@app.post("/unlock")
async def unlock_pdf(file: UploadFile = File(...), password: str = Form(...)):
    path = save_temp(file)

    try:
        pdf = Pdf.open(path, password=password)
        pdf.save("unlocked.pdf")
        return FileResponse("unlocked.pdf", filename="unlocked.pdf")
    except Exception:
        return {"error": "Invalid password or file cannot be unlocked."}


# 1️⃣6️⃣ ADD WATERMARK (Text Watermark)
@app.post("/watermark")
async def watermark_pdf(
    file: UploadFile = File(...),
    text: str = Form(...),
    opacity: float = Form(0.3),
    size: int = Form(40)
):
    path = save_temp(file)

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PyPDF2 import PdfReader, PdfWriter

    # Create watermark PDF
    watermark_file = "watermark_temp.pdf"
    c = canvas.Canvas(watermark_file, pagesize=letter)
    c.setFont("Helvetica", size)
    c.setFillGray(0.5, opacity)
    c.drawString(200, 500, text)
    c.save()

    # Apply watermark
    watermark = PdfReader(watermark_file).pages[0]
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)

    out = "watermarked.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)


# 1️⃣7️⃣ REMOVE WATERMARK (Reprint PDF clean)
@app.post("/remove-watermark")
async def remove_watermark(file: UploadFile = File(...)):
    path = save_temp(file)

    # Converting PDF → images → PDF clears watermark
    pages = convert_from_path(path)
    imgs = []

    for p in pages:
        img = p.convert("RGB")
        imgs.append(img)

    out = "cleaned.pdf"
    imgs[0].save(out, save_all=True, append_images=imgs[1:])

    return FileResponse(out, filename=out)


# 1️⃣8️⃣ ROTATE PDF (90/180/270 degrees)
@app.post("/rotate")
async def rotate_pdf(file: UploadFile = File(...), angle: int = Form(...)):
    path = save_temp(file)
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    out = "rotated.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)


# 1️⃣9️⃣ EXTRACT PDF PAGES (Range)
@app.post("/extract")
async def extract_pages(file: UploadFile = File(...), pages: str = Form(...)):
    path = save_temp(file)
    reader = PdfReader(path)
    writer = PdfWriter()

    def parse_range(r):
        out = []
        for part in r.split(","):
            if "-" in part:
                a, b = part.split("-")
                out.extend(range(int(a), int(b) + 1))
            else:
                out.append(int(part))
        return out

    selected = parse_range(pages)

    for p in selected:
        writer.add_page(reader.pages[p - 1])

    out = "extracted.pdf"
    with open(out, "wb") as fp:
        writer.write(fp)

    return FileResponse(out, filename=out)

