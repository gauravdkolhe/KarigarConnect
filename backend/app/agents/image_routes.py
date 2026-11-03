from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image

from backend.app.database.connection import database
from backend.app.services.image_service import (
    ENHANCED_DIR,
    ORIGINALS_DIR,
    STYLE_CONFIGS,
    enhance_product_image,
)

router = APIRouter(
    prefix="/api/images",
    tags=["Image Processing"],
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


# --------------------------------------------------
# 0. List available style options
# --------------------------------------------------

@router.get("/styles")
def get_image_styles():
    """Retrieve available e-commerce enhancement style presets."""
    styles = []
    for key, cfg in STYLE_CONFIGS.items():
        styles.append({
            "key": key,
            "name": cfg["name"],
            "description": cfg["description"],
            "bg_color": cfg["bg_color"],
            "has_shadow": cfg.get("has_shadow", False),
            "warm_tint": cfg.get("warm_tint", False),
        })
    return {
        "styles": styles,
        "default": "studio_white",
    }


# --------------------------------------------------
# 1. Upload and enhance a product image
# --------------------------------------------------

@router.post("/enhance")
def upload_and_enhance_image(
    product_id: str = Form(..., min_length=1, max_length=100),
    file: UploadFile = File(...),
    style: str = Form("studio_white"),
    brightness: Optional[float] = Form(None),
    contrast: Optional[float] = Form(None),
    sharpness: Optional[float] = Form(None),
):
    # Support either product_catalogs or product_workflows
    product = database["product_catalogs"].find_one({"product_id": product_id}, {"_id": 1})
    if product is None:
        wf = database["product_workflows"].find_one({"product_id": product_id}, {"_id": 1})
        if wf is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found. Generate its catalog or draft first.",
            )

    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    ENHANCED_DIR.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Only JPG, PNG, and WEBP images are supported.",
        )

    original_name = f"{uuid4().hex}{extension}"
    original_path = ORIGINALS_DIR / original_name
    enhanced_path = None

    try:
        # Save the uploaded file with a unique name.
        total_bytes = 0

        with original_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Image must be 10 MB or smaller.",
                    )

                destination.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # Validate the actual image format.
        try:
            with Image.open(original_path) as image:
                if image.format not in ALLOWED_FORMATS:
                    raise HTTPException(
                        status_code=415,
                        detail="Unsupported image format.",
                    )
                image.verify()

        except HTTPException:
            raise
        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid image.",
            ) from error

        # Enhance image with white background, auto-alignment, and chosen style
        result = enhance_product_image(
            original_path,
            style=style,
            custom_brightness=brightness,
            custom_contrast=contrast,
            custom_sharpness=sharpness,
        )
        enhanced_path = Path(result["enhanced_path"])

        created_at = datetime.now(timezone.utc)

        # Store metadata in MongoDB.
        document = {
            "product_id": product_id,
            "original_filename": original_name,
            "enhanced_filename": result["enhanced_filename"],
            "original_path": f"storage/originals/{original_name}",
            "enhanced_path": f"storage/enhanced/{result['enhanced_filename']}",
            "original_dimensions": result["original_dimensions"],
            "enhanced_dimensions": result["enhanced_dimensions"],
            "style_applied": result["style_applied"],
            "settings": result["settings"],
            "created_at": created_at,
        }

        saved = database["product_images"].insert_one(document)

        # Also update workflow steps if workflow exists
        database["product_workflows"].update_one(
            {"product_id": product_id},
            {
                "$addToSet": {"steps_completed": "images_uploaded"},
                "$set": {"updated_at": created_at},
            },
        )

        return {
            "status": "success",
            "message": f"Image enhanced with {result['style_applied']['name']} style and saved.",
            "image_id": str(saved.inserted_id),
            "product_id": product_id,
            "original_filename": document["original_filename"],
            "enhanced_filename": document["enhanced_filename"],
            "original_path": document["original_path"],
            "enhanced_path": document["enhanced_path"],
            "original_dimensions": document["original_dimensions"],
            "enhanced_dimensions": document["enhanced_dimensions"],
            "style_applied": document["style_applied"],
            "settings": document["settings"],
            "created_at": created_at.isoformat(),
        }

    except HTTPException:
        original_path.unlink(missing_ok=True)
        if enhanced_path is not None:
            enhanced_path.unlink(missing_ok=True)
        raise

    except Exception as error:
        original_path.unlink(missing_ok=True)
        if enhanced_path is not None:
            enhanced_path.unlink(missing_ok=True)

        print(f"Image processing failed: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Image processing failed: {str(error)}",
        ) from error

    finally:
        file.file.close()


