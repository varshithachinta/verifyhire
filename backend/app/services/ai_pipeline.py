"""
VerifyHire AI Processing Pipeline
Implements the full contract from Video Data Extraction Contract.

Pipeline steps:
  1. extract_audio()    — ffmpeg: video → 16kHz WAV
  2. detect_face()      — YOLOv8n-face: middle frame → crop
  3. verify_face()      — DeepFace/ArcFace: identity check
  4. transcribe_audio() — Whisper: WAV → text + timestamps
  5. extract_skills()   — spaCy: transcript → skills
  6. extract_worker_info() — regex: name, experience, location
  7. process_video_pipeline() — orchestrator

All outputs follow the strict JSON contract schema.
"""

import re
import subprocess
import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SKILL VOCABULARY  (50+ blue-collar skills)
# ─────────────────────────────────────────────────────────────────────────────

SKILL_VOCABULARY = {
    # Trades
    "electrician", "electrical", "wiring", "circuitry",
    "plumbing", "plumber", "pipefitting", "pipe",
    "welding", "welder", "soldering",
    "carpentry", "carpenter", "woodwork", "joinery",
    "masonry", "mason", "bricklaying",
    "painting", "painter",
    "tiling", "tile",
    "roofing", "roofer",
    "hvac", "air conditioning", "refrigeration",
    # Mechanical
    "mechanic", "automotive", "engine", "vehicle", "automobile",
    "two-wheeler", "bike repair", "diesel", "hydraulics",
    # Construction
    "construction", "civil", "concrete", "scaffolding",
    "steel", "fabrication", "structural",
    # Domestic
    "cooking", "chef", "cleaning", "housekeeping", "caretaking",
    "childcare", "eldercare", "driving", "driver",
    # Industrial
    "forklift", "crane", "heavy equipment", "machine operator",
    "lathe", "cnc", "grinding", "drilling",
    # Security
    "security guard", "security", "surveillance",
    # Agriculture
    "farming", "agriculture", "irrigation", "harvesting",
    # Logistics
    "delivery", "logistics", "warehouse", "loading", "unloading",
    "packing", "stacking",
    # IT support / basic
    "computer", "data entry", "typing",
}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5.1 — Audio Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_audio(video_path: str, output_audio_path: str) -> dict[str, Any]:
    """
    Extract 16kHz mono WAV from video using ffmpeg.
    Returns: {audio_path, duration_seconds, success}
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",                  # no video
            "-acodec", "pcm_s16le", # PCM 16-bit little-endian
            "-ar", "16000",         # 16kHz sample rate
            "-ac", "1",             # mono
            output_audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.error(f"ffmpeg failed: {result.stderr}")
            return {"success": False, "error": result.stderr, "audio_path": None, "duration_seconds": 0.0}

        # Get duration
        duration = _get_audio_duration(output_audio_path)
        logger.info(f"Audio extracted: {output_audio_path} | Duration: {duration:.2f}s")
        return {"success": True, "audio_path": output_audio_path, "duration_seconds": duration}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffmpeg timed out", "audio_path": None, "duration_seconds": 0.0}
    except FileNotFoundError:
        return {"success": False, "error": "ffmpeg not found — install ffmpeg and add to PATH", "audio_path": None, "duration_seconds": 0.0}


def _get_audio_duration(audio_path: str) -> float:
    """Use ffprobe to get audio duration in seconds."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip()) if result.returncode == 0 else 0.0
    except Exception:
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5.2 — Face Detection (YOLOv8)
# ─────────────────────────────────────────────────────────────────────────────

