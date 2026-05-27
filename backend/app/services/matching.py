"""
VerifyHire Job Matching Engine
Formula: Final Score = (0.7 × semantic_similarity) + (0.3 × jaccard_skill_overlap)
"""

import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

_sbert_model = None


def _get_sbert_model():
    global _sbert_model
    if _sbert_model is None:
        from sentence_transformers import SentenceTransformer
        from app.core.config import settings
        logger.info(f"Loading SBERT model: {settings.SBERT_MODEL}")
        _sbert_model = SentenceTransformer(settings.SBERT_MODEL)
        logger.info("SBERT model loaded")
    return _sbert_model


def _jaccard_skill_overlap(worker_skills: list[str], job_skills: list[str]) -> float:
    if not worker_skills or not job_skills:
        return 0.0
    w_set = {s.lower().strip() for s in worker_skills}
    j_set = {s.lower().strip() for s in job_skills}
    intersection = w_set & j_set
    union = w_set | j_set
    return len(intersection) / len(union) if union else 0.0


def compute_matches(
    worker_text: str,
    worker_skills: list[str],
    jobs: list[dict[str, Any]],
    top_k: int = 20,
) -> list[dict[str, Any]]:
    if not jobs:
        return []

    try:
        model = _get_sbert_model()

        # Build job texts
        job_texts = [
            f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('required_skills', []))}"
            for job in jobs
        ]

        all_texts = [worker_text] + job_texts
        logger.info(f"Encoding {len(all_texts)} texts with SBERT...")

        # Encode all at once
        embeddings = model.encode(all_texts, convert_to_numpy=True, show_progress_bar=False)

        worker_emb = embeddings[0]
        job_embs = embeddings[1:]

        # Normalize
        def normalize(v):
            n = np.linalg.norm(v)
            return v / n if n > 0 else v

        worker_emb = normalize(worker_emb)

        results = []
        for i, job in enumerate(jobs):
            job_emb = normalize(job_embs[i])
            semantic_score = float(np.dot(worker_emb, job_emb))
            semantic_score = max(0.0, min(1.0, semantic_score))

            job_required_skills = job.get("required_skills", [])
            skill_score = _jaccard_skill_overlap(worker_skills, job_required_skills)

            final_score = (0.7 * semantic_score) + (0.3 * skill_score)

            w_set = {s.lower().strip() for s in worker_skills}
            j_set = {s.lower().strip() for s in job_required_skills}
            matched_skills = list(w_set & j_set)

            results.append({
                "job_id": str(job.get("id", "")),
                "job": job,
                "final_score": round(final_score, 4),
                "semantic_score": round(semantic_score, 4),
                "skill_score": round(skill_score, 4),
                "matched_skills": matched_skills,
                "rank": i + 1,
            })

        results.sort(key=lambda x: x["final_score"], reverse=True)
        logger.info(f"Matching complete: {len(results)} jobs ranked, top score: {results[0]['final_score'] if results else 0}")
        return results[:top_k]

    except Exception as e:
        logger.error(f"Matching engine error: {e}", exc_info=True)
        return []