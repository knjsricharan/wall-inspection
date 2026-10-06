import os
import time
import cv2
import numpy as np
import logging

from backend.core.config import get_settings
from backend.services.quality_service import run_quality_check
from backend.schemas.process import ProcessResponse, ProcessMetadata
from backend.schemas.quality import QualityStatus

logger = logging.getLogger(__name__)

def preprocess_image(file_bytes: bytes, filename: str) -> ProcessResponse:
    settings = get_settings()
    
    quality_result = run_quality_check(file_bytes, filename)
    
    # Save original image
    timestamp = int(time.time())
    safe_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_')]).rstrip()
    if not safe_filename: 
        safe_filename = "upload.jpg"
    
    orig_filename = f"{timestamp}_orig_{safe_filename}"
    orig_path = os.path.join(settings.upload_dir, orig_filename)
    with open(orig_path, "wb") as f:
        f.write(file_bytes)
        
    orig_url = f"/uploads/{orig_filename}"
    
    if quality_result.status == QualityStatus.FAIL:
        logger.info("Image failed quality check, skipping preprocessing.")
        return ProcessResponse(
            quality_result=quality_result,
            original_image_url=orig_url,
            processed_image_url=None,
            metadata=None
        )
        
    np_img = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    
    original_h, original_w = img.shape[:2]
    operations_applied = []
    
    # 1. Aspect-ratio-preserving resize if too large
    max_dim = 1024
    if max(original_w, original_h) > max_dim:
        scale = max_dim / max(original_w, original_h)
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        operations_applied.append(f"resize_max_{max_dim}")
        
    # 2. Mild denoising
    img = cv2.GaussianBlur(img, (3, 3), 0)
    operations_applied.append("mild_denoise")
    
    # 3. Brightness correction and CLAHE contrast enhancement
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    
    mean_l = np.mean(l_channel)
    if mean_l < 70:
        l_channel = cv2.add(l_channel, 30)
        operations_applied.append("brightness_correction_up")
    elif mean_l > 200:
        l_channel = cv2.subtract(l_channel, 30)
        operations_applied.append("brightness_correction_down")
        
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    operations_applied.append("clahe_contrast_enhancement")
    
    lab = cv2.merge((l_channel, a_channel, b_channel))
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 4. Mild sharpening (Unsharp Masking)
    gaussian = cv2.GaussianBlur(img, (0, 0), 2.0)
    img = cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)
    operations_applied.append("mild_sharpen")
    
    processed_h, processed_w = img.shape[:2]
    
    proc_filename = f"{timestamp}_proc_{safe_filename}"
    proc_path = os.path.join(settings.upload_dir, proc_filename)
    cv2.imwrite(proc_path, img)
    
    proc_url = f"/uploads/{proc_filename}"
    
    return ProcessResponse(
        quality_result=quality_result,
        original_image_url=orig_url,
        processed_image_url=proc_url,
        metadata=ProcessMetadata(
            operations_applied=operations_applied,
            original_size=[original_w, original_h],
            processed_size=[processed_w, processed_h]
        )
    )
