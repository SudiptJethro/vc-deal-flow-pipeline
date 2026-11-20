"""
Deal Flow Pipeline - Configuration
All shared constants, keywords, and settings.
"""

# ---- Target sectors ----
SECTORS = ["Consumer AI", "Consumer Tech", "HealthTech"]

SECTOR_KEYWORDS = {
    "Consumer AI": [
        "ai", "artificial intelligence", "machine learning", "llm", "generative ai",
        "genai", "chatbot", "nlp", "computer vision", "voice ai", "conversational ai",
        "ai agent", "copilot", "recommendation", "personalization", "deep learning",
        "vernacular ai", "language model", "agentic"
    ],
    "Consumer Tech": [
        "consumer", "d2c", "marketplace", "ecommerce", "e-commerce", "fintech",
        "edtech", "social", "gaming", "travel", "food", "logistics", "delivery",
        "mobility", "payments", "neobank", "creator", "content", "entertainment",
        "fashion", "beauty", "retail", "saas for consumers", "subscription"
    ],
    "HealthTech": [
        "health", "healthcare", "medtech", "biotech", "telemedicine", "mental health",
        "wellness", "fitness", "diagnostics", "femtech", "fertility", "eldercare",
        "elder care", "pharma", "clinical", "patient", "doctor", "hospital",
        "therapy", "nutrition", "dental", "radiology", "oncology"
    ]
}

# ---- Excluded startups ----
# Startups already in your own pipeline. Anything listed here is skipped by the
# enricher. Left empty in the public repo; add your own names locally.
EXCLUDED_STARTUPS: list[str] = []

# ---- Top Indian startups whose ex-employees we track ----
MAFIA_COMPANIES = [
    # Original unicorns
    "Swiggy", "Zomato", "CRED", "Razorpay", "Groww", "PhonePe",
    "Juspay", "Udaan", "Dunzo", "Urban Company", "Curefit", "Nykaa",
    "Mamaearth", "Flipkart", "Ola", "Paytm", "Byju's", "Meesho",
    "Zepto", "ShareChat", "Dream11", "Unacademy", "Lenskart",

    # Fintech & Payments
    "BharatPe", "Slice", "Jupiter", "Jar", "Fi Money", "Niyo",
    "Cashfree", "Juspay", "Open", "Khatabook", "OkCredit",
    "Smallcase", "Zerodha", "Upstox", "INDmoney", "Scripbox",

    # SaaS & B2B Tech
    "Freshworks", "Zoho", "Browserstack", "Druva", "Postman",
    "Chargebee", "Clevertap", "MoEngage", "Exotel", "Eka Software",
    "Darwinbox", "Leadsquared", "Capillary Technologies",

    # Consumer & D2C
    "Boat", "Noise", "Wakefit", "Sleepycat", "Atomberg",
    "mCaffeine", "WOW Skin Science", "Bombay Shaving Company",
    "Sugar Cosmetics", "Plum Goodness", "The Whole Truth",

    # Logistics & Commerce
    "Delhivery", "Porter", "Shiprocket", "Shadowfax", "Loadshare",
    "CARS24", "Spinny", "Droom", "Fashinza", "Moglix", "Zetwerk",

    # EdTech
    "Vedantu", "Toppr", "UpGrad", "Eruditus", "Classplus",
    "Scaler", "Physics Wallah", "Leverage Edu",

    # HealthTech
    "Practo", "1mg", "PharmEasy", "Healthkart", "Pristyn Care",
    "Cure.fit", "Mfine", "Innovaccer", "Portea",

    # Deep Tech & AI
    "Sarvam AI", "Krutrim", "Mad Street Den", "Haptik",
    "Uniphore", "Vernacular.ai", "Gupshup", "Yellow.ai",

    # Gaming & Entertainment
    "Games24x7", "Nazara Technologies", "WinZO", "MPL",
    "Stage", "Kuku FM", "Pocket FM",
]

