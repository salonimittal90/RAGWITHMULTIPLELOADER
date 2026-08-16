from fastapi import APIRouter, HTTPException
#from repos.loader import load_document_route
from repos.loader import load_and_index_documents
from fastapi import APIRouter, HTTPException, UploadFile, File
from repos.loader import load_and_index_documents
import os
import tempfile


router = APIRouter()

#load from url
@router.post("/load_url")
async def load_url(source: str, source_type: str = "web"):
    try:
        count = load_and_index_documents(source, source_type)
        return {"message": f"Successfully loaded {count} chunks", "source": source, "type": source_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#load from file (pdf, docx, csv)
@router.post("/load_file")
async def load_file(file: UploadFile = File(...)):
    try:
        # File extension se type detect karo
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in ['pdf', 'docx', 'csv', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'bmp']:
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, DOCX, CSV, PPTX, Images allowed.")

        
        # Temporary file create karo
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Document load karo
        count = load_and_index_documents(temp_file_path, file_extension)
        
        # Temporary file delete karo
        os.unlink(temp_file_path)
        
        return {"message": f"Successfully loaded {count} chunks", "filename": file.filename, "type": file_extension}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))