"""
Related Report Detection Layer (Part 3A)

Identifies analytically related reports for a specific target report
and generates transparent evidence-backed explanations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.analytics.config import MISSING_VALUE_PLACEHOLDER
from backend.analytics.data_access import AnalyticsReportDTO


@dataclass
class RelatedReport:
    """Representation of an analytically related report with explicit evidence."""
    target_report_id: int
    related_report_id: int
    related_report_number: str
    matching_dimensions: Dict[str, str]
    evidence_explanation: str
    similarity_score: Optional[float]
    date: str
    site: str
    refinery_unit: str
    equipment_id: str
    activity: str
    description_snippet: str
    is_sif_ai: bool
    is_sif_hse: Optional[bool]


def find_related_reports(
    target_report_id: int,
    reports: List[AnalyticsReportDTO],
    max_results: int = 5,
) -> List[RelatedReport]:
    """
    Finds reports analytically related to target_report_id across the provided report list.
    Calculates exact dimension overlap and TF-IDF text similarity to produce evidence.
    """
    related_list: List[RelatedReport] = []

    report_map = {r.report_id: r for r in reports}
    target = report_map.get(target_report_id)
    if not target:
        return related_list

    candidates = [r for r in reports if r.report_id != target_report_id]
    if not candidates:
        return related_list

    # Compute text similarities if description exists
    descriptions = [target.normalized.get("description", target.description)] + [
        c.normalized.get("description", c.description) for c in candidates
    ]

    tfidf_sims: Dict[int, float] = {}
    valid_texts = [d for d in descriptions if d and d != MISSING_VALUE_PLACEHOLDER]
    if len(valid_texts) >= 2:
        try:
            vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
            matrix = vectorizer.fit_transform(descriptions)
            target_vector = matrix[0]
            candidate_vectors = matrix[1:]
            sim_scores = cosine_similarity(target_vector, candidate_vectors)[0]

            for idx, cand in enumerate(candidates):
                tfidf_sims[cand.report_id] = float(sim_scores[idx])
        except Exception:
            pass

    scored_candidates: List[Tuple[float, Dict[str, str], List[str], AnalyticsReportDTO]] = []

    target_norm = target.normalized

    for cand in candidates:
        cand_norm = cand.normalized
        matching_dims: Dict[str, str] = {}
        evidence_reasons: List[str] = []

        overlap_score = 0.0

        # Dimension checks
        for dim, weight in [
            ("equipment_id", 3.0),
            ("activity", 2.0),
            ("location", 2.0),
            ("refinery_unit", 1.5),
            ("work_type", 1.0),
            ("department", 1.0),
        ]:
            t_val = target_norm.get(dim, MISSING_VALUE_PLACEHOLDER)
            c_val = cand_norm.get(dim, MISSING_VALUE_PLACEHOLDER)
            if t_val != MISSING_VALUE_PLACEHOLDER and t_val == c_val:
                matching_dims[dim] = getattr(cand, dim, c_val)
                evidence_reasons.append(f"Matching {dim.replace('_', ' ').title()}: {matching_dims[dim]}")
                overlap_score += weight

        # Shared Hazards / Barriers
        t_hazards = set(target_norm.get("hazards", []))
        c_hazards = set(cand_norm.get("hazards", []))
        shared_hazards = t_hazards.intersection(c_hazards) - {MISSING_VALUE_PLACEHOLDER}
        if shared_hazards:
            matching_dims["shared_hazards"] = ", ".join(shared_hazards)
            evidence_reasons.append(f"Shared Hazard(s): {', '.join(shared_hazards)}")
            overlap_score += 1.5 * len(shared_hazards)

        t_barriers = set(target_norm.get("barriers", []))
        c_barriers = set(cand_norm.get("barriers", []))
        shared_barriers = t_barriers.intersection(c_barriers) - {MISSING_VALUE_PLACEHOLDER}
        if shared_barriers:
            matching_dims["shared_barriers"] = ", ".join(shared_barriers)
            evidence_reasons.append(f"Shared Barrier(s): {', '.join(shared_barriers)}")
            overlap_score += 1.5 * len(shared_barriers)

        # Text Similarity contribution
        text_sim = tfidf_sims.get(cand.report_id, 0.0)
        if text_sim > 0.3:
            overlap_score += text_sim * 4.0
            evidence_reasons.append(f"Description Text Similarity: {text_sim:.1%}")

        if overlap_score > 0.0 and evidence_reasons:
            scored_candidates.append((overlap_score, matching_dims, evidence_reasons, cand))

    # Sort candidates by combined overlap score descending
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    for score, dims, reasons, cand in scored_candidates[:max_results]:
        snippet = (cand.description[:120] + "...") if len(cand.description) > 120 else cand.description
        text_sim = tfidf_sims.get(cand.report_id, None)

        related_list.append(
            RelatedReport(
                target_report_id=target_report_id,
                related_report_id=cand.report_id,
                related_report_number=cand.report_number,
                matching_dimensions=dims,
                evidence_explanation="; ".join(reasons),
                similarity_score=round(text_sim, 4) if text_sim is not None else None,
                date=cand.date,
                site=cand.site,
                refinery_unit=cand.refinery_unit,
                equipment_id=cand.equipment_id,
                activity=cand.activity,
                description_snippet=snippet,
                is_sif_ai=cand.is_sif_ai(),
                is_sif_hse=cand.is_sif_hse(),
            )
        )

    return related_list