# ---- Premier institutions ----
PREMIER_INSTITUTIONS = [
    # ── Engineering (Top 20 India) ──
    "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kanpur", "IIT Kharagpur",
    "IIT Roorkee", "IIT Guwahati", "IIT Hyderabad", "IIT BHU",
    "IIT Indore", "IIT Gandhinagar", "IIT Jodhpur", "IIT Mandi",
    "IISc Bangalore",
    "BITS Pilani", "BITS Goa", "BITS Hyderabad",
    "NIT Trichy", "NIT Warangal", "NIT Surathkal",
    "IIIT Hyderabad", "IIIT Delhi", "IIIT Bangalore",
    "VIT Vellore", "Jadavpur University", "DTU Delhi", "Thapar University",

    # ── Business / Management (Top 20 India) ──
    "IIM Ahmedabad", "IIM Bangalore", "IIM Calcutta", "IIM Lucknow",
    "IIM Kozhikode", "IIM Indore", "IIM Shillong", "IIM Trichy", "IIM Udaipur",
    "ISB Hyderabad", "ISB Mohali",
    "XLRI Jamshedpur", "MDI Gurgaon", "SPJIMR Mumbai", "FMS Delhi",
    "IIFT Delhi", "NITIE Mumbai", "TISS Mumbai",
    "Great Lakes Chennai", "Symbiosis SCMHRD Pune",

    # ── Arts, Design & Architecture (Top 20 India) ──
    "NID Ahmedabad", "NID Bangalore", "NID Mumbai",
    "NIFT Delhi", "NIFT Mumbai", "NIFT Chennai",
    "Srishti Institute Bangalore",
    "MIT Institute of Design Pune", "Pearl Academy Delhi",
    "Symbiosis Institute of Design Pune",
    "CEPT Ahmedabad",
    "School of Planning and Architecture Delhi",
    "Sir JJ School of Art Mumbai", "Delhi College of Art",
    "MS University Baroda", "Visva-Bharati Shantiniketan",
    "Rachana Sansad Mumbai", "College of Art New Delhi",
    "Jamia Millia Islamia", "Amity School of Fine Arts",

    # ── Pure Sciences (Top 20 India) ──
    "TIFR Mumbai", "IISER Pune", "IISER Kolkata", "IISER Mohali",
    "IISER Bhopal", "IISER Thiruvananthapuram", "IISER Tirupati",
    "JNU Delhi", "Delhi University", "Hyderabad University",
    "Banaras Hindu University", "Aligarh Muslim University",
    "Calcutta University", "Madras University", "Bombay University",
    "Savitribai Phule Pune University", "Amrita Vishwa Vidyapeetham",
    "Manipal Academy of Higher Education",
    "Christ University Bangalore", "Presidency University Kolkata",

    # ── Medicine / Healthcare (Top 20 India) ──
    "AIIMS Delhi", "AIIMS Bhopal", "AIIMS Jodhpur",
    "AIIMS Rishikesh", "AIIMS Patna", "AIIMS Bhubaneswar",
    "CMC Vellore", "PGIMER Chandigarh", "JIPMER Puducherry",
    "NIMHANS Bangalore",
    "Kasturba Medical College Manipal",
    "Maulana Azad Medical College Delhi",
    "Grant Medical College Mumbai", "KEM Hospital Mumbai",
    "Bangalore Medical College",
    "Seth GS Medical College Mumbai", "Madras Medical College",
    "Armed Forces Medical College Pune",
    "Amrita School of Medicine", "St Johns Medical College Bangalore",

    # ── Global Top Institutions ──
    "Stanford", "MIT", "Harvard", "Carnegie Mellon", "Caltech",
    "UC Berkeley", "Columbia", "Oxford", "Cambridge", "Wharton",
    "Imperial College London", "ETH Zurich", "NUS Singapore",
]

