// ============================================
// Deal Flow Pipeline - Config (ported from Python)
// ============================================

export const SECTORS = ['Consumer AI', 'Consumer Tech', 'HealthTech'] as const;

export const SECTOR_KEYWORDS: Record<string, string[]> = {
  'Consumer AI': [
    'ai', 'artificial intelligence', 'machine learning', 'llm', 'generative ai',
    'genai', 'chatbot', 'nlp', 'computer vision', 'voice ai', 'conversational ai',
    'ai agent', 'copilot', 'recommendation', 'personalization', 'deep learning',
    'vernacular ai', 'language model', 'agentic',
  ],
  'Consumer Tech': [
    'consumer', 'd2c', 'marketplace', 'ecommerce', 'e-commerce', 'fintech',
    'edtech', 'social', 'gaming', 'travel', 'food', 'logistics', 'delivery',
    'mobility', 'payments', 'neobank', 'creator', 'content', 'entertainment',
    'fashion', 'beauty', 'retail', 'saas for consumers', 'subscription',
  ],
  'HealthTech': [
    'health', 'healthcare', 'medtech', 'biotech', 'telemedicine', 'mental health',
    'wellness', 'fitness', 'diagnostics', 'femtech', 'fertility', 'eldercare',
    'elder care', 'pharma', 'clinical', 'patient', 'doctor', 'hospital',
    'therapy', 'nutrition', 'dental', 'radiology', 'oncology',
  ],
};

export const MAFIA_COMPANIES = [
  // Original unicorns
  'Swiggy', 'Zomato', 'CRED', 'Razorpay', 'Groww', 'PhonePe',
  'Juspay', 'Udaan', 'Dunzo', 'Urban Company', 'Curefit', 'Nykaa',
  'Mamaearth', 'Flipkart', 'Ola', 'Paytm', "Byju's", 'Meesho',
  'Zepto', 'ShareChat', 'Dream11', 'Unacademy', 'Lenskart',

  // Fintech & Payments
  'BharatPe', 'Slice', 'Jupiter', 'Jar', 'Fi Money', 'Niyo',
  'Cashfree', 'Open', 'Khatabook', 'OkCredit',
  'Smallcase', 'Zerodha', 'Upstox', 'INDmoney', 'Scripbox',

  // SaaS & B2B Tech
  'Freshworks', 'Zoho', 'Browserstack', 'Druva', 'Postman',
  'Chargebee', 'Clevertap', 'MoEngage', 'Exotel',
  'Darwinbox', 'Leadsquared', 'Capillary Technologies',

  // Consumer & D2C
  'Boat', 'Noise', 'Wakefit', 'Sleepycat', 'Atomberg',
  'mCaffeine', 'WOW Skin Science', 'Bombay Shaving Company',
  'Sugar Cosmetics', 'Plum Goodness', 'The Whole Truth',

  // Logistics & Commerce
  'Delhivery', 'Porter', 'Shiprocket', 'Shadowfax', 'Loadshare',
  'CARS24', 'Spinny', 'Droom', 'Fashinza', 'Moglix', 'Zetwerk',

  // EdTech
  'Vedantu', 'Toppr', 'UpGrad', 'Eruditus', 'Classplus',
  'Scaler', 'Physics Wallah', 'Leverage Edu',

  // HealthTech
  'Practo', '1mg', 'PharmEasy', 'Healthkart', 'Pristyn Care',
  'Mfine', 'Innovaccer', 'Portea',

  // Deep Tech & AI
  'Sarvam AI', 'Krutrim', 'Mad Street Den', 'Haptik',
  'Uniphore', 'Gupshup', 'Yellow.ai',

  // Gaming & Entertainment
  'Games24x7', 'Nazara Technologies', 'WinZO', 'MPL',
  'Stage', 'Kuku FM', 'Pocket FM',
];

