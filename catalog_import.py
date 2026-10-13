"""Small, reversible catalog importer helpers for the admin CSV import."""
import html
import re
from urllib.parse import quote

KNOWN_GAMES = {
    "Free Fire": ("free fire", "فري فاير"), "PUBG": ("pubg", "ببجي"),
    "Roblox": ("roblox",), "Honkai": ("honkai",), "Genshin Impact": ("genshin", "جينشن", "jades"),
    "Valorant": ("valorant", "فالورانت"), "Mobile Legends": ("mobile legends", "موبايل ليجند"),
    "NIKKE": ("nikke",), "ZEPETO": ("zepeto",), "Blood Strike": ("blood strike", "بلود سترايك"),
    "Honor of Kings": ("honor of kings",), "Minecraft": ("minecraft",),
    "Steam": ("steam",), "PlayStation": ("playstation", "بلاي ستيشن"), "Xbox": ("xbox",),
}
SOCIAL = ("instagram", "tiktok", "telegram", "whatsapp", "youtube", "facebook", "snapchat", "twitter", "wechat", "لايك", "متابع", "مشاهد", "تفاعل", "followers", "views", "likes", "رواتب")
SUBSCRIPTIONS = ("netflix", "spotify", "shahid", "شاهد", "prime video", "youtube premium", "chatgpt", "canva", "adobe", "gemini", "جيمني", "vpn", "iptv", "discord", "كاسبرسكي", "كرانشي", "نورد", "سيرف شارك", "اشتراك", "عضوية")
CARDS = ("voucher", "gift card", "بطاقة", "كود", "قسيمة", "itunes", "google play", "visa", "mastercard", "فيزا", "امازون", "ريزر", "shamcash")
ACCOUNTS = ("حساب", "account", "gmail", "email", "icloud", "رقم", "number", "ايميل")
VIRTUAL = ("diamond", "جوهرة", "gems", "gem", "gold", "ذهب", "coins", "coin", "عملة", "crystal", "كرستال", "بلورة", "points", "نقاط", "pass", "card", "pack", "bundle", "ticket", "tickets", "shard", "credits", "cash", "tokens", "token", "jade", "ingots", "premium", "battle", "coupon", "كوبونات", "opal", "platinum", "silver", "wild cores", "monochrome", "quartz", "chips")

def _branch(name):
    cleaned = re.sub(r"[\d$€£()+\-_/|]+", " ", name)
    words = [w for w in re.sub(r"\s+", " ", cleaned).strip(" .").split()
             if w.lower() not in {"the", "a", "an", "of", "and", "with", "bonus", "global", "pack", "bundle", "card", "pass", "monthly", "weekly", "premium", "basic", "special", "value", "days", "day", "شهر", "اشهر", "يوم", "أيام", "باقة", "حزمة", "جوهرة", "ذهب", "عملة", "نقاط", "كود"}]
    return " ".join(words[:3])[:48] or "منتجات تحتاج مراجعة"

def classify(name):
    n = name.lower()
    for branch, terms in KNOWN_GAMES.items():
        if any(term in n for term in terms):
            return "ألعاب وشحن", branch
    if any(term in n for term in SOCIAL): return "خدمات التواصل الاجتماعي", "خدمات السوشال ميديا"
    if any(term in n for term in ACCOUNTS): return "الحسابات والأرقام", "حسابات وخدمات يدوية"
    if any(term in n for term in SUBSCRIPTIONS): return "الاشتراكات والخدمات الرقمية", "الاشتراكات الرقمية"
    if any(term in n for term in CARDS): return "البطاقات والقسائم", "البطاقات والشحن"
    if any(term in n for term in VIRTUAL): return "ألعاب وشحن", _branch(name)
    return "المزيد من المنتجات", "منتجات تحتاج مراجعة"

def branded_image(name, kind="product"):
    safe = html.escape(name[:42], quote=True)
    label = {"section": "ARAB STORE", "subsection": "ARAB STORE", "product": "ARAB STORE"}.get(kind, "ARAB STORE")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#0b0f19"/><stop offset=".55" stop-color="#251326"/><stop offset="1" stop-color="#780d27"/></linearGradient></defs><rect width="800" height="500" rx="28" fill="url(#g)"/><circle cx="650" cy="160" r="150" fill="#ff1a3c" opacity=".16"/><circle cx="650" cy="160" r="95" fill="none" stroke="#ffc24b" stroke-width="3" opacity=".5"/><text x="55" y="90" fill="#ffc24b" font-family="Arial,sans-serif" font-size="22" font-weight="700" letter-spacing="4">{label}</text><text x="55" y="290" fill="#fff" font-family="Arial,sans-serif" font-size="42" font-weight="900">{safe}</text><text x="55" y="345" fill="#f3f6fa" opacity=".75" font-family="Arial,sans-serif" font-size="20">خدمة أصلية • تنفيذ سريع • ضمان كامل</text><text x="650" y="175" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="31" font-weight="900">ARAB</text><text x="650" y="214" text-anchor="middle" fill="#ffc24b" font-family="Arial,sans-serif" font-size="25" font-weight="900" letter-spacing="4">STORE</text></svg>'''
    return "data:image/svg+xml;charset=UTF-8," + quote(svg)
