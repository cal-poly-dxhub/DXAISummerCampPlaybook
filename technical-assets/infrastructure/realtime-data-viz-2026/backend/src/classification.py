"""
Deterministic classification for institution (from email domain) and major category.
No LLM calls — pure lookup tables and keyword matching.
"""

# CSU email domains -> institution names
# Source: resume_reviewer/utils/university_mapping.py
CSU_DOMAIN_MAP = {
    "csub.edu": "CSU Bakersfield",
    "caub.edu": "CSU Bakersfield",
    "csuci.edu": "CSU Channel Islands",
    "myci.csuci.edu": "CSU Channel Islands",
    "csuchico.edu": "CSU Chico",
    "csudh.edu": "CSU Dominguez Hills",
    "toromail.csudh.edu": "CSU Dominguez Hills",
    "csueastbay.edu": "CSU East Bay",
    "fresnostate.edu": "CSU Fresno",
    "mail.fresnostate.edu": "CSU Fresno",
    "mail.fresnostate.com": "CSU Fresno",
    "fresno.state.edu": "CSU Fresno",
    "mail.fresno.state.edu": "CSU Fresno",
    "csu.fullerton.edu": "CSU Fullerton",
    "fullerton.edu": "CSU Fullerton",
    "humboldt.edu": "Cal Poly Humboldt",
    "student.csulb.edu": "CSU Long Beach",
    "csulb.edu": "CSU Long Beach",
    "calstatela.edu": "CSU Los Angeles",
    "csum.edu": "CSU Maritime Academy",
    "csumb.edu": "CSU Monterey Bay",
    "my.csun.edu": "CSU Northridge",
    "csun.edu": "CSU Northridge",
    "cpp.edu": "Cal Poly Pomona",
    "hornet.csus.edu": "CSU Sacramento",
    "csus.edu": "CSU Sacramento",
    "coyote.csusb.edu": "CSU San Bernardino",
    "csusb.edu": "CSU San Bernardino",
    "sdsu.edu": "San Diego State",
    "mail.sfsu.edu": "San Francisco State",
    "sfsu.edu": "San Francisco State",
    "sjsu.edu": "San Jose State",
    "calpoly.edu": "Cal Poly SLO",
    "csusm.edu": "CSU San Marcos",
    "sonoma.edu": "Sonoma State",
    "csustan.edu": "CSU Stanislaus",
}

# CCC email domains -> institution codes
# Source: cccAIsummercamp/realtime_updates.py
CCC_DOMAIN_MAP = {
    "hancockcollege.edu": "Hancock",
    "losrios.edu": "Los Rios",
    "avc.edu": "Antelope Valley",
    "bakersfieldcollege.edu": "Bakersfield College",
    "barstow.edu": "Barstow",
    "peralta.edu": "Peralta",
    "butte.edu": "Butte",
    "cabrillo.edu": "Cabrillo",
    "calbright.org": "Calbright",
    "smccd.edu": "San Mateo CCD",
    "cerritos.edu": "Cerritos",
    "cerrocoso.edu": "Cerro Coso",
    "chabotcollege.edu": "Chabot",
    "chaffey.edu": "Chaffey",
    "citruscollege.edu": "Citrus",
    "ccsf.edu": "City College SF",
    "scccd.edu": "State Center CCD",
    "coastline.edu": "Coastline",
    "marin.edu": "College of Marin",
    "canyons.edu": "College of the Canyons",
    "collegeofthedesert.edu": "College of the Desert",
    "redwoods.edu": "College of the Redwoods",
    "cos.edu": "College of the Sequoias",
    "siskiyous.edu": "College of the Siskiyous",
    "yosemite.edu": "Yosemite CCD",
    "compton.edu": "Compton",
    "4cd.edu": "Contra Costa CCD",
    "cmccd.edu": "Copper Mountain",
    "craftonhills.edu": "Crafton Hills",
    "cuesta.edu": "Cuesta",
    "gcccd.edu": "Grossmont-Cuyamaca",
    "nocccd.edu": "North Orange CCD",
    "deanza.edu": "De Anza",
    "laccd.edu": "LA CCD",
    "elcamino.edu": "El Camino",
    "evc.edu": "Evergreen Valley",
    "frc.edu": "Feather River",
    "foothill.edu": "Foothill",
    "gavilan.edu": "Gavilan",
    "glendale.edu": "Glendale",
    "gwc.cccd.edu": "Golden West",
    "hartnell.edu": "Hartnell",
    "imperial.edu": "Imperial Valley",
    "ivc.edu": "Irvine Valley",
    "ltcc.edu": "Lake Tahoe",
    "laspositascollege.edu": "Las Positas",
    "lassencollege.edu": "Lassen",
    "lbcc.edu": "Long Beach City",
    "mendocino.edu": "Mendocino",
    "mccd.edu": "Merced CCD",
    "miracosta.edu": "MiraCosta",
    "missioncollege.edu": "Mission",
    "mpc.edu": "Monterey Peninsula",
    "vcccd.edu": "Ventura CCD",
    "rcc.edu": "Riverside City",
    "mtsac.edu": "Mt. SAC",
    "msjc.edu": "Mt. San Jacinto",
    "napavalley.edu": "Napa Valley",
    "ohlone.edu": "Ohlone",
    "occ.cccd.edu": "Orange Coast",
    "paloverde.edu": "Palo Verde",
    "palomar.edu": "Palomar",
    "pasadena.edu": "Pasadena City",
    "portervillecollege.edu": "Porterville",
    "riohondo.edu": "Rio Hondo",
    "saddleback.edu": "Saddleback",
    "valleycollege.edu": "San Bernardino Valley",
    "sdccd.edu": "San Diego CCD",
    "deltacollege.edu": "San Joaquin Delta",
    "sjcc.edu": "San Jose City",
    "sac.edu": "Sacramento City",
    "sbcc.edu": "Santa Barbara City",
    "smc.edu": "Santa Monica",
    "santarosa.edu": "Santa Rosa JC",
    "sccollege.edu": "Santiago Canyon",
    "shastacollege.edu": "Shasta",
    "sierracollege.edu": "Sierra",
    "solano.edu": "Solano",
    "swccd.edu": "Southwestern",
    "taftcollege.edu": "Taft",
    "vvc.edu": "Victor Valley",
    "westhillscollege.com": "West Hills",
    "westvalley.edu": "West Valley",
    "yccd.edu": "Yuba CCD",
}