export const PREMIER_INSTITUTIONS = [
  // ── Engineering (Top 20 India) ──
  'IIT Bombay', 'IIT Delhi', 'IIT Madras', 'IIT Kanpur', 'IIT Kharagpur',
  'IIT Roorkee', 'IIT Guwahati', 'IIT Hyderabad', 'IIT BHU',
  'IIT Indore', 'IIT Gandhinagar', 'IIT Jodhpur', 'IIT Mandi',
  'IISc Bangalore',
  'BITS Pilani', 'BITS Goa', 'BITS Hyderabad',
  'NIT Trichy', 'NIT Warangal', 'NIT Surathkal',
  'IIIT Hyderabad', 'IIIT Delhi', 'IIIT Bangalore',
  'VIT Vellore', 'Jadavpur University', 'DTU Delhi', 'Thapar University',

  // ── Business / Management (Top 20 India) ──
  'IIM Ahmedabad', 'IIM Bangalore', 'IIM Calcutta', 'IIM Lucknow',
  'IIM Kozhikode', 'IIM Indore', 'IIM Shillong', 'IIM Trichy', 'IIM Udaipur',
  'ISB Hyderabad', 'ISB Mohali',
  'XLRI Jamshedpur', 'MDI Gurgaon', 'SPJIMR Mumbai', 'FMS Delhi',
  'IIFT Delhi', 'NITIE Mumbai', 'TISS Mumbai',
  'Great Lakes Chennai', 'Symbiosis SCMHRD Pune',

  // ── Arts, Design & Architecture (Top 20 India) ──
  'NID Ahmedabad', 'NID Bangalore', 'NID Mumbai',
  'NIFT Delhi', 'NIFT Mumbai', 'NIFT Chennai',
  'Srishti Institute Bangalore',
  'MIT Institute of Design Pune', 'Pearl Academy Delhi',
  'Symbiosis Institute of Design Pune',
  'CEPT Ahmedabad',
  'School of Planning and Architecture Delhi',
  'Sir JJ School of Art Mumbai', 'Delhi College of Art',
  'MS University Baroda', 'Visva-Bharati Shantiniketan',
  'Rachana Sansad Mumbai', 'College of Art New Delhi',
  'Jamia Millia Islamia', 'Amity School of Fine Arts',

  // ── Pure Sciences (Top 20 India) ──
  'TIFR Mumbai', 'IISER Pune', 'IISER Kolkata', 'IISER Mohali',
  'IISER Bhopal', 'IISER Thiruvananthapuram', 'IISER Tirupati',
  'JNU Delhi', 'Delhi University', 'Hyderabad University',
  'Banaras Hindu University', 'Aligarh Muslim University',
  'Calcutta University', 'Madras University', 'Bombay University',
  'Savitribai Phule Pune University', 'Amrita Vishwa Vidyapeetham',
  'Manipal Academy of Higher Education',
  'Christ University Bangalore', 'Presidency University Kolkata',

  // ── Medicine / Healthcare (Top 20 India) ──
  'AIIMS Delhi', 'AIIMS Bhopal', 'AIIMS Jodhpur',
  'AIIMS Rishikesh', 'AIIMS Patna', 'AIIMS Bhubaneswar',
  'CMC Vellore', 'PGIMER Chandigarh', 'JIPMER Puducherry',
  'NIMHANS Bangalore',
  'Kasturba Medical College Manipal',
  'Maulana Azad Medical College Delhi',
  'Grant Medical College Mumbai', 'KEM Hospital Mumbai',
  'Bangalore Medical College',
  'Seth GS Medical College Mumbai', 'Madras Medical College',
  'Armed Forces Medical College Pune',
  'Amrita School of Medicine', 'St Johns Medical College Bangalore',

  // ── Global Top Institutions ──
  'Stanford', 'MIT', 'Harvard', 'Carnegie Mellon', 'Caltech',
  'UC Berkeley', 'Columbia', 'Oxford', 'Cambridge', 'Wharton',
  'Imperial College London', 'ETH Zurich', 'NUS Singapore',
];

export const TOP_COMPANIES = [
  'Google', 'Meta', 'Facebook', 'Amazon', 'Microsoft', 'Apple',
  'McKinsey', 'BCG', 'Bain', 'Goldman Sachs', 'Morgan Stanley',
  'Flipkart', 'Swiggy', 'Zomato', 'Razorpay', 'PhonePe', 'CRED',
  'Uber', 'Stripe', 'Airbnb', 'Netflix', 'Tesla', 'OpenAI',
  'DeepMind', 'Salesforce', 'LinkedIn', 'Twitter', 'ByteDance',
];

export const GOOGLE_DORK_TEMPLATES = {
  linkedin_founder: 'site:linkedin.com/in "{company}" founder India',
  linkedin_building: 'site:linkedin.com/in "building" "{sector}" India 2024',
  linkedin_ex_employee: 'site:linkedin.com/in "ex-{company}" founder startup',
  twitter_building: 'site:twitter.com "building" "startup" India "{sector}" 2024',
  producthunt_india: 'site:producthunt.com "India" "{sector}" 2024',
  iit_founder: 'site:linkedin.com/in "{institution}" founder startup India 2024',
};
