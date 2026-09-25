"""Testes do Google Dork Scanner."""
import json
from unittest.mock import MagicMock, patch

import dork_scanner_v3 as s


# --------------------------------------------------------------------------
# normalize_domain
# --------------------------------------------------------------------------
def test_normalize_strips_scheme_and_www():
    assert s.normalize_domain("https://www.exemplo.com/path") == "exemplo.com"


def test_normalize_keeps_subdomain():
    assert s.normalize_domain("app.exemplo.com.br") == "app.exemplo.com.br"


def test_normalize_rejects_invalid():
    assert s.normalize_domain("nao_e_dominio") is None
    assert s.normalize_domain("") is None


def test_normalize_does_not_eat_internal_www():
    # "www." só deve ser removido no início (bug antigo do replace global)
    assert s.normalize_domain("wwwexemplo.com") == "wwwexemplo.com"


# --------------------------------------------------------------------------
# mask_key
# --------------------------------------------------------------------------
def test_mask_key_reveals_only_last_four():
    masked = s.mask_key("abcdefghijklmnop1234")
    assert masked.endswith("1234")
    assert "abcdef" not in masked


# --------------------------------------------------------------------------
# database
# --------------------------------------------------------------------------
def test_database_has_no_duplicate_dorks():
    with open(s.DB_FILE, encoding="utf-8") as f:
        data = json.load(f)
    all_dorks = [d for c in data["dork_categories"].values() for d in c["dorks"]]
    assert len(all_dorks) == len(set(all_dorks)), "há dorks duplicadas"


def test_every_category_has_severity():
    with open(s.DB_FILE, encoding="utf-8") as f:
        data = json.load(f)
    for c in data["dork_categories"].values():
        assert c["severity"] in s.SEVERITY_ORDER


def test_load_categories_substitutes_domain():
    cats = s.load_categories("exemplo.com")
    assert cats
    assert all("{domain}" not in d for c in cats for d in c.dorks)
    assert any("exemplo.com" in d for c in cats for d in c.dorks)


# --------------------------------------------------------------------------
# search_serper — o bug principal: 'vazio' != 'erro'
# --------------------------------------------------------------------------
def _fake_conn(status, body):
    conn = MagicMock()
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = body.encode("utf-8")
    conn.getresponse.return_value = resp
    return conn


def test_search_found():
    body = json.dumps({"organic": [{"title": "t", "link": "http://x", "snippet": ""}]})
    with patch.object(s, "HTTPSConnection", return_value=_fake_conn(200, body)):
        r = s.search_serper("site:x inurl:admin", "key", "br", "pt")
    assert r.status is s.SearchStatus.FOUND
    assert len(r.urls) == 1


def test_search_empty_is_not_error():
    body = json.dumps({"organic": []})
    with patch.object(s, "HTTPSConnection", return_value=_fake_conn(200, body)):
        r = s.search_serper("site:x inurl:nada", "key", "br", "pt")
    assert r.status is s.SearchStatus.EMPTY  # antes virava ERRO


def test_search_quota_detected():
    with patch.object(s, "HTTPSConnection", return_value=_fake_conn(429, "rate limit")):
        r = s.search_serper("q", "key", "br", "pt")
    assert r.status is s.SearchStatus.QUOTA  # antes virava "sem resultados"


def test_search_network_error():
    with patch.object(s, "HTTPSConnection", side_effect=OSError("no net")):
        r = s.search_serper("q", "key", "br", "pt")
    assert r.status is s.SearchStatus.ERROR


# --------------------------------------------------------------------------
# summarize
# --------------------------------------------------------------------------
def test_summarize_counts_each_status():
    results = [
        s.DorkResult("c", "alto", "d1", s.SearchStatus.FOUND, urls=[{"link": "x"}]),
        s.DorkResult("c", "alto", "d2", s.SearchStatus.EMPTY),
        s.DorkResult("c", "alto", "d3", s.SearchStatus.ERROR),
        s.DorkResult("c", "alto", "d4", s.SearchStatus.QUOTA),
    ]
    summary = s.summarize(results)
    assert summary == {"total": 4, "found": 1, "empty": 1, "error": 1, "quota": 1}


# --------------------------------------------------------------------------
# save_report
# --------------------------------------------------------------------------
def test_save_report_json(tmp_path):
    results = [s.DorkResult("Cat", "critico", "site:x", s.SearchStatus.FOUND,
                            urls=[{"title": "T", "link": "http://x", "snippet": ""}])]
    path = tmp_path / "r.json"
    s.save_report(results, "exemplo.com", "json", str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["summary"]["found"] == 1
    assert data["findings"][0]["severity"] == "critico"


def test_save_report_csv_only_findings(tmp_path):
    results = [
        s.DorkResult("Cat", "alto", "d1", s.SearchStatus.FOUND,
                     urls=[{"title": "T", "link": "http://x", "snippet": ""}]),
        s.DorkResult("Cat", "alto", "d2", s.SearchStatus.EMPTY),
    ]
    path = tmp_path / "r.csv"
    s.save_report(results, "exemplo.com", "csv", str(path))
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # header + 1 achado (EMPTY não entra)