def detect_face(video_path: str, face_output_path: str) -> dict[str, Any]:
    """
    Detect face from middle frame of video using YOLOv8n-face.
    Returns: {face_detected, confidence, bounding_box, face_image_path}
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        return {"face_detected": False, "confidence": 0.0, "error": "ultralytics not installed"}

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"face_detected": False, "confidence": 0.0, "error": "Cannot open video"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        mid_frame = max(0, total_frames // 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"face_detected": False, "confidence": 0.0, "error": "Cannot read frame"}

        # Load YOLOv8 face model (auto-downloads ~6MB on first use)
        model = YOLO(settings.YOLO_MODEL)
        results = model(frame, verbose=False)

        best_box = None
        best_conf = 0.0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    best_box = box.xyxy[0].cpu().numpy().astype(int)

        if best_box is None or best_conf < 0.3:
            logger.warning("No face detected in video")
            return {
                "face_detected": False,
                "confidence": best_conf,
                "bounding_box": None,
                "face_image_path": None,
            }

        # Crop and save face
        x1, y1, x2, y2 = best_box
        x1, y1 = max(0, x1), max(0, y1)
        face_crop = frame[y1:y2, x1:x2]
        cv2.imwrite(face_output_path, face_crop)

        logger.info(f"Face detected: conf={best_conf:.3f}, saved to {face_output_path}")
        return {
            "face_detected": True,
            "confidence": round(best_conf, 4),
            "bounding_box": [int(x1), int(y1), int(x2), int(y2)],
            "face_image_path": face_output_path,
        }

    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return {"face_detected": False, "confidence": 0.0, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5.3 — Face Verification (DeepFace / ArcFace)
# ─────────────────────────────────────────────────────────────────────────────

def verify_face(
    new_face_path: str,
    reference_face_path: str | None,
) -> dict[str, Any]:
    """
    Compare new face against stored reference using ArcFace.
    First upload: save reference → returns is_verified=True, similarity_score=1.0
    Subsequent uploads: compare and return result.
    """
    if not reference_face_path or not Path(reference_face_path).exists():
        # First upload — this IS the reference
        logger.info("No reference face found — setting current as reference")
        return {
            "is_verified": True,
            "similarity_score": 1.0,
            "is_first_upload": True,
        }

    try:
        from deepface import DeepFace

        result = DeepFace.verify(
            img1_path=new_face_path,
            img2_path=reference_face_path,
            model_name="ArcFace",
            detector_backend="opencv",
            enforce_detection=False,
        )
        similarity = 1.0 - result.get("distance", 1.0)
        is_verified = result.get("verified", False)
        logger.info(f"Face verification: verified={is_verified}, similarity={similarity:.4f}")
        return {
            "is_verified": is_verified,
            "similarity_score": round(max(0.0, similarity), 4),
            "is_first_upload": False,
        }

    except Exception as e:
        logger.error(f"Face verification error: {e}")
        return {"is_verified": False, "similarity_score": 0.0, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5.4 — Speech Transcription (Whisper)
# ─────────────────────────────────────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> dict[str, Any]:
    """
    Transcribe audio using faster-whisper (drop-in replacement for openai-whisper).
    Returns: {full_text, language, segments}
    """
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
        segments_gen, info = model.transcribe(audio_path, beam_size=5)

        segments = []
        full_text_parts = []
        for seg in segments_gen:
            text = seg.text.strip()
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": text,
            })
            full_text_parts.append(text)

        full_text = " ".join(full_text_parts).strip()
        language = info.language

        logger.info(f"Transcription complete: {len(full_text)} chars, lang={language}")
        return {
            "full_text": full_text,
            "language": language,
            "segments": segments,
        }

    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return {"full_text": "", "language": "unknown", "segments": [], "error": str(e)}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5.5 — Skill Extraction (spaCy)
# ─────────────────────────────────────────────────────────────────────────────

def extract_skills(transcript: str) -> dict[str, Any]:
    """
    Extract skills from transcript using:
      A. Keyword matching against predefined vocabulary
      B. Noun phrase extraction via spaCy
    Returns: {detected_skills, confidence_scores, noun_phrases}
    """
    if not transcript:
        return {"detected_skills": [], "confidence_scores": [], "noun_phrases": []}

    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Auto-download model if missing
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            nlp = spacy.load("en_core_web_sm")

        doc = nlp(transcript.lower())

        # A. Keyword matching (lemmatized, case-insensitive)
        detected_skills = []
        confidence_scores = []

        for skill in SKILL_VOCABULARY:
            skill_words = skill.lower().split()
            # Check multi-word skills
            if skill.lower() in transcript.lower():
                detected_skills.append(skill)
                confidence_scores.append(0.9)
            # Check individual token lemmas
            elif len(skill_words) == 1:
                for token in doc:
                    if token.lemma_ == skill or token.text == skill:
                        detected_skills.append(skill)
                        confidence_scores.append(0.85)
                        break

        # Deduplicate
        seen = set()
        unique_skills, unique_scores = [], []
        for s, c in zip(detected_skills, confidence_scores):
            if s not in seen:
                seen.add(s)
                unique_skills.append(s)
                unique_scores.append(c)

        # B. Noun phrase extraction
        noun_phrases = [
            chunk.text.lower()
            for chunk in doc.noun_chunks
            if 2 <= len(chunk.text) <= 50 and not chunk.text.isdigit()
        ]
        # Remove duplicates
        noun_phrases = list(dict.fromkeys(noun_phrases))[:20]

        logger.info(f"Skills extracted: {unique_skills}")
        return {
            "detected_skills": unique_skills,
            "confidence_scores": unique_scores,
            "noun_phrases": noun_phrases,
        }

    except Exception as e:
        logger.error(f"Skill extraction error: {e}")
        return {"detected_skills": [], "confidence_scores": [], "noun_phrases": [], "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5.6 — Worker Metadata Extraction (Regex NLP)
# ─────────────────────────────────────────────────────────────────────────────

def extract_worker_info(transcript: str) -> dict[str, Any]:
    """
    Extract basic worker info from transcript using regex patterns.
    Patterns:
      name: "my name is X" / "I am X" / "I'm X"
      experience: "X years experience / X years of experience"
      location: "I am from X" / "I'm from X" / "based in X"
    """
    if not transcript:
        return {"name_detected": None, "experience_years": None, "location_detected": None}

    text = transcript.strip()

    # Name patterns
    name = None
    name_patterns = [
        r"my name is ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)",
        r"i am ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)",
        r"i'm ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)",
        r"myself ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Filter out common non-name words
            if candidate.lower() not in {"a", "an", "the", "working", "looking", "here"}:
                name = candidate
                break

    # Experience patterns
    experience_years = None
    exp_patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
        r"experience\s+of\s+(\d+)\+?\s*years?",
        r"(\d+)\+?\s*years?\s+(?:in|as|of)",
    ]
    for pattern in exp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                experience_years = int(match.group(1))
                break
            except ValueError:
                pass

    # Location patterns
    location = None
    loc_patterns = [
        r"i am from ([A-Z][a-zA-Z\s,]+?)(?:\.|,|and|where|\n|$)",
        r"i'm from ([A-Z][a-zA-Z\s,]+?)(?:\.|,|and|where|\n|$)",
        r"based in ([A-Z][a-zA-Z\s,]+?)(?:\.|,|and|where|\n|$)",
        r"located in ([A-Z][a-zA-Z\s,]+?)(?:\.|,|and|where|\n|$)",
    ]
    for pattern in loc_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip().title()
            if len(location) < 50:  # Sanity check
                break
            location = None

    return {
        "name_detected": name,
        "experience_years": experience_years,
        "location_detected": location,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MASTER PIPELINE — Combines all steps
# ─────────────────────────────────────────────────────────────────────────────

def process_video_pipeline(
    video_id: str,
    worker_id: str,
    video_path: str,
    audio_output_path: str,
    face_output_path: str,
    reference_face_path: str | None = None,
) -> dict[str, Any]:
    """
    Full AI processing pipeline. Executes all 6 extraction steps.
    Returns the complete structured output matching the contract schema.
    """
    logger.info(f"=== Starting pipeline for video_id={video_id} ===")

    result: dict[str, Any] = {
        "video_id": video_id,
        "worker_id": worker_id,
        "face_detection": {},
        "face_verification": {},
        "audio_processing": {},
        "transcription": {},
        "skill_extraction": {},
        "worker_metadata": {},
        "processing_status": "pending",
    }

    # ── Step 1: Audio Extraction ──────────────────────────────────────────────
    logger.info("Step 1: Extracting audio...")
    audio_result = extract_audio(video_path, audio_output_path)
    result["audio_processing"] = {
        "audio_path": audio_result.get("audio_path"),
        "duration_seconds": audio_result.get("duration_seconds", 0.0),
    }
    if not audio_result.get("success"):
        result["processing_status"] = "failed"
        result["error"] = f"Audio extraction failed: {audio_result.get('error')}"
        logger.error(f"Pipeline failed at audio extraction: {audio_result.get('error')}")
        return result

    # ── Step 2: Face Detection ────────────────────────────────────────────────
    logger.info("Step 2: Detecting face...")
    face_result = detect_face(video_path, face_output_path)
    result["face_detection"] = {
        "face_detected": face_result.get("face_detected", False),
        "confidence": face_result.get("confidence", 0.0),
        "face_image_path": face_result.get("face_image_path"),
    }
    if not face_result.get("face_detected"):
        result["processing_status"] = "failed"
        result["error"] = "No face detected in video"
        logger.warning("Pipeline failed: no face detected")
        return result

    # ── Step 3: Face Verification ─────────────────────────────────────────────
    logger.info("Step 3: Verifying face...")
    verify_result = verify_face(face_output_path, reference_face_path)
    result["face_verification"] = {
        "is_verified": verify_result.get("is_verified", False),
        "similarity_score": verify_result.get("similarity_score", 0.0),
    }

    # ── Step 4: Transcription ─────────────────────────────────────────────────
    logger.info("Step 4: Transcribing audio...")
    transcription = transcribe_audio(audio_output_path)
    result["transcription"] = transcription
    if not transcription.get("full_text"):
        result["processing_status"] = "failed"
        result["error"] = "Transcription produced empty text"
        logger.warning("Pipeline failed: empty transcript")
        return result

    # ── Step 5: Skill Extraction ──────────────────────────────────────────────
    logger.info("Step 5: Extracting skills...")
    skills = extract_skills(transcription["full_text"])
    result["skill_extraction"] = skills

    # ── Step 6: Worker Info Extraction ────────────────────────────────────────
    logger.info("Step 6: Extracting worker metadata...")
    worker_info = extract_worker_info(transcription["full_text"])
    result["worker_metadata"] = worker_info

    result["processing_status"] = "completed"

    # ── Validation Summary ────────────────────────────────────────────────────
    logger.info("=== Pipeline Validation ===")
    logger.info(f"Face detected: {'YES' if result['face_detection']['face_detected'] else 'NO'}")
    logger.info(f"Transcript length: {len(result['transcription'].get('full_text', ''))} chars")
    logger.info(f"Skills extracted: {len(result['skill_extraction'].get('detected_skills', []))}")
    matching_ready = (
        result["face_detection"]["face_detected"]
        and len(result["transcription"].get("full_text", "")) > 0
    )
    logger.info(f"Matching readiness: {'YES' if matching_ready else 'NO'}")

    return result