# ---- Top companies for Tier 1 classification ----
TOP_COMPANIES = [
    "Google", "Meta", "Facebook", "Amazon", "Microsoft", "Apple",
    "McKinsey", "BCG", "Bain", "Goldman Sachs", "Morgan Stanley",
    "Flipkart", "Swiggy", "Zomato", "Razorpay", "PhonePe", "CRED",
    "Uber", "Stripe", "Airbnb", "Netflix", "Tesla", "OpenAI",
    "DeepMind", "Salesforce", "LinkedIn", "Twitter", "ByteDance"
]

# ---- Accelerator portfolio URLs (for scraping) ----
ACCELERATOR_URLS = {
    "Antler India": "https://www.antler.co/location/india",
    "YC India": "https://www.ycombinator.com/companies?regions=South+Asia",
    "SURGE (Peak XV)": "https://surge.peakxv.com/startups/",
    "100X.VC": "https://www.100x.vc/portfolio",
    "Techstars India": "https://www.techstars.com/portfolio?countries=India",
    "GSF India": "https://gsf.in/portfolio",
    "500 Startups India": "https://500.co/companies?country=India",
    "Plug and Play India": "https://www.plugandplaytechcenter.com/portfolio",
    "IIM NASSCOM Mentorship": "https://nasscom.in/startups",
}

# ---- Indian Directory & High-Signal Source URLs ----
DIRECTORY_URLS = {
    "Inc42": "https://inc42.com",
    "YourStory": "https://yourstory.com",
    "Wellfound (AngelList India)": "https://wellfound.com/companies?locations=India",
    "Startup India Hub": "https://www.startupindia.gov.in",
    "Nasscom Startup Members": "https://nasscom.in/startups",
    "IAMAI Members": "https://iamai.in/membership",
    "Hacker News": "https://news.ycombinator.com",
    "AngelList Syndicates": "https://angel.co/syndicates",
    "Gust": "https://gust.com",
    "SeedInvest": "https://www.seedinvest.com",
    "CB Insights": "https://www.cbinsights.com/research/india",
}

# ---- VC Portfolio URLs (India-focused) ----
VC_PORTFOLIO_URLS = {
    "Peak XV (Sequoia India)": "https://www.peakxv.com/portfolio",
    "Lightspeed India": "https://lsvp.com/portfolio",
    "Matrix Partners India": "https://www.matrixpartners.in/portfolio",
    "Accel India": "https://www.accel.com/portfolio",
    "Blume Ventures": "https://blume.vc/portfolio",
    "Nexus VP": "https://www.nexusvp.com/portfolio",
    "Kalaari Capital": "https://www.kalaari.com/portfolio",
    "Stellaris VP": "https://www.stellaris.in/portfolio",
    "Chiratae": "https://www.chiratae.com/portfolio",
    "3one4 Capital": "https://www.3one4.com/portfolio",
    "Andreessen Horowitz (a16z)": "https://a16z.com/portfolio",
}

# ---- Google dork templates ----
GOOGLE_DORK_TEMPLATES = {
    # No site:linkedin.com/in - LinkedIn de-indexes most profiles so that
    # operator returns nothing.  'linkedin' keyword biases results toward profiles.
    "linkedin_founder": '"{company}" founder India linkedin',
    "linkedin_building": '"building" "{sector}" India startup 2024 linkedin',
    "linkedin_ex_employee": '"ex-{company}" OR "previously {company}" founder startup India linkedin',
    "twitter_building": '"building" "startup" India "{sector}" 2024 twitter OR x.com',
    "producthunt_india": 'site:producthunt.com "India" "{sector}" 2024',
    "iit_founder": '"{institution}" alumni founder startup India linkedin 2024',
}

# ---- Rate limiting ----
REQUEST_DELAY_SECONDS = 2
MAX_RETRIES = 3

# ---- Output ----
OUTPUT_DIR = "../data"
OUTPUT_FILE = "startups.json"