# --------------------------------------------------
# 2. Re-style an existing image
# --------------------------------------------------

@router.post("/{image_id}/restyle")
def restyle_image(
    image_id: str,
    style: str = Form(..., description="Style name: studio_white, warm_heritage, or modern_minimalist"),
    brightness: Optional[float] = Form(None),
    contrast: Optional[float] = Form(None),
    sharpness: Optional[float] = Form(None),
):
    """Re-render an existing product image with an alternative style preset."""
    if not ObjectId.is_valid(image_id):
        raise HTTPException(status_code=400, detail="Invalid image ID.")

    doc = database["product_images"].find_one({"_id": ObjectId(image_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Image record not found.")

    orig_filename = doc.get("original_filename")
    orig_path = (ORIGINALS_DIR / orig_filename).resolve()

    if not orig_path.is_file():
        raise HTTPException(status_code=404, detail="Original raw image file is missing on server.")

    result = enhance_product_image(
        orig_path,
        style=style,
        custom_brightness=brightness,
        custom_contrast=contrast,
        custom_sharpness=sharpness,
    )

    created_at = datetime.now(timezone.utc)
    new_doc = {
        "product_id": doc["product_id"],
        "original_filename": orig_filename,
        "enhanced_filename": result["enhanced_filename"],
        "original_path": doc["original_path"],
        "enhanced_path": f"storage/enhanced/{result['enhanced_filename']}",
        "original_dimensions": result["original_dimensions"],
        "enhanced_dimensions": result["enhanced_dimensions"],
        "style_applied": result["style_applied"],
        "settings": result["settings"],
        "created_at": created_at,
    }

    saved = database["product_images"].insert_one(new_doc)

    return {
        "status": "success",
        "message": f"Image re-rendered with {result['style_applied']['name']} style.",
        "image_id": str(saved.inserted_id),
        "product_id": doc["product_id"],
        "enhanced_filename": result["enhanced_filename"],
        "style_applied": result["style_applied"],
        "file_url": f"/api/images/{saved.inserted_id}/file",
    }


# --------------------------------------------------
# 3. Retrieve all images associated with a product
# --------------------------------------------------

@router.get("/product/{product_id}")
def get_product_images(product_id: str):
    documents = database["product_images"].find({"product_id": product_id}).sort("created_at", -1)

    images = []
    for document in documents:
        images.append({
            "image_id": str(document["_id"]),
            "product_id": document["product_id"],
            "original_filename": document["original_filename"],
            "enhanced_filename": document["enhanced_filename"],
            "original_dimensions": document["original_dimensions"],
            "enhanced_dimensions": document["enhanced_dimensions"],
            "style_applied": document.get("style_applied"),
            "settings": document["settings"],
            "created_at": document["created_at"].isoformat() if isinstance(document["created_at"], datetime) else str(document["created_at"]),
            "image_url": f"/api/images/{document['_id']}/file",
        })

    return {
        "product_id": product_id,
        "total_images": len(images),
        "images": images,
    }


# --------------------------------------------------
# 4. Display an enhanced image in a browser
# --------------------------------------------------

@router.get("/{image_id}/file")
def get_enhanced_image(image_id: str):
    if not ObjectId.is_valid(image_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid image ID.",
        )

    document = database["product_images"].find_one({"_id": ObjectId(image_id)})

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Image record not found.",
        )

    filename = document.get("enhanced_filename", "")

    # Prevent directory traversal through stored filenames.
    if not filename or Path(filename).name != filename:
        raise HTTPException(
            status_code=500,
            detail="Invalid stored image filename.",
        )

    image_path = (ENHANCED_DIR / filename).resolve()

    if image_path.parent != ENHANCED_DIR.resolve():
        raise HTTPException(
            status_code=400,
            detail="Invalid image path.",
        )

    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Enhanced image file not found on disk.",
        )

    return FileResponse(
        path=image_path,
        media_type="image/jpeg",
        filename=filename,
    )
