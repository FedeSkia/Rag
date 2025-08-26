from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Optional
from langchain.schema import Document

# ---- Config ----
@dataclass(frozen=True)
class CoalesceConfig:
    min_len: int = 50
    keep_headings_separate: bool = True
    avoid_cross_page_merge: bool = True
    hard_types: tuple[str, ...] = ("Table", "Code", "Figure", "Caption")

# ---- Helpers ----
def category(doc: Document) -> Optional[str]:
    return doc.metadata.get("category") or doc.metadata.get("type")

def page(doc: Document) -> Optional[int]:
    return doc.metadata.get("page_number") or doc.metadata.get("page")

def _flush_buffer(buf: List[Document], out: List[Document]) -> None:
    if not buf:
        return
    base = buf[0]
    base.page_content = "\n".join(x.page_content for x in buf if x.page_content)
    cats = list({category(x) for x in buf if category(x)})
    if cats:
        base.metadata["layout_categories"] = cats
    out.append(base)

# ---- Pass 1: merge adjacent elements of same category (optionally same page) ----
def merge_adjacent_by_category(elements: Iterable[Document], *, cfg: CoalesceConfig) -> List[Document]:
    merged: List[Document] = []
    buf: List[Document] = []
    last_cat: Optional[str] = None
    last_page: Optional[int] = None

    for el in elements:
        cat = category(el)
        pg = page(el)
        same_cat = (cat == last_cat)
        same_page = (pg == last_page) or (last_page is None)

        if same_cat and (not cfg.avoid_cross_page_merge or same_page):
            buf.append(el)
        else:
            _flush_buffer(buf, merged)
            buf = [el]
            last_cat, last_page = cat, pg

    _flush_buffer(buf, merged)
    return merged

# ---- Pass 2: ensure minimum length without mixing hard types or headings ----
def ensure_min_length(docs: List[Document], *, cfg: CoalesceConfig) -> List[Document]:
    out: List[Document] = []
    acc: Optional[Document] = None

    def is_hard(d: Document) -> bool:
        return (category(d) or "") in cfg.hard_types

    def is_heading(d: Document) -> bool:
        return (category(d) or "").lower() in {"title", "heading", "header"}

    for d in docs:
        if acc is None:
            acc = d
            continue

        barrier = is_hard(acc) or is_hard(d) or (cfg.keep_headings_separate and (is_heading(acc) or is_heading(d)))

        if len(acc.page_content) < cfg.min_len and not barrier:
            acc.page_content += "\n" + d.page_content
        else:
            out.append(acc)
            acc = d

    if acc:
        out.append(acc)
    return out

# ---- Public API ----
def coalesce_elements(elements: Iterable[Document], *, cfg: CoalesceConfig = CoalesceConfig()) -> List[Document]:
    """
    Coalesce Unstructured elements:
    1) merge adjacent same-category (optionally same-page),
    2) glue short fragments up to min_len with simple guards.
    """
    step1 = merge_adjacent_by_category(elements, cfg=cfg)
    step2 = ensure_min_length(step1, cfg=cfg)
    return step2
