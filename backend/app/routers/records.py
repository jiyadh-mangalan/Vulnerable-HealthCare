import os
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from lxml import etree
import yaml

from .. import models
from ..database import get_db
from ..security import get_current_user_from_token

router = APIRouter(tags=["records"])
templates = Jinja2Templates(directory="backend/app/templates")

REPORTS_DIR = "backend/app/static/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Create a dummy report
with open(os.path.join(REPORTS_DIR, "sample_report.txt"), "w") as f:
    f.write("Patient: John Doe\nDiagnosis: Healthy\nDate: 2023-10-01")

@router.get("/reports", response_class=HTMLResponse)
async def list_reports(
    request: Request,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # Determine which report to show
    # Real app would query DB, here we list literal files for LFI demo
    # But usually LFI is via a parameter like ?file=...
    
    return templates.TemplateResponse("records.html", {
        "request": request,
        "user": current_user
    })

@router.get("/reports/download")
async def download_report(
    file: str, 
    current_user: models.User = Depends(get_current_user_from_token)
):
    # VULNERABILITY: Path Traversal / LFI
    # Intentionally joining path without validation
    # Attack: /reports/download?file=../../../../etc/passwd
    
    file_path = os.path.join(REPORTS_DIR, file)
    
    if not os.path.exists(file_path):
         raise HTTPException(status_code=404, detail="File not found")
         
    return FileResponse(file_path)

@router.post("/reports/import_xml")
async def import_xml(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user_from_token)
):
    # VULNERABILITY: XXE (XML External Entity)
    # Parsing XML with resolve_entities=True (or default that allows it depending on lib version, 
    # but strictly lxml needs manual config to be vulnerable usually, or just 'no_network=False')
    
    try:
        content = await file.read()
        
        # Explicitly enabling external entities for vulnerability
        parser = etree.XMLParser(resolve_entities=True, no_network=False)
        tree = etree.fromstring(content, parser=parser)
        
        # Extract data to show user (reflection)
        # Assuming simple structure <record><diagnosis>...</diagnosis></record>
        diagnosis = tree.find("diagnosis")
        result_text = diagnosis.text if diagnosis is not None else "No diagnosis found"
        
        return templates.TemplateResponse("records.html", {
            "request": request, 
            "user": current_user, 
            "xml_result": f"Imported: {result_text}"
        })
        
    except Exception as e:
         return templates.TemplateResponse("records.html", {
            "request": request, 
            "user": current_user, 
            "error": f"XML Parse Error: {str(e)}"
        })

@router.post("/reports/import_yaml")
async def import_yaml(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user_from_token)
):
    # VULNERABILITY: Insecure Deserialization (YAML)
    try:
        content = await file.read()
        # yaml.load is unsafe by default in older versions, but current PyYAML requires Loader
        # We explicitly use UnsafeLoader to be vulnerable
        data = yaml.load(content, Loader=yaml.UnsafeLoader)
        
        return templates.TemplateResponse("records.html", {
            "request": request, 
            "user": current_user, 
            "yaml_result": f"Processed YAML: {str(data)}"
        })
    except Exception as e:
         return templates.TemplateResponse("records.html", {
            "request": request, 
            "user": current_user, 
            "error": f"YAML Error: {str(e)}"
        })
