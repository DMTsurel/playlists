"""Automated multi-composer playlist, attribution, audio-quality, and export QA auditor."""

from __future__ import annotations

import json
import re
from typing import Any

from core.artists import ACUM_PERFORMER_EXACT_MAP, check_performer_year_anachronism
from core.config import ComposerConfig, load_composer, load_overrides
from core.hebrew import has_bad_keyword, norm_heb, parse_duration_seconds
from core.ranking import partition_matched_blocks
from core.year_verifier import (
    TRUSTED_COVER_YEAR_SOURCES,
    extract_authoritative_desc_years,
    extract_explicit_title_years,
    matches_reissue_rerecording_album,
    merge_compilation_keywords,
)

_NON_CLIP_SUBSTRINGS: tuple[str, ...] = ("ראיון", "פרודיה", "סקיצה נדירה", "חזרה,", "הקדמה לשיר")

_AI_FANMIX_MARKERS: tuple[str, ...] = (
    "בינה מלאכותית",
    "ללא תזמורת",
    "מיקס מעריצים",
    "שיפוץ סאונד",
    " ai ",
    "(ai)",
)
_NON_SONG_MARKERS: tuple[str, ...] = (
    "ראיון",
    "סקיצה",
    "פרודיה",
    "חזרה,",
    "מערכון",
    "שירה בציבור",
    "הקהל שר",
)
_STUDIO_TIERS: set[str] = {"1_album_naomi", "1_album_creator", "2_album_original"}
_LIVE_MARKERS_HE: tuple[str, ...] = ("בהופעה", "הופעה חיה", "צוותא", "קונצרט")


def _parse_year(val: Any) -> int | None:
    s = str(val or "").strip()
    if re.fullmatch(r"\d{4}", s):
        return int(s)
    return None


def _is_creator_credited(item: dict[str, Any], cfg: ComposerConfig) -> bool:
    sel = item.get("selected_video") or {}
    blob = " ".join(
        str(x or "")
        for x in (sel.get("matched_performer"), sel.get("video_title"), sel.get("channel"))
    )
    name_he_norm = norm_heb(cfg.name_he)
    if name_he_norm and name_he_norm in norm_heb(blob):
        return True
    name_en_low = cfg.name_en.strip().lower()
    if name_en_low and name_en_low in blob.lower():
        return True
    return False


def _issue(code: str, index: Any, title: str, video_id: str, detail: str) -> dict[str, Any]:
    return {
        "code": code,
        "index": index,
        "title": title,
        "video_id": video_id,
        "detail": detail,
    }


def _check_primary_pairing(
    primary_items: list[dict[str, Any]],
    cfg: ComposerConfig,
    warnings: list[dict[str, Any]],
) -> None:
    by_title: dict[str, list[dict[str, Any]]] = {}
    for it in primary_items:
        by_title.setdefault(it.get("title", ""), []).append(it)

    creator_tiers = set(cfg.creator_performance_tiers)
    mode = cfg.dual_performance_mode

    for title, group in by_title.items():
        if mode == "original_only" and len(group) > 1:
            warnings.append(
                _issue(
                    "PRIMARY_MULTI_NON_PERFORMER",
                    group[0].get("index"),
                    title,
                    group[0]["selected_video"]["video_id"],
                    f"dual_performance_mode=original_only but {len(group)} versions appear in p1..p3",
                )
            )
            continue

        if mode == "original_plus_creator":
            if len(group) > 2:
                warnings.append(
                    _issue(
                        "PRIMARY_OVER_TWO",
                        group[0].get("index"),
                        title,
                        group[0]["selected_video"]["video_id"],
                        f"{len(group)} versions in primary block p1..p3 (max 2 expected)",
                    )
                )
            elif len(group) == 2:
                is_c0 = group[0].get("tier") in creator_tiers
                is_c1 = group[1].get("tier") in creator_tiers
                vid0 = group[0]["selected_video"]["video_id"]
                vid1 = group[1]["selected_video"]["video_id"]
                if is_c0 and is_c1:
                    warnings.append(
                        _issue(
                            "PRIMARY_DOUBLE_CREATOR",
                            group[1].get("index"),
                            title,
                            vid1,
                            "Two creator performances paired back-to-back in primary block",
                        )
                    )
                elif (not is_c0) and (not is_c1):
                    warnings.append(
                        _issue(
                            "PRIMARY_DOUBLE_NON_CREATOR",
                            group[1].get("index"),
                            title,
                            vid1,
                            "Two non-creator performances paired together in primary block",
                        )
                    )
                elif is_c0 and group[1].get("tier") == "5_cover":
                    warnings.append(
                        _issue(
                            "PRIMARY_COVER_AFTER_CREATOR_ORIGINAL",
                            group[1].get("index"),
                            title,
                            vid1,
                            f"Cover #{group[1].get('index')} paired right after creator original ({vid0})",
                        )
                    )


