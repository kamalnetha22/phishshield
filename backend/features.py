import re
from urllib.parse import urlparse

URGENCY_WORDS = ["urgent", "verify", "suspend", "account", "confirm", "update",
                 "click", "immediately", "expire", "limited", "act now", "winner",
                 "prize", "free", "offer", "login", "password", "security"]

TRUSTED_DOMAINS = ["paypal.com", "amazon.com", "apple.com", "google.com",
                   "microsoft.com", "facebook.com", "netflix.com", "bank"]

def extract_url_features(url: str) -> dict:
    try:
        parsed = urlparse(url if url.startswith("http") else "http://" + url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        full = url.lower()
    except Exception:
        parsed = urlparse("http://unknown")
        domain, path, full = "", "", url.lower()

    ip_pattern = re.compile(r'\d{1,3}(\.\d{1,3}){3}')
    has_ip = 1 if ip_pattern.search(domain) else 0
    url_length = len(url)
    domain_length = len(domain)
    num_dots = domain.count(".")
    num_hyphens = domain.count("-")
    num_subdomains = max(0, domain.count(".") - 1)
    has_https = 1 if url.startswith("https") else 0
    has_at = 1 if "@" in url else 0
    has_double_slash = 1 if "//" in url[7:] else 0
    path_length = len(path)
    num_params = len(parsed.query.split("&")) if parsed.query else 0
    has_suspicious_tld = 1 if any(domain.endswith(t) for t in [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top"]) else 0
    has_brand_in_subdomain = 0
    for brand in [d.split(".")[0] for d in TRUSTED_DOMAINS]:
        subdomain_part = domain.replace(parsed.hostname or "", "") if parsed.hostname else ""
        if brand in subdomain_part:
            has_brand_in_subdomain = 1
            break
    has_port = 1 if parsed.port and parsed.port not in (80, 443) else 0
    num_digits_in_domain = sum(c.isdigit() for c in domain)
    special_char_count = sum(1 for c in url if c in "!$%^*()+=[]{}|;':\"<>?,~`")
    has_login_keyword = 1 if any(w in full for w in ["login", "signin", "verify", "secure", "account", "update", "confirm"]) else 0
    url_entropy = len(set(url)) / max(len(url), 1)

    return {
        "url_length": url_length,
        "domain_length": domain_length,
        "num_dots": num_dots,
        "num_hyphens": num_hyphens,
        "num_subdomains": num_subdomains,
        "has_https": has_https,
        "has_at_symbol": has_at,
        "has_double_slash": has_double_slash,
        "path_length": path_length,
        "num_params": num_params,
        "has_suspicious_tld": has_suspicious_tld,
        "has_brand_in_subdomain": has_brand_in_subdomain,
        "has_ip_address": has_ip,
        "has_port": has_port,
        "num_digits_in_domain": num_digits_in_domain,
        "special_char_count": special_char_count,
        "has_login_keyword": has_login_keyword,
        "url_entropy": round(url_entropy, 4),
    }


def extract_email_features(subject: str, body: str, sender: str = "") -> dict:
    text = (subject + " " + body).lower()
    words = re.findall(r'\w+', text)
    sender_domain = sender.split("@")[-1].lower() if "@" in sender else ""

    urgency_score = sum(1 for w in URGENCY_WORDS if w in text)
    domain_mismatch = 0
    if sender_domain:
        trusted = [d.split(".")[0] for d in TRUSTED_DOMAINS]
        for brand in trusted:
            if brand in text and brand not in sender_domain:
                domain_mismatch = 1
                break

    has_url = 1 if re.search(r"http[s]?://", body) else 0
    url_count = len(re.findall(r"http[s]?://\S+", body))
    has_html = 1 if re.search(r"<[a-z][\s\S]*>", body, re.IGNORECASE) else 0
    exclamation_count = body.count("!")
    caps_ratio = sum(1 for c in body if c.isupper()) / max(len(body), 1)
    word_count = len(words)
    avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
    has_attachment_mention = 1 if any(w in text for w in ["attachment", "attached", "invoice", "document", "pdf"]) else 0
    greeting_generic = 1 if any(g in text for g in ["dear customer", "dear user", "dear account", "valued customer"]) else 0

    return {
        "subject_length": len(subject),
        "body_length": len(body),
        "urgency_score": urgency_score,
        "domain_mismatch": domain_mismatch,
        "has_url": has_url,
        "url_count": url_count,
        "has_html_tags": has_html,
        "exclamation_count": exclamation_count,
        "caps_ratio": round(caps_ratio, 4),
        "word_count": word_count,
        "avg_word_length": round(avg_word_length, 4),
        "has_attachment_mention": has_attachment_mention,
        "generic_greeting": greeting_generic,
        "sender_domain_length": len(sender_domain),
        "has_free_keyword": 1 if "free" in text else 0,
        "has_prize_keyword": 1 if any(w in text for w in ["winner", "prize", "won", "lottery", "congratulations"]) else 0,
        "question_mark_count": body.count("?"),
    }
