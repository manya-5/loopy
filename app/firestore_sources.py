"""Firestore client and data access for news sources."""

from typing import Any, Dict, List
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-ecdb51b92176"

_db = None


def get_firestore_client() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def get_sources_for_role(role: str) -> List[Dict[str, Any]]:
    """Fetches news sources from Firestore relevant to a given role or role description.

    Args:
        role: The role name (e.g. 'Frontend', 'Backend', 'Product Designer',
              'Design Engineer', 'PM', 'FDE') or a user's description of their work.

    Returns:
        A list of dictionaries, each containing 'name', 'url', 'type', and 'roles'.
    """
    db = get_firestore_client()
    collection = db.collection("sources")

    canonical_roles = {
        "product designer": "Product Designer",
        "design engineer": "Design Engineer",
        "pm": "PM",
        "product manager": "PM",
        "frontend": "Frontend",
        "backend": "Backend",
        "fde": "FDE",
        "forward deployed engineer": "FDE",
    }

    normalized = role.strip().lower()
    matched_role = canonical_roles.get(normalized)

    # If exact canonical match, query with ArrayContains
    if matched_role:
        query = collection.where(filter=firestore.FieldFilter("roles", "array_contains", matched_role))
        return [doc.to_dict() for doc in query.stream()]

    # Otherwise (custom description or non-chip role), inspect all sources and pick closest
    all_docs = [doc.to_dict() for doc in collection.stream()]
    
    # Check for keyword matches in description
    scored_sources: List[Dict[str, Any]] = []
    has_design = any(w in normalized for w in ["design", "ui", "ux", "visual", "css"])
    has_frontend = any(w in normalized for w in ["frontend", "web", "client", "react", "html", "javascript", "typescript"])
    has_backend = any(w in normalized for w in ["backend", "api", "database", "server", "distributed", "infra", "cloud", "devops"])
    has_pm = any(w in normalized for w in ["product", "pm", "growth", "strategy", "roadmap", "market"])

    for src in all_docs:
        roles_set = set(src.get("roles", []))
        score = 0
        if has_design and ("Product Designer" in roles_set or "Design Engineer" in roles_set):
            score += 2
        if has_frontend and ("Frontend" in roles_set or "Design Engineer" in roles_set):
            score += 2
        if has_backend and ("Backend" in roles_set or "FDE" in roles_set):
            score += 2
        if has_pm and ("PM" in roles_set):
            score += 2

        if score > 0:
            scored_sources.append(src)

    if scored_sources:
        return scored_sources

    # Default fallback: return all sources so agent has broad options
    return all_docs