def audit_composer(slug: str) -> dict[str, Any]:
    """Run hard-invariant errors and editorial/audio quality warnings on a composer."""
    cfg = load_composer(slug)
    ov = load_overrides(slug)
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    playlist = data.get("playlist", [])

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    bad_ids: dict[str, str] = ov.get("bad_video_ids") or {}
    qa_exceptions: dict[str, Any] = ov.get("qa_allow_exceptions") or {}
    approved_iconic: dict[str, Any] = ov.get("approved_iconic_primaries") or {}
    reissue_rules: list[dict[str, Any]] = list(ov.get("reissue_rerecording_albums") or [])
    trim_bounds: dict[str, Any] = ov.get("video_trim_bounds") or {}
    comp_kws = merge_compilation_keywords(ov)
    strict_perf_only = bool(ov.get("performance_only_strict_creator_match", True))
    excluded_norm = {norm_heb(x) for x in (ov.get("excluded_normalized_songs") or []) if norm_heb(x)}
    creator_tiers = set(cfg.creator_performance_tiers)

    meta_videos: dict[str, Any] = {}
    if cfg.metadata_backup_json.exists():
        try:
            mraw = json.loads(cfg.metadata_backup_json.read_text(encoding="utf-8"))
            meta_videos = mraw.get("videos", mraw) if isinstance(mraw, dict) else {}
        except Exception:
            meta_videos = {}

    song_years_seen: dict[str, set[str]] = {}
    matched_titles_with_videos: set[str] = {str(it.get("title", "")) for it in playlist if it.get("selected_video")}

    def _is_allowed_exception(code: str, vid: str) -> bool:
        code_map = qa_exceptions.get(code)
        return isinstance(code_map, dict) and bool(vid) and vid in code_map

    def _is_approved_iconic(song_title: str, video_id: str) -> bool:
        if not video_id:
            return False
        if video_id in approved_iconic:
            return True
        spec = approved_iconic.get(song_title)
        if isinstance(spec, str):
            return spec == video_id
        if isinstance(spec, dict):
            return spec.get("video_id") == video_id
        return False

    matched = [it for it in playlist if it.get("selected_video")]
    unmatched = [it for it in playlist if not it.get("selected_video")]

    blocks = partition_matched_blocks(matched, cfg)
    primary_items = blocks["p1"] + blocks["p2"] + blocks["p3"]
    primary_keys = {id(it) for it in primary_items}
    tv_keys = {id(it) for it in blocks["tv"]}
    tail_keys = {id(it) for it in blocks["tail"]}

    for item in playlist:
        idx = item.get("index")
        title = item.get("title", "")
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id", "")

        if norm_heb(title) in excluded_norm:
            errors.append(
                _issue(
                    "EXCLUDED_SONG_PRESENT",
                    idx,
                    title,
                    vid,
                    "Song matches overrides['excluded_normalized_songs']",
                )
            )

        if any(str(item.get(yk, "")).strip() == "2099" for yk in ("year", "song_year", "recording_year")):
            errors.append(_issue("PLACEHOLDER_YEAR", idx, title, vid, "Placeholder year '2099' present"))
        else:
            yr_num = _parse_year(item.get("year"))
            if yr_num is not None and (yr_num < 1920 or yr_num > 2030):
                warnings.append(_issue("SUSPICIOUS_YEAR", idx, title, vid, f"Unusual recording year: {yr_num}"))

        if vid and "recording_year" in item:
            if str(item.get("year") or "").strip() != str(item.get("recording_year") or "").strip():
                errors.append(
                    _issue(
                        "YEAR_FIELD_DESYNC",
                        idx,
                        title,
                        vid,
                        f"year='{item.get('year', '')}' != recording_year='{item.get('recording_year', '')}'",
                    )
                )
        elif (not vid) and "song_year" in item:
            if str(item.get("year") or "").strip() != str(item.get("song_year") or "").strip():
                errors.append(
                    _issue(
                        "YEAR_FIELD_DESYNC",
                        idx,
                        title,
                        "",
                        f"Archive year='{item.get('year', '')}' != song_year='{item.get('song_year', '')}'",
                    )
                )

        sy_val = str(item.get("song_year") or "").strip()
        if sy_val and sy_val != "2099":
            song_years_seen.setdefault(title, set()).add(sy_val)

        for perf in list(item.get("catalog_performers") or []) + ([sel.get("matched_performer", "")] if sel else []):
            if str(perf).strip() in ACUM_PERFORMER_EXACT_MAP:
                warnings.append(
                    _issue(
                        "REVERSED_ACUM_NAME",
                        idx,
                        title,
                        vid,
                        f"Unnormalized ACUM performer name: '{perf}'",
                    )
                )
                break

        if not vid:
            if not (item.get("archive_links") or []):
                warnings.append(_issue("ARCHIVE_NO_LINKS", idx, title, "", "Unmatched archive song has zero archive_links"))
            continue

        if vid in bad_ids:
            errors.append(
                _issue("BAD_VIDEO_PRIMARY", idx, title, vid, f"Blacklisted primary video: {bad_ids[vid]}")
            )
        for alt in item.get("alternative_videos") or []:
            avid = alt.get("video_id", "")
            if avid in bad_ids:
                warnings.append(
                    _issue("BAD_VIDEO_ALT", idx, title, avid, f"Blacklisted backup video: {bad_ids[avid]}")
                )

        if item.get("role_category") == "performance_only" and strict_perf_only:
            if not _is_creator_credited(item, cfg):
                errors.append(
                    _issue(
                        "PERF_ONLY_NON_CREATOR",
                        idx,
                        title,
                        vid,
                        f"performance_only song missing creator credit ({sel.get('matched_performer', '')})",
                    )
                )

        vtitle = sel.get("video_title", "")
        channel = sel.get("channel", "")
        perf = sel.get("matched_performer", "")
        desc = sel.get("description", "")
        is_tv = id(item) in tv_keys
        is_tail = id(item) in tail_keys
        is_primary = id(item) in primary_keys

        if (not is_tv) and (not is_tail) and has_bad_keyword(vtitle, channel, perf):
            errors.append(
                _issue(
                    "BAD_KEYWORD_PRIMARY",
                    idx,
                    title,
                    vid,
                    f"Matched karaoke/playback/bad keyword in '{vtitle}' / '{perf}'",
                )
            )

        blob_low = f" {vtitle} {desc} {perf} ".lower()
        if any(mk in blob_low for mk in _AI_FANMIX_MARKERS):
            warnings.append(
                _issue("AI_OR_FAN_MIX", idx, title, vid, f"Possible AI or fan-remixed audio in '{vtitle}'")
            )

        title_perf_low = f"{vtitle} {perf}".lower()
        if is_primary and any(mk in title_perf_low for mk in _NON_SONG_MARKERS):
            warnings.append(
                _issue(
                    "NON_SONG_IN_PRIMARY",
                    idx,
                    title,
                    vid,
                    f"Non-song/interview/sketch marker in primary block: '{vtitle}' ({perf})",
                )
            )

        if item.get("tier") in _STUDIO_TIERS and not is_tv:
            if any(mk in title_perf_low for mk in _LIVE_MARKERS_HE) or re.search(r"\blive\b", title_perf_low):
                warnings.append(
                    _issue(
                        "LIVE_IN_STUDIO_TIER",
                        idx,
                        title,
                        vid,
                        f"Live marker on studio tier {item.get('tier')}: '{vtitle}'",
                    )
                )

        if vid in trim_bounds and isinstance(trim_bounds[vid], dict):
            tb = trim_bounds[vid]
            try:
                t_start = int(tb.get("start") or 0)
                t_end = int(tb.get("end") or 0)
            except (TypeError, ValueError):
                t_start, t_end = -1, -1
            raw_dur_sec = parse_duration_seconds(sel.get("duration", ""))
            trim_err = ""
            if t_start < 0 or (t_end != 0 and t_end <= t_start):
                trim_err = f"Invalid trim bounds start={t_start}, end={t_end}"
            elif raw_dur_sec > 0 and (t_start >= raw_dur_sec or t_end > raw_dur_sec + 2):
                trim_err = f"Trim bounds start={t_start}, end={t_end} exceed video duration {raw_dur_sec}s"
            if trim_err:
                errors.append(_issue("INVALID_TRIM_BOUNDS", idx, title, vid, trim_err))

        if not is_tv:
            dur_sec = parse_duration_seconds(sel.get("duration", ""))
            if dur_sec <= 0:
                warnings.append(_issue("MISSING_DURATION", idx, title, vid, "Missing or unparseable video duration"))
            else:
                if (not is_tail) and dur_sec < 65:
                    warnings.append(
                        _issue("SUSPICIOUSLY_SHORT", idx, title, vid, f"Short duration {sel.get('duration')} (< 65s)")
                    )
                if dur_sec > 480:
                    warnings.append(
                        _issue("SUSPICIOUSLY_LONG", idx, title, vid, f"Long non-TV duration {sel.get('duration')} (> 8m)")
                    )

            rec_yr_str = str(item.get("recording_year") if "recording_year" in item else item.get("year", "") or "").strip()
            rec_yr_num = _parse_year(rec_yr_str)
            song_yr_str = str(item.get("song_year") or "").strip()
            song_yr_num = _parse_year(song_yr_str)
            yr_src = str(item.get("year_source") or "").strip()

            m_entry = meta_videos.get(vid) or {}
            ym = m_entry.get("youtube_metadata") if isinstance(m_entry, dict) and "youtube_metadata" in m_entry else m_entry
            ym = ym or {}
            full_title = ym.get("title") or vtitle
            full_desc = ym.get("short_description") or desc
            pub_yr = _parse_year(str(ym.get("publish_date") or "")[:4])

            if "recording_year" in item and not rec_yr_str:
                warnings.append(
                    _issue("MISSING_RECORDING_YEAR", idx, title, vid, f"Blank recording_year ({item.get('tier')}, perf='{perf}')")
                )

            ty = extract_explicit_title_years(full_title, perf, title)
            if ty["video_title"] and ty["matched_performer"] and not (set(ty["video_title"]) & set(ty["matched_performer"])):
                errors.append(
                    _issue(
                        "TITLE_YEAR_MISMATCH",
                        idx,
                        title,
                        vid,
                        f"Conflicting explicit years in video_title {ty['video_title']} vs matched_performer {ty['matched_performer']}",
                    )
                )
            elif rec_yr_num is not None and ty["all"] and rec_yr_num not in ty["all"]:
                # Allow seasonal TV finals titled with the upcoming year (e.g. '2025' airing Nov/Dec 2024).
                if not (pub_yr is not None and rec_yr_num == pub_yr and ty["all"] == [pub_yr + 1]):
                    errors.append(
                        _issue(
                            "TITLE_YEAR_MISMATCH",
                            idx,
                            title,
                            vid,
                            f"recording_year={rec_yr_num} contradicts explicit title/performer year {ty['all']} ('{full_title}')",
                        )
                    )

            if rec_yr_num is not None and pub_yr is not None and rec_yr_num > pub_yr:
                errors.append(
                    _issue(
                        "RECORDING_AFTER_PUBLISH",
                        idx,
                        title,
                        vid,
                        f"recording_year={rec_yr_num} is later than YouTube publish_year={pub_yr}",
                    )
                )

            if rec_yr_num is not None and yr_src not in {"canonical_album", "stereo_ve_mono", "discogs", "manual_verified"}:
                desc_hits = extract_authoritative_desc_years(full_desc, channel, title, comp_kws)
                if desc_hits:
                    hys = [y for y, _ in desc_hits]
                    if rec_yr_num not in hys and all(abs(rec_yr_num - hy) >= 2 for hy in hys):
                        warnings.append(
                            _issue(
                                "DESC_YEAR_MISMATCH",
                                idx,
                                title,
                                vid,
                                f"recording_year={rec_yr_num} differs from description recording year {desc_hits[0]}",
                            )
                        )

            if item.get("tier") == "5_cover" and rec_yr_str and song_yr_str and rec_yr_str == song_yr_str:
                if yr_src not in TRUSTED_COVER_YEAR_SOURCES:
                    warnings.append(
                        _issue(
                            "COVER_COPIED_SONG_YEAR",
                            idx,
                            title,
                            vid,
                            f"5_cover has recording_year==song_year ({rec_yr_str}) without independent year_source ('{yr_src or 'none'}')",
                        )
                    )

            if rec_yr_num is not None and song_yr_num is not None and rec_yr_num < song_yr_num:
                warnings.append(
                    _issue(
                        "RECORDING_BEFORE_SONG",
                        idx,
                        title,
                        vid,
                        f"recording_year={rec_yr_num} precedes song_year={song_yr_num}",
                    )
                )

            if rec_yr_num is not None:
                anach_reason = check_performer_year_anachronism(perf, rec_yr_num)
                if anach_reason:
                    warnings.append(_issue("PERFORMER_DEBUT_ANACHRONISM", idx, title, vid, anach_reason))

            reissue_reason = matches_reissue_rerecording_album(
                reissue_rules, perf, full_title, channel, full_desc, song_yr_num
            )
            if reissue_reason:
                warnings.append(_issue("REISSUE_RERECORDING_ALBUM", idx, title, vid, reissue_reason))

            if (not is_primary) and (not is_tail) and yr_src in ("original_inherited", "unverified_inherited"):
                warnings.append(
                    _issue(
                        "NON_PRIMARY_INHERITED_YEAR",
                        idx,
                        title,
                        vid,
                        f"Non-primary entry has inherited year_source='{yr_src}' ({rec_yr_str})",
                    )
                )

    _check_primary_pairing(primary_items, cfg, warnings)

    # Same-song duplicate recording & original-vs-cover year checks across matched entries
    by_title_all: dict[str, list[dict[str, Any]]] = {}
    for it in matched:
        if id(it) not in tv_keys:
            by_title_all.setdefault(it.get("title", ""), []).append(it)

    for title, group in by_title_all.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            a = group[i]
            pa = norm_heb((a.get("selected_video") or {}).get("matched_performer", ""))
            da = parse_duration_seconds((a.get("selected_video") or {}).get("duration", ""))
            if not pa or da <= 0:
                continue
            for j in range(i + 1, len(group)):
                b = group[j]
                pb = norm_heb((b.get("selected_video") or {}).get("matched_performer", ""))
                db = parse_duration_seconds((b.get("selected_video") or {}).get("duration", ""))
                if pb == pa and db > 0 and abs(da - db) <= 12:
                    warnings.append(
                        _issue(
                            "POSSIBLE_DUPLICATE_RECORDING",
                            b.get("index"),
                            title,
                            b["selected_video"]["video_id"],
                            f"Matches #{a.get('index')} ({a['selected_video']['video_id']}): same performer '{(b.get('selected_video') or {}).get('matched_performer', '')}' & ~duration ({da}s vs {db}s)",
                        )
                    )

        other_years = [
            y
            for x in group
            if x.get("dual_role") != "original_performance"
            and not any(
                w in f"{(x.get('selected_video') or {}).get('matched_performer', '')} {(x.get('selected_video') or {}).get('video_title', '')}"
                for w in _NON_CLIP_SUBSTRINGS
            )
            for y in [_parse_year(x.get("recording_year") if "recording_year" in x else x.get("year"))]
            if y is not None
        ]
        if other_years:
            min_other_yr = min(other_years)
            for x in group:
                if x.get("dual_role") == "original_performance":
                    orig_yr = _parse_year(x.get("recording_year") if "recording_year" in x else x.get("year"))
                    if orig_yr is not None and orig_yr > min_other_yr:
                        warnings.append(
                            _issue(
                                "ORIGINAL_LATER_THAN_OTHER",
                                x.get("index"),
                                title,
                                x["selected_video"]["video_id"],
                                f"Original recording_year={orig_yr} > earliest other version year {min_other_yr}",
                            )
                        )

        prim0 = group[0]
        prim0_vid = (prim0.get("selected_video") or {}).get("video_id", "")
        if id(prim0) in primary_keys and prim0_vid:
            p0_yr = _parse_year(prim0.get("recording_year") if "recording_year" in prim0 else prim0.get("year"))
            p0_perf = (prim0.get("selected_video") or {}).get("matched_performer", "")
            earlier_others: list[tuple[int, dict[str, Any]]] = []
            for x in group[1:]:
                if any(
                    w in f"{(x.get('selected_video') or {}).get('matched_performer', '')} {(x.get('selected_video') or {}).get('video_title', '')}"
                    for w in _NON_CLIP_SUBSTRINGS
                ):
                    continue
                xy = _parse_year(x.get("recording_year") if "recording_year" in x else x.get("year"))
                if xy is not None and p0_yr is not None and xy < p0_yr:
                    earlier_others.append((xy, x))
            if (
                earlier_others
                and not _is_approved_iconic(title, prim0_vid)
                and not _is_allowed_exception("ORIGINAL_LATER_THAN_OTHER", prim0_vid)
            ):
                min_yr, min_x = min(earlier_others, key=lambda t: t[0])
                min_perf = (min_x.get("selected_video") or {}).get("matched_performer", "")
                warnings.append(
                    _issue(
                        "PRIMARY_NOT_EARLIEST",
                        prim0.get("index"),
                        title,
                        prim0_vid,
                        f"Primary ({p0_perf}, {p0_yr}) is later than #{min_x.get('index')} ({min_perf}, {min_yr})",
                    )
                )

            p0_src = str(prim0.get("year_source") or "").strip()
            if (
                prim0.get("tier") not in creator_tiers
                and p0_src in ("", "original_inherited", "unverified_inherited")
                and not _is_approved_iconic(title, prim0_vid)
            ):
                creator_albs = [
                    x
                    for x in group[1:]
                    if x.get("tier") in ("1_album_naomi", "1_album_creator")
                ]
                if creator_albs:
                    cr_x = creator_albs[0]
                    cr_yr = _parse_year(cr_x.get("recording_year") if "recording_year" in cr_x else cr_x.get("year"))
                    if p0_yr is None or (cr_yr is not None and cr_yr <= p0_yr + 1):
                        warnings.append(
                            _issue(
                                "UNVERIFIED_PRIMARY_BEFORE_CREATOR",
                                prim0.get("index"),
                                title,
                                prim0_vid,
                                f"Unverified primary ({p0_perf}, src='{p0_src or 'none'}') precedes creator album #{cr_x.get('index')} ({cr_yr})",
                            )
                        )

    for title, sy_set in song_years_seen.items():
        if len(sy_set) > 1 and title in matched_titles_with_videos:
            errors.append(
                _issue(
                    "INCONSISTENT_SONG_YEAR",
                    "",
                    title,
                    "",
                    f"Multiple distinct song_year values across entries: {sorted(sy_set)}",
                )
            )

    if cfg.playlist_data_js.exists():
        raw_js = cfg.playlist_data_js.read_text(encoding="utf-8")
        if raw_js.lstrip().startswith("window.PLAYLIST_DATA"):
            json_str = raw_js.split("=", 1)[1].strip().rstrip(";")
            pdata_js = json.loads(json_str)
            for row in list(pdata_js.get("songs") or []) + list(pdata_js.get("archiveSongs") or []):
                for lk in row.get("links") or []:
                    lbl = str(lk.get("label", ""))
                    if "ACUM_WRKNBR:" in lbl:
                        errors.append(
                            _issue(
                                "RAW_ACUM_LABEL_IN_EXPORT",
                                row.get("n"),
                                row.get("raw_title") or row.get("title", ""),
                                row.get("vid", ""),
                                f"Unstripped ACUM_WRKNBR prefix in label '{lbl}'",
                            )
                        )
                    url_val = str(lk.get("url", ""))
                    if "acumsitesearchdb/issearch" in url_val or "ACUM_WRKNBR:" in url_val:
                        errors.append(
                            _issue(
                                "BROKEN_ACUM_URL",
                                row.get("n"),
                                row.get("raw_title") or row.get("title", ""),
                                row.get("vid", ""),
                                f"Broken ACUM archive URL '{url_val}' (use /acumsitesearchdb/work?workid=<numeric_id>)",
                            )
                        )
                notes_val = str(row.get("notes") or "")
                if len(notes_val) > 220:
                    warnings.append(
                        _issue(
                            "LONG_NOTES_IN_EXPORT",
                            row.get("n"),
                            row.get("raw_title") or row.get("title", ""),
                            row.get("vid", ""),
                            f"Long notes paragraph ({len(notes_val)} chars) in public export",
                        )
                    )

    errors = [e for e in errors if not _is_allowed_exception(e["code"], e["video_id"])]
    warnings = [w for w in warnings if not _is_allowed_exception(w["code"], w["video_id"])]

    return {
        "slug": cfg.slug,
        "name_he": cfg.name_he,
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def format_qa_report(report: dict[str, Any], max_warnings: int = 30) -> str:
    """Format an audit report for readable CLI output."""
    lines = [
        f"QA Report [{report['slug']}] ({report['name_he']}): "
        f"{report['matched_count']} matched, {report['unmatched_count']} archive | "
        f"errors={report['error_count']} | warnings={report['warning_count']}"
    ]
    if report["errors"]:
        lines.append("  ERRORS:")
        for err in report["errors"]:
            lines.append(
                f"    [{err['code']}] #{err['index']} {err['title']} ({err['video_id']}): {err['detail']}"
            )
    if report["warnings"]:
        lines.append(f"  WARNINGS (showing {min(len(report['warnings']), max_warnings)}/{len(report['warnings'])}):")
        for warn in report["warnings"][:max_warnings]:
            lines.append(
                f"    [{warn['code']}] #{warn['index']} {warn['title']} ({warn['video_id']}): {warn['detail']}"
            )
    return "\n".join(lines)
