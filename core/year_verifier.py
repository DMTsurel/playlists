"""Cross-source year verification, separation (`song_year` + `recording_year`), and auto-discovery."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import datetime
import json
from pathlib import Path
import re
import time
from typing import Any
import urllib.parse
import urllib.request

from core.artists import ARTIST_ALIASES, ENGLISH_TO_HEB_ARTISTS, expand_performer_variants
from core.backup import fetch_video_metadata
from core.config import ComposerConfig, load_composer, load_overrides
from core.hebrew import heb_loose, norm_heb, title_similarity

CURRENT_YEAR = max(2026, datetime.date.today().year)

_YEAR_TOKEN_RE = re.compile(r"(?<!\d)(19[2-9]\d|20[0-2]\d)(?!\d)")
_LIFESPAN_PAIR_RE = re.compile(r"(?:19\d\d|20\d\d)\s*[-–]\s*(?:19\d\d|20\d\d)")
_DATE_YEAR_RE = re.compile(r"(?:\b|\D)(\d{1,2}\.\d{1,2}\.)?(19[2-9]\d|20[0-2]\d)\b")

COMPILATION_ALBUM_KEYWORDS: tuple[str, ...] = (
    "אוסף",
    "האוסף",
    "המיטב",
    "מבראשית",
    "להיטי זהב",
    "Greatest Hits",
    "Best Of",
    "Collection",
    "Anthology",
    "Remaster",
    "כל שירי",
    "היסטוריה",
    "ההיסטוריה",
    "שירי המדינה",
    "שירים לזיכרון",
    "שרתי לך ארצי",
    "מאז ועד היום",
    "שירים רבותי",
    "לדורותיו",
    "השירים שלנו",
    "נוסטלגיה",
    "מבצעים שונים",
    "קטלוג שירים",
    "שבעים ומשהו",
    "שירי יובל",
    "שירי מלחמת",
    "פעמוני היובל",
    "הקלטות נדירות",
    "כל הלהיטים",
    "הלהיטים",
    "גדולי",
    "השירים היפים",
    "שירים לנצח",
    "מהדורה",
    "מבצעים את",
    "עמותת הורז",
    "מיטב",
    "פזמונים שהיו",
    "מארז",
    "כולם שרים",
)

_ARCHIVE_CHANNEL_MARKERS: tuple[str, ...] = (
    "שיר עד",
    "shir ad",
    "רחל פרומן",
    "אוצר הזמר",
    "אוצרות ארכיון",
    "כאן | מוזיקה",
    "כאן ארכיון",
    "דודי פטימר",
    "נוסטלגיה",
    "משירי ארץ ישראל",
    "ללי שמר",
    "israeli classics",
    "israeli archive",
    "ישראפון",
    "israphon",
    "odedzentner",
    "guy alon",
    "aronia",
    "ron nostalgy",
    "ron nostalgia",
    "heapjoe",
    "alon eingev",
    "retro",
    "ארכיון",
)

_CONTEMPORARY_MARKERS: tuple[str, ...] = (
    "קולולם",
    "koolulam",
    "זהו זה",
    "הכוכב הבא",
    "בית ספר למוסיקה",
    "בית אבי חי",
    "חיל החינוך",
    "יונינה",
    "yonina",
    "כאן 11",
    "קשת 12",
    "רשת 13",
    "the voice",
    "x factor",
    "אמפי שוני",
    "קאבר",
    "עיבוד עכשווי",
)

_AUTHORITATIVE_DESC_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"שנת הקלטה[:\s]*[^\d\n]{0,8}(19[2-9]\d|20[0-2]\d)"),
    re.compile(r"הוקלט(?:ה)?\s+(?:ב[-]?(?:\d{1,2}\.\d{1,2}\.)?\s*|בשנת\s+|במהלך\s+)?[^\n.]{0,35}?(19[2-9]\d|20[0-2]\d)"),
    re.compile(r"(?:במקור\s+)?מתוך\s+(?:התכנית|התוכנית|פרק|המופע|הסרט|האלבום|התקליט|פסטיבל|אירוע)[^\n.]{0,80}?(19[2-9]\d|20[0-2]\d)"),
    re.compile(r"(?:האלבום|התקליט|השיר|הסינגל|התקליטון)[^\n.]{0,30}?(?:שיצא|יצא|ראה אור)\s+(?:לאור\s+)?(?:ב[-]?|בשנת\s+)(19[2-9]\d|20[0-2]\d)"),
    re.compile(r"הופעה חיה[^\n.]{0,45}?(19[2-9]\d|20[0-2]\d)"),
    re.compile(r"(?<!ספר\s)(?<!נדפס\s)(?<!פורסם\s)(?<!נפל\s)(?<!נהרג\s)(?<!השירים\s)משנת\s*(19[2-9]\d|20[0-2]\d)"),
)

_NON_RECORDING_DESC_PREFIXES: tuple[str, ...] = (
    "נדפס",
    "פורסם",
    "הספר",
    "מילים ותווים",
    "שנהרג",
    "נפל ב",
    "נולד ב",
    "2004-1930",
    "1930-2004",
    "לא אותו ביצוע",
    "הקלטה נוספת",
    "הלקטה נוספת",
    "בוצע לראשונה",
    "הוקלט לראשונה",
    "נכתב ב",
    "חובר ב",
    "נכתב ל",
    "השיר נכתב",
    "תקליטור",
    "הוצאה מחודשת",
    "כל השירים",
    "כתבה בספרה",
    "בספרה",
)

SOURCE_CONFIDENCE: dict[str, int] = {
    "manual_verified": 100,
    "video_title": 95,
    "canonical_album": 92,
    "archive_desc": 89,
    "stereo_ve_mono": 85,
    "discogs": 82,
    "musicbrainz": 80,
    "topic_album": 78,
    "streaming_api": 76,
    "desc_album": 74,
    "publish_date_contemporary": 65,
    "original_inherited": 55,
    "existing_curated": 50,
}

TRUSTED_COVER_YEAR_SOURCES: set[str] = {
    "manual_verified",
    "video_title",
    "canonical_album",
    "archive_desc",
    "stereo_ve_mono",
    "discogs",
    "musicbrainz",
    "topic_album",
    "streaming_api",
    "desc_album",
    "publish_date_contemporary",
}

_REISSUE_PRONE_SOURCES: set[str] = {
    "stereo_ve_mono",
    "discogs",
    "musicbrainz",
    "topic_album",
    "streaming_api",
    "desc_album",
    "publish_date_contemporary",
}


def merge_compilation_keywords(overrides: dict[str, Any] | None) -> tuple[str, ...]:
    """Combine generic compilation markers with composer-specific ignore keywords."""
    extra = ((overrides or {}).get("finder_overrides") or {}).get("compilation_year_ignore_keywords") or []
    seen: list[str] = list(COMPILATION_ALBUM_KEYWORDS)
    for kw in extra:
        ks = str(kw or "").strip()
        if ks and ks not in seen:
            seen.append(ks)
    return tuple(seen)


def is_compilation_album(text: str, extra_keywords: tuple[str, ...] = ()) -> bool:
    """Return True if album or collection title indicates a compilation/reissue."""
    if not text:
        return False
    low = str(text).lower()
    kws = COMPILATION_ALBUM_KEYWORDS + tuple(extra_keywords or ())
    return any(kw.lower() in low for kw in kws if kw)


def _strip_lifespans_and_song_years(text: str, song_title: str) -> str:
    cleaned = _LIFESPAN_PAIR_RE.sub(" ", str(text or ""))
    title_yrs = set(_YEAR_TOKEN_RE.findall(str(song_title or "")))
    for ty in title_yrs:
        cleaned = re.sub(rf"(?<!\d){re.escape(ty)}(?!\d)", " ", cleaned)
    return cleaned


def extract_explicit_title_years(
    video_title: str,
    matched_performer: str,
    song_title: str = "",
) -> dict[str, list[int]]:
    """Extract explicit 4-digit recording years from `video_title` and `matched_performer`."""
    vt_clean = _strip_lifespans_and_song_years(video_title, song_title)
    pf_clean = _strip_lifespans_and_song_years(matched_performer, song_title)

    # Ignore 4-digit numbers embedded inside non-song identifiers like dates only as whole tokens
    vt_years = sorted({int(y) for y in _YEAR_TOKEN_RE.findall(vt_clean) if 1920 <= int(y) <= CURRENT_YEAR})
    pf_years = sorted({int(y) for y in _YEAR_TOKEN_RE.findall(pf_clean) if 1920 <= int(y) <= CURRENT_YEAR})
    all_years = sorted(set(vt_years) | set(pf_years))
    return {"video_title": vt_years, "matched_performer": pf_years, "all": all_years}


def extract_authoritative_desc_years(
    short_description: str,
    channel: str,
    song_title: str = "",
    extra_comp_kws: tuple[str, ...] = (),
) -> list[tuple[int, str]]:
    """Extract high-confidence recording/release years from YouTube descriptions."""
    desc = str(short_description or "")
    if not desc.strip():
        return []

    found: list[tuple[int, str]] = []
    seen_yrs: set[int] = set()
    title_yrs = {int(y) for y in _YEAR_TOKEN_RE.findall(str(song_title or ""))}

    for raw_line in desc.splitlines():
        line = _LIFESPAN_PAIR_RE.sub(" ", raw_line.strip())
        if not line:
            continue
        if any(bad in line for bad in _NON_RECORDING_DESC_PREFIXES):
            continue
        for pat in _AUTHORITATIVE_DESC_PATTERNS:
            for m in pat.finditer(line):
                phrase = m.group(0)
                yr = int(m.group(1))
                if not (1920 <= yr <= CURRENT_YEAR) or yr in title_yrs:
                    continue
                if is_compilation_album(phrase, extra_comp_kws):
                    continue
                if yr not in seen_yrs:
                    seen_yrs.add(yr)
                    found.append((yr, phrase.strip()))
    return found


def extract_topic_album_year(
    short_description: str,
    channel: str,
    extra_comp_kws: tuple[str, ...] = (),
) -> tuple[int | None, str]:
    """Extract original album release year from YouTube Auto-Generated Topic metadata."""
    desc = str(short_description or "")
    is_topic = ("Provided to YouTube" in desc) or ("Auto-generated by YouTube" in desc) or str(channel).endswith("- Topic")
    if not is_topic or not desc.strip():
        return None, ""

    paras = [p.strip() for p in re.split(r"\n\s*\n", desc) if p.strip()]
    album_line = paras[2] if len(paras) >= 3 and not paras[2].startswith(("℗", "©", "Released on", "Auto-generated")) else ""
    if is_compilation_album(album_line, extra_comp_kws):
        return None, ""

    rel_m = re.search(r"Released on:\s*(19[2-9]\d|20[0-2]\d)-\d{2}-\d{2}", desc)
    p_m = re.search(r"[℗©]\s*(19[2-9]\d|20[0-2]\d)\b", desc)
    yr: int | None = None
    if p_m and rel_m:
        py, ry = int(p_m.group(1)), int(rel_m.group(1))
        # Prefer earlier of ℗ and Released-on when both refer to a single album release
        yr = min(py, ry)
    elif p_m:
        yr = int(p_m.group(1))
    elif rel_m:
        yr = int(rel_m.group(1))
    if yr is None or not (1920 <= yr <= CURRENT_YEAR):
        return None, ""
    return yr, album_line


def is_archive_uploader(channel: str) -> bool:
    """Return True if the YouTube channel primarily uploads historical archives."""
    ch_low = str(channel or "").lower()
    return any(mk in ch_low for mk in _ARCHIVE_CHANNEL_MARKERS)


def is_contemporary_release(
    video_title: str,
    matched_performer: str,
    channel: str,
    tier: str,
    publish_year: int | None,
    song_year: int | None,
) -> bool:
    """Detect modern TV/stage covers whose YouTube upload year reflects the recording year."""
    if not publish_year or publish_year < 2008:
        return False
    if is_archive_uploader(channel):
        return False
    blob = f"{video_title} {matched_performer} {channel}".lower()
    if any(mk in blob for mk in _CONTEMPORARY_MARKERS):
        return True
    return False


def _canonical_artist_tokens(name: str) -> set[str]:
    """Expand an artist string into normalized Hebrew & Latin tokens for cross-source matching."""
    out: set[str] = set()
    raw = str(name or "").strip()
    if not raw:
        return out
    clean = re.sub(r"\([^)]*\)", "", raw).strip()
    parts = [p.strip() for p in re.split(r"[,&/·•]|(?:\s+ו(?=[א-ת]))", clean) if p.strip()]
    parts.append(clean)
    eng_to_heb = {k.lower(): v for k, v in ENGLISH_TO_HEB_ARTISTS}

    for part in parts:
        for var in [part] + expand_performer_variants(part):
            nh = heb_loose(var)
            if nh:
                out.add(nh)
            pl = var.lower().strip()
            if pl in eng_to_heb:
                out.add(heb_loose(eng_to_heb[pl]))
        for heb_name, eng_tuple in ARTIST_ALIASES.items():
            heb_nh = heb_loose(heb_name)
            part_nh = heb_loose(part)
            part_low = part.lower()
            if part_nh == heb_nh or any(part_low == ea.lower() for ea in eng_tuple):
                out.add(heb_nh)
                for ea in eng_tuple:
                    out.add(norm_heb(ea))
    return {t for t in out if len(t) >= 3}


def _performer_matches(perf_a: str, perf_b: str) -> bool:
    if not perf_a or not perf_b:
        return False
    ta = _canonical_artist_tokens(perf_a)
    tb = _canonical_artist_tokens(perf_b)
    if ta & tb:
        return True
    for a in ta:
        for b in tb:
            if len(a) >= 5 and len(b) >= 5 and (a in b or b in a):
                return True
    return False


def refresh_missing_metadata(cfg: ComposerConfig, matched_entries: list[dict[str, Any]]) -> dict[str, int]:
    """Fetch full YouTube metadata via InnerTube/watch for any matched video missing in backup."""
    archive: dict[str, Any] = {}
    videos: dict[str, dict[str, Any]] = {}
    if cfg.metadata_backup_json.exists():
        try:
            archive = json.loads(cfg.metadata_backup_json.read_text(encoding="utf-8"))
            videos = dict(archive.get("videos") or {})
        except Exception:
            archive, videos = {}, {}

    missing_items: list[dict[str, Any]] = []
    seen_missing: set[str] = set()
    for it in matched_entries:
        sel = it.get("selected_video") or {}
        vid = sel.get("video_id", "")
        if not vid or vid in seen_missing:
            continue
        existing = videos.get(vid) or {}
        ym = existing.get("youtube_metadata") if isinstance(existing, dict) and "youtube_metadata" in existing else existing
        if not (isinstance(ym, dict) and ym.get("title") and ym.get("publish_date")):
            seen_missing.add(vid)
            missing_items.append(it)

    fetched_ok = 0
    fetched_with_meta = 0
    if missing_items:
        with ThreadPoolExecutor(max_workers=8) as ex:
            fut_map = {ex.submit(fetch_video_metadata, it["selected_video"]["video_id"]): it for it in missing_items}
            for fut in as_completed(fut_map):
                it = fut_map[fut]
                sel = it["selected_video"]
                vid = sel["video_id"]
                ym = fut.result()
                if ym.get("playability_status") == "OK":
                    fetched_ok += 1
                if ym.get("title") or ym.get("publish_date"):
                    fetched_with_meta += 1
                videos[vid] = {
                    "playlist_position": it.get("index", 0),
                    "song_number": it.get("index", 0),
                    "song_title": it.get("title", ""),
                    "year": it.get("year", ""),
                    "role": it.get("role_label_heb", ""),
                    "lyricist": it.get("lyricist", ""),
                    "composer": it.get("composer", ""),
                    "matched_performer": sel.get("matched_performer", ""),
                    "catalog_performers": it.get("catalog_performers", []),
                    "alternative_video_ids": [a.get("video_id") for a in it.get("alternative_videos", []) if a.get("video_id")],
                    "youtube_metadata": ym,
                }

        archive["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        archive["total_unique_videos"] = len(videos)
        archive["videos"] = videos
        cfg.metadata_backup_json.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "checked": len(matched_entries),
        "missing_before": len(missing_items),
        "fetched_ok": fetched_ok,
        "fetched_with_meta": fetched_with_meta,
    }


def lookup_streaming_release_year(
    title: str,
    performer: str,
    cache: dict[str, Any],
    extra_comp_kws: tuple[str, ...] = (),
) -> tuple[int | None, str]:
    """Query cached or live iTunes IL API for non-compilation album release year of `(title, performer)`."""
    perf_clean = re.sub(r"\([^)]*\)", "", str(performer or "")).strip()
    if not title or not perf_clean:
        return None, ""
    cache_key = f"{heb_loose(title)}||{heb_loose(perf_clean)}"
    if cache_key in cache:
        ent = cache[cache_key] or {}
        yr = ent.get("year")
        return (int(yr) if yr else None), str(ent.get("album") or "")

    term = f"{title} {perf_clean}".strip()
    url = "https://itunes.apple.com/search?term=" + urllib.parse.quote(term) + "&country=IL&media=music&entity=song&limit=12"
    best: tuple[int, str] | None = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
        for r in payload.get("results", []):
            trk = r.get("trackName") or ""
            art = r.get("artistName") or ""
            col = r.get("collectionName") or ""
            rdate = str(r.get("releaseDate") or "")
            if not col or is_compilation_album(col, extra_comp_kws):
                continue
            if not re.match(r"^(19[5-9]\d|20[0-2]\d)", rdate):
                continue
            if title_similarity(title, trk) < 0.78:
                continue
            if not _performer_matches(perf_clean, art):
                continue
            yr = int(rdate[:4])
            if 1950 <= yr <= CURRENT_YEAR and (best is None or yr < best[0]):
                best = (yr, col)
    except Exception:
        pass

    cache[cache_key] = {"year": best[0] if best else None, "album": best[1] if best else ""}
    return (best[0] if best else None), (best[1] if best else "")


def _load_json_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _build_discography_index(
    raw_dir: Path,
    extra_comp_kws: tuple[str, ...],
) -> tuple[dict[str, list[tuple[int, str, str, str]]], dict[str, int]]:
    """Build title->[(year, performer, album_title, source)] and title->song_year indices from raw_cache."""
    perf_records: dict[str, list[tuple[int, str, str, str]]] = {}
    song_year_map: dict[str, list[int]] = {}

    # Stereo VeMono
    svm = _load_json_safe(raw_dir / "stereo_ve_mono_raw.json")
    for alb in svm.get("albums", []):
        ym = re.search(r"(19[2-9]\d|20[0-2]\d)", str(alb.get("year") or ""))
        atitle = str(alb.get("title") or "")
        if not ym or is_compilation_album(atitle, extra_comp_kws):
            continue
        ayr = int(ym.group(1))
        alb_perf = str(alb.get("performer") or "")
        for tr in alb.get("tracks", []):
            tt = heb_loose(tr.get("title") or "")
            if not tt:
                continue
            tperfs = tr.get("performers") or ([alb_perf] if alb_perf else [])
            for tp in tperfs:
                perf_records.setdefault(tt, []).append((ayr, str(tp), atitle, "stereo_ve_mono"))
            song_year_map.setdefault(tt, []).append(ayr)

    # Discogs & MusicBrainz
    for fn, src_name in (("discogs_raw.json", "discogs"), ("musicbrainz_raw.json", "musicbrainz")):
        raw = _load_json_safe(raw_dir / fn)
        for rel in raw.get("releases", []):
            ym = re.search(r"(19[2-9]\d|20[0-2]\d)", str(rel.get("year") or ""))
            atitle = str(rel.get("title") or "")
            if not ym or is_compilation_album(atitle, extra_comp_kws):
                continue
            ayr = int(ym.group(1))
            r_art = str(rel.get("artist") or "")
            for tr in rel.get("tracks", []):
                tr_str = tr.get("title", "") if isinstance(tr, dict) else str(tr or "")
                tt = heb_loose(tr_str)
                if not tt:
                    continue
                perf_records.setdefault(tt, []).append((ayr, r_art, atitle, src_name))

    # Pizmonet & NLI song years
    piz = _load_json_safe(raw_dir / "pizmonet_raw.json")
    for s in piz.get("songs", []):
        ym = re.search(r"(19[2-9]\d|20[0-2]\d)", str(s.get("year") or ""))
        tt = heb_loose(s.get("title") or "")
        if tt and ym:
            song_year_map.setdefault(tt, []).append(int(ym.group(1)))

    nli = _load_json_safe(raw_dir / "nli_raw.json")
    for s in nli.get("songs", []):
        ym = re.search(r"(19[2-9]\d|20[0-2]\d)", str(s.get("year") or ""))
        tt = heb_loose(s.get("title") or "")
        if tt and ym:
            song_year_map.setdefault(tt, []).append(int(ym.group(1)))

    canonical_song_min = {k: min(v) for k, v in song_year_map.items() if v}
    return perf_records, canonical_song_min


def _match_canonical_album(
    item: dict[str, Any],
    full_desc: str,
    cfg: ComposerConfig,
) -> tuple[int, str, int] | None:
    """Match an entry to `discography.canonical_albums`, scoring title/album_group/description signals."""
    canon_albs = list(cfg.discography.get("canonical_albums", []))
    if not canon_albs:
        return None
    title = item.get("title", "")
    sel = item.get("selected_video") or {}
    ag = item.get("album_group", "")
    title_blob = " ".join([sel.get("matched_album", ""), sel.get("video_title", "")])
    perf = sel.get("matched_performer", "")
    is_cover = item.get("tier") == "5_cover"

    best: tuple[int, int, int, str] | None = None
    for alb in canon_albs:
        trks = alb.get("tracks") or []
        atitle = str(alb["title"])
        ag_match = bool(ag and (atitle in ag or ag in atitle))
        if title not in trks and not ag_match:
            continue
        ayr = int(alb["year"])
        kws = list(alb.get("keywords") or [])
        is_solo = bool(alb.get("is_creator_solo"))
        if is_solo and perf and not _performer_matches(perf, cfg.name_he):
            continue
        kw_in_title = any(k in title_blob for k in kws)
        kw_in_desc = any(k in full_desc for k in kws)
        if ag_match and (kw_in_title or kw_in_desc):
            score = 94
        elif kw_in_title:
            score = 92
        elif kw_in_desc:
            score = 90
        elif not is_cover and ag_match and "מתוך האלבום" not in full_desc and "מתוך התקליט" not in full_desc:
            score = 86
        else:
            continue
        solo_pref = 0 if (is_solo and _performer_matches(perf, cfg.name_he)) else 1
        rank_key = (-score, solo_pref, ayr, atitle)
        if best is None or rank_key < best:
            best = rank_key
    if best is None:
        return None
    return best[2], best[3], -best[0]


def _filter_reissue_cands(
    cands: list[tuple[int, int, str, str]],
    tier: str,
    existing_valid: str,
) -> list[tuple[int, int, str, str]]:
    """Prevent later CD reissues/compilations from overwriting valid earlier non-cover years."""
    if tier == "5_cover" or not existing_valid or not existing_valid.isdigit():
        return cands
    ex_yr = int(existing_valid)
    return [c for c in cands if not (c[2] in _REISSUE_PRONE_SOURCES and c[1] > ex_yr + 2)]


def verify_composer_years(
    slug: str,
    *,
    fetch_missing: bool = False,
    use_streaming_api: bool = False,
    apply: bool = False,
) -> dict[str, Any]:
    """Cross-verify and separate `song_year` + `recording_year` + `year_source` across a composer."""
    cfg = load_composer(slug)
    ov = load_overrides(slug)
    comp_kws = merge_compilation_keywords(ov)
    raw_dir = cfg.dir / "raw_cache"

    pdata = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    playlist = pdata.get("playlist", [])
    matched = [it for it in playlist if it.get("selected_video")]
    unmatched = [it for it in playlist if not it.get("selected_video")]

    refresh_stats = {"checked": len(matched), "missing_before": 0, "fetched_ok": 0, "fetched_with_meta": 0}
    if fetch_missing:
        refresh_stats = refresh_missing_metadata(cfg, matched)

    meta_raw = _load_json_safe(cfg.metadata_backup_json)
    meta_videos = meta_raw.get("videos", meta_raw) if isinstance(meta_raw, dict) else {}
    manual_rec_years: dict[str, Any] = ov.get("manual_recording_years") or {}
    manual_song_years: dict[str, Any] = ((ov.get("finder_overrides") or {}).get("manual_years")) or {}

    cat_data = _load_json_safe(cfg.catalog_json)
    cat_by_title = {s.get("title", ""): s for s in cat_data.get("songs", [])}

    perf_records, raw_song_years = _build_discography_index(raw_dir, comp_kws)
    stream_cache_path = raw_dir / "year_lookup_cache.json"
    stream_cache = _load_json_safe(stream_cache_path)

    contradictions: list[dict[str, Any]] = []
    evidence_by_idx: dict[int, list[tuple[int, int, str, str]]] = {}
    publish_year_by_idx: dict[int, int | None] = {}

    # Pass 1: Gather E1..E9 recording-year evidence per matched entry
    for item in matched:
        idx = int(item.get("index", 0))
        title = item.get("title", "")
        sel = item["selected_video"]
        vid = sel["video_id"]
        vtitle = sel.get("video_title", "")
        perf = sel.get("matched_performer", "")
        channel = sel.get("channel", "")
        tier = item.get("tier", "")

        m_entry = meta_videos.get(vid) or {}
        ym = m_entry.get("youtube_metadata") if isinstance(m_entry, dict) and "youtube_metadata" in m_entry else m_entry
        ym = ym or {}
        full_title = ym.get("title") or vtitle
        full_desc = ym.get("short_description") or sel.get("description") or ""
        pub_raw = str(ym.get("publish_date") or "")
        pub_yr = int(pub_raw[:4]) if re.match(r"^(19|20)\d\d", pub_raw) else None
        publish_year_by_idx[idx] = pub_yr

        cands: list[tuple[int, int, str, str]] = []  # (conf, year, source, detail)
        is_tv = item.get("album_group") == cfg.tv_album_group

        # E1: Manual recording year override
        if vid in manual_rec_years and str(manual_rec_years[vid]).isdigit():
            cands.append((SOURCE_CONFIDENCE["manual_verified"], int(manual_rec_years[vid]), "manual_verified", "overrides.manual_recording_years"))

        # E2: Explicit title/performer years
        ty = extract_explicit_title_years(full_title, perf, title)
        if ty["video_title"] and ty["matched_performer"] and not (set(ty["video_title"]) & set(ty["matched_performer"])):
            contradictions.append({
                "index": idx, "title": title, "vid": vid, "kind": "TITLE_VS_PERFORMER_YEAR",
                "detail": f"title={ty['video_title']} vs perf={ty['matched_performer']}",
            })
        if ty["all"]:
            chosen_ty = max(ty["all"]) if tier == "5_cover" else min(ty["all"])
            if pub_yr and chosen_ty == pub_yr + 1:
                cands.append((SOURCE_CONFIDENCE["video_title"], pub_yr, "video_title", f"title={ty['all']}~pub={pub_yr}"))
            else:
                cands.append((SOURCE_CONFIDENCE["video_title"], chosen_ty, "video_title", f"title={ty['all']}"))

        if not is_tv:
            # E4: Canonical albums matched to this video
            canon_hit = _match_canonical_album(item, full_desc, cfg)
            if canon_hit:
                ayr, atitle, aconf = canon_hit
                cands.append((aconf, ayr, "canonical_album", atitle))

            # E3: Authoritative description years vs generic album citations on non-archive channels
            is_arch = is_archive_uploader(channel)
            for dy, dphrase in extract_authoritative_desc_years(full_desc, channel, title, comp_kws):
                is_strong_phrase = any(
                    mk in dphrase for mk in ("הוקלט", "שנת הקלטה", "הופעה חיה", "התכנית", "התוכנית", "פסטיבל")
                )
                is_weak_album_cite = (
                    not is_arch
                    and ("מתוך האלבום" in dphrase or "מתוך התקליט" in dphrase)
                    and not is_strong_phrase
                )
                d_src = "desc_album" if is_weak_album_cite else "archive_desc"
                if pub_yr and dy == pub_yr + 1:
                    cands.append((SOURCE_CONFIDENCE[d_src], pub_yr, d_src, f"{dphrase[:50]}~pub={pub_yr}"))
                else:
                    cands.append((SOURCE_CONFIDENCE[d_src], dy, d_src, dphrase[:60]))

            # E5 & E6: Discography match by (title, performer) in Stereo VeMono / Discogs / MusicBrainz
            tt_key = heb_loose(title)
            for dyr, dperf, dalb, dsrc in perf_records.get(tt_key, []):
                if _performer_matches(perf, dperf):
                    cands.append((SOURCE_CONFIDENCE[dsrc], dyr, dsrc, dalb[:50]))

            # E7: YouTube Topic non-compilation album year (only if no higher-confidence LP contradicts or reissue)
            t_yr, t_alb = extract_topic_album_year(full_desc, channel, comp_kws)
            if t_yr:
                high_yrs = [c[1] for c in cands if c[0] >= 80]
                if not high_yrs or abs(t_yr - min(high_yrs)) <= 5 or t_yr <= min(high_yrs):
                    cands.append((SOURCE_CONFIDENCE["topic_album"], t_yr, "topic_album", t_alb[:50]))

            # E8: Streaming API lookup when still below 78 confidence
            best_so_far = max((c[0] for c in cands), default=0)
            if use_streaming_api and best_so_far < 78:
                s_yr, s_alb = lookup_streaming_release_year(title, perf, stream_cache, comp_kws)
                if s_yr:
                    cands.append((SOURCE_CONFIDENCE["streaming_api"], s_yr, "streaming_api", s_alb[:50]))

        # Publish-date upper-bound filter on non-manual evidence
        filtered_cands: list[tuple[int, int, str, str]] = []
        for conf, yr, src, det in cands:
            if pub_yr and src != "manual_verified" and yr > pub_yr:
                contradictions.append({
                    "index": idx, "title": title, "vid": vid, "kind": "EVIDENCE_AFTER_PUBLISH",
                    "detail": f"{src}={yr} > publish_year={pub_yr}",
                })
                continue
            filtered_cands.append((conf, yr, src, det))

        evidence_by_idx[idx] = sorted(filtered_cands, key=lambda x: (-x[0], x[1]))

    if use_streaming_api:
        raw_dir.mkdir(parents=True, exist_ok=True)
        stream_cache_path.write_text(json.dumps(stream_cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # Pass 2: Resolve canonical song_year per unique song title
    song_groups: dict[str, list[dict[str, Any]]] = {}
    for it in playlist:
        song_groups.setdefault(it.get("title", ""), []).append(it)

    canonical_song_year: dict[str, str] = {}
    for title, grp in song_groups.items():
        # Check strong original recording evidence first
        orig_rec_yrs: list[int] = []
        any_non_parody_rec_yrs: list[int] = []
        for it in grp:
            if not it.get("selected_video"):
                continue
            sel = it["selected_video"]
            vtxt = f"{sel.get('matched_performer', '')} {sel.get('video_title', '')}"
            if it.get("album_group") == cfg.tv_album_group or any(w in vtxt for w in ("ראיון", "פרודיה", "סקיצה נדירה", "הקדמה לשיר")):
                continue
            it_old_rec = str(it.get("recording_year") if "recording_year" in it else it.get("year") or "").strip()
            it_pub = publish_year_by_idx.get(int(it["index"]))
            it_existing = (
                it_old_rec
                if (it_old_rec.isdigit() and it_old_rec != "2099" and (not it_pub or int(it_old_rec) <= it_pub))
                else ""
            )
            cands = _filter_reissue_cands(evidence_by_idx.get(int(it["index"]), []), it.get("tier", ""), it_existing)
            eff_yr = cands[0][1] if cands else (int(it_existing) if it_existing and it.get("tier") != "5_cover" else None)
            if eff_yr is not None:
                any_non_parody_rec_yrs.append(eff_yr)
                if it.get("dual_role") == "original_performance" or it.get("is_true_original"):
                    orig_rec_yrs.append(eff_yr)

        sy: str = ""
        if title in manual_song_years and str(manual_song_years[title]).isdigit():
            m_yr = int(manual_song_years[title])
            if orig_rec_yrs and orig_rec_yrs[0] != m_yr and abs(orig_rec_yrs[0] - m_yr) >= 1:
                contradictions.append({
                    "index": grp[0].get("index"), "title": title, "vid": "", "kind": "MANUAL_SONG_YEAR_VS_ORIGINAL",
                    "detail": f"manual_years={m_yr} vs original_evidence={orig_rec_yrs[0]}",
                })
            sy = str(m_yr)
        elif orig_rec_yrs:
            sy = str(min(orig_rec_yrs))
        elif any_non_parody_rec_yrs and len(grp) == 1:
            sy = str(min(any_non_parody_rec_yrs))
        else:
            tt_key = heb_loose(title)
            if tt_key in raw_song_years:
                sy = str(raw_song_years[tt_key])
            else:
                # Fall back to existing song_year or original_performance year or catalog notes year
                for it in grp:
                    ex_sy = str(it.get("song_year") or "").strip()
                    if ex_sy.isdigit() and ex_sy != "2099":
                        sy = ex_sy
                        break
                if not sy:
                    for it in grp:
                        ex_yr = str(it.get("year") or "").strip()
                        if ex_yr.isdigit() and ex_yr != "2099" and (len(grp) == 1 or it.get("dual_role") == "original_performance"):
                            sy = ex_yr
                            break
                if not sy:
                    cat_song = cat_by_title.get(title) or {}
                    cy = str(cat_song.get("year") or "").strip()
                    if cy.isdigit() and cy != "2099":
                        sy = cy
        if sy.isdigit() and any_non_parody_rec_yrs and title not in manual_song_years:
            earliest_rec = min(any_non_parody_rec_yrs)
            if earliest_rec < int(sy):
                sy = str(earliest_rec)
        canonical_song_year[title] = sy

    # Pass 3: Assign song_year, recording_year, year_source, and year cleanly
    resolved_by_src: dict[str, int] = {}
    updated_rows = 0
    cleared_cover_rows: list[dict[str, Any]] = []
    missing_rec_rows: list[dict[str, Any]] = []
    missing_song_matched: set[str] = set()
    missing_song_archive: set[str] = set()

    for it in playlist:
        title = it.get("title", "")
        sy = canonical_song_year.get(title, "")
        sy_int = int(sy) if sy.isdigit() else None

        old_rec = str(it.get("recording_year") if "recording_year" in it else it.get("year") or "").strip()
        old_sy = str(it.get("song_year") or "").strip()
        old_src = str(it.get("year_source") or "").strip()

        if not it.get("selected_video"):
            if not sy:
                missing_song_archive.add(title)
            # Unmatched archive row tracks song_year
            new_rec, new_src, new_yr = "", old_src, sy
            if it.get("song_year") != sy or it.get("recording_year") != new_rec or it.get("year") != new_yr:
                updated_rows += 1
            if apply:
                it["song_year"] = sy
                it["recording_year"] = ""
                it["year"] = sy
            continue

        if not sy:
            missing_song_matched.add(title)

        idx = int(it["index"])
        sel = it["selected_video"]
        vid = sel["video_id"]
        tier = it.get("tier", "")
        dual = it.get("dual_role", "")
        ver_total = int(it.get("ver_total") or 1)
        pub_yr = publish_year_by_idx.get(idx)
        cands = evidence_by_idx.get(idx, [])

        # Check E9 (contemporary TV/show/artist cover) if no stronger evidence
        if not cands and is_contemporary_release(
            sel.get("video_title", ""),
            sel.get("matched_performer", ""),
            sel.get("channel", ""),
            tier,
            pub_yr,
            sy_int,
        ):
            cands = [(SOURCE_CONFIDENCE["publish_date_contemporary"], pub_yr, "publish_date_contemporary", f"publish={pub_yr}")]  # type: ignore[list-item]

        existing_valid = old_rec if (old_rec.isdigit() and old_rec != "2099" and (not pub_yr or int(old_rec) <= pub_yr)) else ""
        cands = _filter_reissue_cands(cands, tier, existing_valid)

        if cands:
            _, best_yr, best_src, _ = cands[0]
            new_rec = str(best_yr)
            new_src = best_src
        elif tier == "5_cover":
            if existing_valid and existing_valid != sy and ver_total > 1:
                new_rec = existing_valid
                new_src = "existing_curated"
            else:
                new_rec = ""
                new_src = ""
                if old_rec == sy and old_rec:
                    cleared_cover_rows.append({"index": idx, "title": title, "vid": vid, "perf": sel.get("matched_performer", ""), "old_yr": old_rec})
        elif dual == "original_performance" or ver_total == 1:
            if existing_valid:
                new_rec = existing_valid
                new_src = "original_inherited" if existing_valid == sy else "existing_curated"
            elif sy:
                new_rec = sy
                new_src = "original_inherited"
            else:
                new_rec = ""
                new_src = ""
        else:
            # Non-cover additional or creator performance with no direct evidence
            if existing_valid and existing_valid != sy:
                new_rec = existing_valid
                new_src = "existing_curated"
            elif existing_valid and old_src == "existing_curated":
                new_rec = existing_valid
                new_src = "existing_curated"
            else:
                # Avoid unverified copied song years on single-perfs when existing year just mirrored song_year
                new_rec = existing_valid if existing_valid else ""
                new_src = "original_inherited" if new_rec else ""

        if new_src:
            resolved_by_src[new_src] = resolved_by_src.get(new_src, 0) + 1
        if not new_rec and it.get("album_group") != cfg.tv_album_group:
            missing_rec_rows.append({
                "index": idx,
                "title": title,
                "vid": vid,
                "tier": tier,
                "perf": sel.get("matched_performer", ""),
                "ch": sel.get("channel", ""),
                "pub_yr": pub_yr or "",
                "song_year": sy,
            })

        if existing_valid and new_rec and existing_valid != new_rec:
            contradictions.append({
                "index": idx, "title": title, "vid": vid, "kind": "EXISTING_VS_VERIFIED",
                "detail": f"old={existing_valid} -> verified={new_rec} ({new_src})",
            })

        changed_here = (
            old_sy != sy
            or str(it.get("recording_year") or "") != new_rec
            or old_src != new_src
            or str(it.get("year") or "") != new_rec
        )
        if changed_here:
            updated_rows += 1
        if apply:
            it["song_year"] = sy
            it["recording_year"] = new_rec
            it["year_source"] = new_src
            it["year"] = new_rec

    if apply:
        cfg.playlist_json.write_text(json.dumps(pdata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    missing_song_archive -= missing_song_matched
    all_missing_song = missing_song_matched | missing_song_archive

    return {
        "slug": cfg.slug,
        "name_he": cfg.name_he,
        "apply": apply,
        "refresh_stats": refresh_stats,
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "updated_rows": updated_rows,
        "resolved_by_source": dict(sorted(resolved_by_src.items(), key=lambda x: -x[1])),
        "cleared_cover_count": len(cleared_cover_rows),
        "cleared_covers_sample": cleared_cover_rows[:15],
        "missing_recording_year_count": len(missing_rec_rows),
        "missing_recording_years": missing_rec_rows,
        "missing_song_year_matched_count": len(missing_song_matched),
        "missing_song_year_archive_count": len(missing_song_archive),
        "missing_song_year_count": len(all_missing_song),
        "contradictions_count": len(contradictions),
        "contradictions": contradictions,
    }


def format_year_verification_report(rep: dict[str, Any], max_items: int = 30) -> str:
    """Format a readable CLI summary of `verify_composer_years`."""
    rf = rep["refresh_stats"]
    lines = [
        f"Year Verification [{rep['slug']}] ({rep['name_he']}) | apply={rep['apply']}: "
        f"{rep['matched_count']} matched, {rep['unmatched_count']} archive | updated_rows={rep['updated_rows']}",
        f"  Metadata backup refresh: missing_before={rf['missing_before']}, fetched_ok={rf['fetched_ok']}, fetched_with_meta={rf.get('fetched_with_meta', 0)}",
        f"  Recording-year sources: {rep['resolved_by_source']}",
        f"  Cleared copied cover years: {rep['cleared_cover_count']} | "
        f"Missing recording_year: {rep['missing_recording_year_count']} | "
        f"Missing song_year titles: {rep['missing_song_year_count']} (matched={rep.get('missing_song_year_matched_count', 0)}, archive={rep.get('missing_song_year_archive_count', 0)})",
    ]
    if rep["contradictions"]:
        lines.append(f"  Contradictions / Corrections ({rep['contradictions_count']}):")
        for c in rep["contradictions"][:max_items]:
            lines.append(f"    [{c['kind']}] #{c['index']} {c['title']} ({c['vid']}): {c['detail']}")
    if rep["missing_recording_years"]:
        lines.append(f"  Still missing recording_year (showing {min(len(rep['missing_recording_years']), max_items)}/{rep['missing_recording_year_count']}):")
        for m in rep["missing_recording_years"][:max_items]:
            lines.append(
                f"    #{m['index']} {m['title']} ({m['vid']}) | {m['tier']} | perf={m['perf']} | pub={m['pub_yr']} | song_yr={m['song_year']}"
            )
    return "\n".join(lines)
