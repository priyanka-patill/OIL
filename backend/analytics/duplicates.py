"""
Duplicate Detection Layer (Part 3A)

Identifies exact, near-duplicate, and potentially similar report groups
without modifying or deleting any source database records.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.analytics.config import SIMILARITY_THRESHOLD, MISSING_VALUE_PLACEHOLDER
from backend.analytics.data_access import AnalyticsReportDTO


@dataclass
class DuplicateGroup:
    """Representation of a group of duplicate or near-duplicate reports."""
    group_id: str
    duplicate_level: str  # LEVEL_1_EXACT, LEVEL_2_NEAR_DUPLICATE, LEVEL_3_POTENTIALLY_SIMILAR
    member_report_ids: List[int]
    member_report_numbers: List[str]
    reason: str
    similarity_score: Optional[float] = None
    detection_method: str = "normalized_fingerprint"


def compute_fingerprint(dto: AnalyticsReportDTO) -> str:
    """
    Computes a stable fingerprint string from normalized report content.
    Excludes source_sheet and internal IDs.
    """
    norm = dto.normalized
    components = [
        norm.get("date", ""),
        norm.get("site", ""),
        norm.get("location", ""),
        norm.get("equipment_id", ""),
        norm.get("activity", ""),
        norm.get("description", ""),
    ]
    raw = "||".join(components)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def detect_duplicates(
    reports: List[AnalyticsReportDTO],
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> List[DuplicateGroup]:
    """
    Scans a list of normalized AnalyticsReportDTO objects and returns detected duplicate groups.
    Does NOT modify source reports.
    """
    duplicate_groups: List[DuplicateGroup] = []
    group_counter = 1

    if not reports:
        return duplicate_groups

    # Track reports already assigned to an exact/near duplicate group
    processed_report_ids: Set[int] = set()

    # -------------------------------------------------------------
    # LEVEL 1 — Exact Fingerprint Duplicates
    # -------------------------------------------------------------
    fingerprint_map: Dict[str, List[AnalyticsReportDTO]] = {}
    for r in reports:
        fp = compute_fingerprint(r)
        fingerprint_map.setdefault(fp, []).append(r)

    for fp, group in fingerprint_map.items():
        if len(group) > 1:
            member_ids = [r.report_id for r in group]
            member_nums = [r.report_number for r in group]
            processed_report_ids.update(member_ids)
            duplicate_groups.append(
                DuplicateGroup(
                    group_id=f"DUP-L1-{group_counter:03d}",
                    duplicate_level="LEVEL_1_EXACT",
                    member_report_ids=member_ids,
                    member_report_numbers=member_nums,
                    reason="Exact match on normalized content fingerprint (date, site, location, equipment, activity, description).",
                    similarity_score=1.0,
                    detection_method="sha256_fingerprint",
                )
            )
            group_counter += 1

    # -------------------------------------------------------------
    # LEVEL 2 — Near-Duplicates via TF-IDF Text Similarity
    # -------------------------------------------------------------
    remaining_reports = [r for r in reports if r.report_id not in processed_report_ids]
    if len(remaining_reports) >= 2:
        descriptions = [r.normalized.get("description", r.description) for r in remaining_reports]
        # Skip if all descriptions are empty/placeholder
        non_empty = [d for d in descriptions if d and d != MISSING_VALUE_PLACEHOLDER]
        if len(non_empty) >= 2:
            try:
                vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
                tfidf_matrix = vectorizer.fit_transform(descriptions)
                similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

                visited_indices: Set[int] = set()

                for i in range(len(remaining_reports)):
                    if i in visited_indices:
                        continue
                    cluster: List[int] = [i]
                    max_sim = 0.0

                    for j in range(i + 1, len(remaining_reports)):
                        if j in visited_indices:
                            continue
                        sim = float(similarity_matrix[i, j])
                        if sim >= similarity_threshold:
                            cluster.append(j)
                            visited_indices.add(j)
                            if sim > max_sim:
                                max_sim = sim

                    if len(cluster) > 1:
                        visited_indices.add(i)
                        cluster_reports = [remaining_reports[idx] for idx in cluster]
                        member_ids = [r.report_id for r in cluster_reports]
                        member_nums = [r.report_number for r in cluster_reports]

                        duplicate_groups.append(
                            DuplicateGroup(
                                group_id=f"DUP-L2-{group_counter:03d}",
                                duplicate_level="LEVEL_2_NEAR_DUPLICATE",
                                member_report_ids=member_ids,
                                member_report_numbers=member_nums,
                                reason=f"High TF-IDF description text similarity ({max_sim:.1%}) above threshold ({similarity_threshold:.1%}).",
                                similarity_score=round(max_sim, 4),
                                detection_method="tfidf_cosine_similarity",
                            )
                        )
                        group_counter += 1
            except Exception:
                # Fallback gracefully if TF-IDF fails (e.g., empty vocabulary)
                pass

    return duplicate_groups