def extract_domain(email):
    """Extract domain from email address."""
    if not email or "@" not in email:
        return ""
    return email.split("@")[-1].lower().strip()


def classify_institution(email, org, form_institution=""):
    """
    Classify applicant institution from email domain.

    For CSU: use email domain lookup.
    For CCC: use email domain lookup, fall back to form-provided institution.
    """
    domain = extract_domain(email)
    if not domain:
        return form_institution or "Unknown"

    if org == "csu":
        return CSU_DOMAIN_MAP.get(domain, f"Other ({domain})")

    if org == "ccc":
        result = CCC_DOMAIN_MAP.get(domain)
        if result:
            return result
        # CCC students may use personal emails — fall back to form field
        return form_institution or f"Other ({domain})"

    return f"Other ({domain})"


# Major category classification via keyword matching
MAJOR_KEYWORDS = {
    "STEM": [
        "computer science", "computerscience", "comp sci", "compsci", "cs",
        "software engineering", "softwareengineering",
        "computer engineering", "computerengineering",
        "information technology", "information systems", "cybersecurity",
        "data science", "datascience",
        "artificial intelligence", "machine learning",
        "computer information",
        "engineering", "mechanical", "electrical", "civil", "aerospace",
        "biomedical engineering", "chemical engineering", "industrial engineering",
        "mathematics", "math", "physics", "chemistry", "biology",
        "statistics", "biochemistry", "environmental science", "geology",
        "science", "technology",
    ],
    "Business & Economics": [
        "business", "finance", "accounting", "economics", "marketing",
        "management", "entrepreneurship", "mba",
    ],
    "Social Sciences": [
        "psychology", "sociology", "political science", "anthropology",
        "criminal justice", "social work", "international relations",
    ],
    "Arts & Humanities": [
        "art", "music", "english", "history", "philosophy", "theater",
        "film", "design", "creative writing", "communications", "journalism",
        "linguistics", "literature",
    ],
    "Health & Human Services": [
        "nursing", "health", "kinesiology", "nutrition", "public health",
        "pre-med", "pre-nursing", "pharmacy",
    ],
    "Education": [
        "education", "teaching", "child development", "early childhood",
    ],
}

# Subset of STEM keywords that count as "computing majors"
COMPUTING_KEYWORDS = [
    "computer science", "computerscience", "comp sci", "compsci", "cs",
    "software engineering", "softwareengineering",
    "computer engineering", "computerengineering",
    "information technology", "information systems", "cybersecurity",
    "data science", "datascience",
    "artificial intelligence", "machine learning",
    "computer information",
]


def _normalize_major(s):
    """Normalize major string for matching: strip degree prefixes, lowercase."""
    import re
    s = s.lower().strip()
    # Strip common degree prefixes like "B.S.", "B.A.", "M.S.", "Bachelor of", etc.
    s = re.sub(r"^(b\.?s\.?|b\.?a\.?|m\.?s\.?|m\.?a\.?|a\.?s\.?|a\.?a\.?)\s*[,.\-:in ]*\s*", "", s)
    s = re.sub(r"^(bachelor|master|associate)s?\s*(of\s*(science|arts|applied\s*science))?\s*[,.\-:in ]*\s*", "", s)
    return s.strip()


def _keyword_match(kw, normalized, no_spaces):
    """Match a keyword, using word boundaries for short ambiguous keywords."""
    import re
    # Only use word boundary for "cs" which false-matches mathematics, physics, etc.
    if kw == "cs":
        return bool(re.search(r'\bcs\b', normalized))
    return kw in normalized or kw.replace(" ", "") in no_spaces


def classify_major(major_string):
    """
    Classify academic major into a top-level category using keyword matching.
    Returns (major_category, is_computing_major).
    """
    if not major_string:
        return "Other", False

    normalized = _normalize_major(major_string)
    no_spaces = normalized.replace(" ", "")

    # Check if it's a computing major
    is_computing = any(
        _keyword_match(kw, normalized, no_spaces)
        for kw in COMPUTING_KEYWORDS
    )

    for category, keywords in MAJOR_KEYWORDS.items():
        for kw in keywords:
            if _keyword_match(kw, normalized, no_spaces):
                return category, is_computing

    return "Other", False
