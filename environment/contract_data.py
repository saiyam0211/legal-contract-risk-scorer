"""Synthetic contract clauses with ground-truth labels.

Each clause dict contains:
  clause_id       : unique identifier
  text            : realistic clause text an agent will read
  risk_level      : ground-truth risk level (low | medium | high | critical)
  category        : ground-truth category (see VALID_CATEGORIES in models.py)
  is_risky        : bool — True when the clause poses meaningful legal risk
  rewrite_keywords: list of terms a quality rewrite should mention (for Task 3 grader)

Missing protections expected per task are defined in tasks.py.
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Task 1  —  5 clauses  (EASY)
# ---------------------------------------------------------------------------

TASK1_CLAUSES: List[Dict[str, Any]] = [
    {
        "clause_id": "t1_c1",
        "text": (
            "Each party agrees to keep confidential all non-public information "
            "disclosed by the other party and to use such information solely for "
            "purposes of this Agreement. This obligation shall survive termination "
            "for a period of two (2) years. Either party may disclose confidential "
            "information as required by applicable law or court order, provided it "
            "gives reasonable prior written notice to the disclosing party."
        ),
        "risk_level": "low",
        "category": "confidentiality",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t1_c2",
        "text": (
            "Party A (Vendor) shall indemnify, defend, and hold harmless Party B "
            "(Client) and its officers, directors, employees, and agents from and "
            "against any and all claims, losses, damages, liabilities, costs, and "
            "expenses, including reasonable attorneys' fees, arising out of or "
            "related to this Agreement, without any cap or limit on liability."
        ),
        "risk_level": "critical",
        "category": "indemnification",
        "is_risky": True,
        "rewrite_keywords": [
            "cap",
            "limit",
            "gross negligence",
            "willful misconduct",
            "mutual",
            "proportional",
        ],
    },
    {
        "clause_id": "t1_c3",
        "text": (
            "Vendor's total cumulative liability arising out of or related to this "
            "Agreement, whether based on contract, tort, or any other legal theory, "
            "shall not exceed three (3) times the total fees paid or payable to "
            "Vendor in the twelve (12) months preceding the event giving rise to "
            "liability. This limitation shall not apply to gross negligence or "
            "willful misconduct."
        ),
        "risk_level": "medium",
        "category": "liability",
        "is_risky": True,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t1_c4",
        "text": (
            "All work product, inventions, software, designs, documentation, and "
            "other intellectual property created or developed by Vendor under this "
            "Agreement shall be the sole and exclusive property of Client. Vendor "
            "hereby irrevocably assigns all right, title, and interest in such "
            "intellectual property to Client. Vendor retains no license to use "
            "any such intellectual property after termination."
        ),
        "risk_level": "high",
        "category": "IP",
        "is_risky": True,
        "rewrite_keywords": ["license", "background IP", "pre-existing", "retain"],
    },
    {
        "clause_id": "t1_c5",
        "text": (
            "Either party may terminate this Agreement for convenience upon thirty "
            "(30) days' prior written notice to the other party. In the event of "
            "material breach, the non-breaching party may terminate immediately "
            "upon written notice if the breaching party fails to cure such breach "
            "within fifteen (15) days of receiving notice thereof."
        ),
        "risk_level": "low",
        "category": "termination",
        "is_risky": False,
        "rewrite_keywords": [],
    },
]

# ---------------------------------------------------------------------------
# Task 2  —  12 clauses  (MEDIUM) — Software Development Contract
# ---------------------------------------------------------------------------

TASK2_CLAUSES: List[Dict[str, Any]] = [
    {
        "clause_id": "t2_c1",
        "text": (
            "Vendor warrants that the software delivered under this Agreement will "
            "be 100% free of defects, bugs, and security vulnerabilities at the "
            "time of delivery and will remain so for the duration of this Agreement."
        ),
        "risk_level": "high",
        "category": "warranty",
        "is_risky": True,
        "rewrite_keywords": ["commercially reasonable", "material defects", "cure period"],
    },
    {
        "clause_id": "t2_c2",
        "text": (
            "Client shall pay all invoices within ninety (90) days of receipt. "
            "Late payments shall not accrue interest. Vendor may not suspend "
            "services for non-payment without sixty (60) days' written notice."
        ),
        "risk_level": "medium",
        "category": "payment",
        "is_risky": True,
        "rewrite_keywords": ["net-30", "interest", "suspend"],
    },
    {
        "clause_id": "t2_c3",
        "text": (
            "This Agreement shall automatically renew for successive one-year terms "
            "unless either party provides written notice of non-renewal no later "
            "than five (5) business days prior to the end of the then-current term."
        ),
        "risk_level": "high",
        "category": "termination",
        "is_risky": True,
        "rewrite_keywords": ["30 days", "60 days", "notice period"],
    },
    {
        "clause_id": "t2_c4",
        "text": (
            "Vendor shall maintain the uptime of the hosted platform at no less "
            "than 99.5% measured on a monthly basis. In the event of a breach of "
            "this SLA, Client's sole remedy shall be to notify Vendor in writing; "
            "no credits or other compensation shall be owed."
        ),
        "risk_level": "medium",
        "category": "SLA",
        "is_risky": True,
        "rewrite_keywords": ["service credit", "credit", "remedy", "compensation"],
    },
    {
        "clause_id": "t2_c5",
        "text": (
            "Each party shall maintain the confidentiality of the other party's "
            "technical and business information disclosed in connection with this "
            "Agreement for a period of three (3) years following disclosure. "
            "Information that becomes publicly available through no fault of the "
            "receiving party is excluded from this obligation."
        ),
        "risk_level": "low",
        "category": "confidentiality",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t2_c6",
        "text": (
            "All source code, algorithms, and derivative works developed by Vendor "
            "specifically for Client under this Agreement shall vest in and be "
            "owned by Client upon payment in full. Pre-existing Vendor intellectual "
            "property incorporated into the deliverables shall remain Vendor's "
            "property, with a perpetual, royalty-free license granted to Client."
        ),
        "risk_level": "low",
        "category": "IP",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t2_c7",
        "text": (
            "Vendor's aggregate liability to Client for all claims under or related "
            "to this Agreement shall not exceed the total fees paid by Client in "
            "the six (6) months preceding the claim. Neither party shall be liable "
            "for indirect, incidental, or consequential damages."
        ),
        "risk_level": "low",
        "category": "liability",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t2_c8",
        "text": (
            "Client grants Vendor a non-exclusive, worldwide, perpetual, "
            "irrevocable, royalty-free license to use, reproduce, modify, and "
            "distribute any data, feedback, or content submitted by Client through "
            "the platform for any commercial purpose, including training machine "
            "learning models."
        ),
        "risk_level": "critical",
        "category": "data_privacy",
        "is_risky": True,
        "rewrite_keywords": [
            "limited",
            "solely",
            "service improvement",
            "anonymized",
            "revocable",
            "opt-out",
        ],
    },
    {
        "clause_id": "t2_c9",
        "text": (
            "This Agreement shall be governed by and construed in accordance with "
            "the laws of the State of Delaware, USA. Any disputes arising out of "
            "this Agreement shall be resolved exclusively in the state or federal "
            "courts located in Wilmington, Delaware."
        ),
        "risk_level": "low",
        "category": "governing_law",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t2_c10",
        "text": (
            "Vendor shall indemnify Client against third-party claims arising from "
            "Vendor's infringement of any patent, copyright, or trademark. This "
            "indemnification is Client's sole remedy for intellectual property "
            "infringement claims."
        ),
        "risk_level": "medium",
        "category": "indemnification",
        "is_risky": True,
        "rewrite_keywords": ["mutual", "reciprocal", "sole remedy"],
    },
    {
        "clause_id": "t2_c11",
        "text": (
            "Vendor shall comply with all applicable data protection laws, "
            "including the General Data Protection Regulation (GDPR) and the "
            "California Consumer Privacy Act (CCPA). Vendor shall implement "
            "appropriate technical and organizational measures to protect personal "
            "data processed under this Agreement."
        ),
        "risk_level": "low",
        "category": "data_privacy",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t2_c12",
        "text": (
            "Either party may terminate this Agreement for convenience upon "
            "fourteen (14) days' written notice. Upon termination, all outstanding "
            "invoices become immediately due and payable, and Vendor shall have no "
            "obligation to return or delete Client data for sixty (60) days."
        ),
        "risk_level": "medium",
        "category": "termination",
        "is_risky": True,
        "rewrite_keywords": ["30 days", "data return", "delete", "immediately"],
    },
]

# Missing protections expected for Task 2
TASK2_MISSING_PROTECTIONS = ["force_majeure", "dispute_resolution"]

# ---------------------------------------------------------------------------
# Task 3  —  20 clauses  (HARD) — Complex Service Agreement
# ---------------------------------------------------------------------------

TASK3_CLAUSES: List[Dict[str, Any]] = [
    {
        "clause_id": "t3_c1",
        "text": (
            "Service Provider may unilaterally modify the terms and conditions of "
            "this Agreement at any time without prior notice to Client. Client's "
            "continued use of the services after any such modification constitutes "
            "acceptance of the modified terms."
        ),
        "risk_level": "critical",
        "category": "other",
        "is_risky": True,
        "rewrite_keywords": [
            "mutual consent",
            "written amendment",
            "30 days notice",
            "opt-out",
            "reject",
        ],
    },
    {
        "clause_id": "t3_c2",
        "text": (
            "All fees are non-refundable under any circumstances, including "
            "termination for cause, service outages exceeding 72 hours, or "
            "material breach by Service Provider."
        ),
        "risk_level": "high",
        "category": "payment",
        "is_risky": True,
        "rewrite_keywords": ["pro-rata", "refund", "termination for cause", "credit"],
    },
    {
        "clause_id": "t3_c3",
        "text": (
            "Client agrees that Service Provider shall have no liability whatsoever "
            "for any damages, losses, or costs arising from the use or inability to "
            "use the services, including direct, indirect, consequential, punitive, "
            "or special damages of any kind."
        ),
        "risk_level": "critical",
        "category": "liability",
        "is_risky": True,
        "rewrite_keywords": [
            "gross negligence",
            "willful misconduct",
            "cap",
            "limitation",
            "reasonable",
        ],
    },
    {
        "clause_id": "t3_c4",
        "text": (
            "Service Provider shall use commercially reasonable efforts to maintain "
            "platform availability and shall provide advance notice of scheduled "
            "maintenance windows of at least 48 hours."
        ),
        "risk_level": "low",
        "category": "SLA",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t3_c5",
        "text": (
            "Client grants Service Provider an irrevocable, perpetual, worldwide, "
            "sublicensable, royalty-free license to use, copy, store, transmit, "
            "display, modify, and create derivative works of all Client data, "
            "content, and materials uploaded to the platform, including for "
            "product development and resale purposes."
        ),
        "risk_level": "critical",
        "category": "data_privacy",
        "is_risky": True,
        "rewrite_keywords": [
            "revocable",
            "solely for service delivery",
            "no commercial use",
            "anonymized",
            "no sublicense",
            "delete upon termination",
        ],
    },
    {
        "clause_id": "t3_c6",
        "text": (
            "Each party shall keep confidential and not disclose to any third party "
            "the other party's Confidential Information, using at least the same "
            "degree of care it uses to protect its own confidential information "
            "of similar nature, but no less than reasonable care."
        ),
        "risk_level": "low",
        "category": "confidentiality",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t3_c7",
        "text": (
            "Service Provider shall indemnify, defend, and hold harmless Client "
            "from any third-party claims arising out of Service Provider's gross "
            "negligence or willful misconduct. Client shall indemnify Service "
            "Provider for claims arising from Client's use of the services in "
            "violation of this Agreement."
        ),
        "risk_level": "medium",
        "category": "indemnification",
        "is_risky": True,
        "rewrite_keywords": ["negligence", "IP infringement", "mutual", "cap"],
    },
    {
        "clause_id": "t3_c8",
        "text": (
            "This Agreement, including all exhibits and schedules, constitutes the "
            "entire agreement between the parties with respect to its subject matter "
            "and supersedes all prior negotiations, representations, and agreements."
        ),
        "risk_level": "low",
        "category": "other",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t3_c9",
        "text": (
            "Any dispute arising out of or relating to this Agreement shall be "
            "subject to the exclusive jurisdiction of the courts of the Cayman "
            "Islands. Client waives any objection to the laying of venue and "
            "irrevocably submits to personal jurisdiction in such courts."
        ),
        "risk_level": "high",
        "category": "governing_law",
        "is_risky": True,
        "rewrite_keywords": [
            "arbitration",
            "home jurisdiction",
            "neutral forum",
            "mediation",
        ],
    },
    {
        "clause_id": "t3_c10",
        "text": (
            "Service Provider warrants that the services will perform substantially "
            "in accordance with the documentation. Client's exclusive remedy for "
            "breach of this warranty is re-performance of the affected services."
        ),
        "risk_level": "medium",
        "category": "warranty",
        "is_risky": True,
        "rewrite_keywords": ["refund", "termination", "credit", "damages"],
    },
    {
        "clause_id": "t3_c11",
        "text": (
            "Client shall pay all invoices within fifteen (15) days of receipt. "
            "Overdue amounts shall accrue interest at 1.5% per month. Service "
            "Provider may suspend services upon five (5) days' notice for "
            "non-payment."
        ),
        "risk_level": "medium",
        "category": "payment",
        "is_risky": True,
        "rewrite_keywords": ["net-30", "cure period", "dispute process"],
    },
    {
        "clause_id": "t3_c12",
        "text": (
            "Client acknowledges that Service Provider's platform may be "
            "temporarily unavailable due to maintenance, updates, or circumstances "
            "beyond Service Provider's control. Service Provider shall not be "
            "liable for any losses caused by such unavailability."
        ),
        "risk_level": "medium",
        "category": "SLA",
        "is_risky": True,
        "rewrite_keywords": ["scheduled maintenance", "SLA credit", "uptime guarantee"],
    },
    {
        "clause_id": "t3_c13",
        "text": (
            "Upon termination for any reason, Client's right to access the services "
            "and all Client data stored on the platform shall terminate immediately. "
            "Service Provider shall delete all Client data within 7 days and shall "
            "have no obligation to provide data export assistance."
        ),
        "risk_level": "high",
        "category": "termination",
        "is_risky": True,
        "rewrite_keywords": ["data export", "30-day grace", "transition assistance", "portability"],
    },
    {
        "clause_id": "t3_c14",
        "text": (
            "Service Provider may assign this Agreement and its rights and "
            "obligations hereunder to any successor in interest or acquirer "
            "without Client's prior written consent."
        ),
        "risk_level": "high",
        "category": "other",
        "is_risky": True,
        "rewrite_keywords": ["consent", "prior written consent", "assignment restriction"],
    },
    {
        "clause_id": "t3_c15",
        "text": (
            "Service Provider shall comply with all applicable laws and regulations "
            "in performing services under this Agreement and shall obtain and "
            "maintain all necessary permits, licenses, and certifications."
        ),
        "risk_level": "low",
        "category": "other",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t3_c16",
        "text": (
            "Client shall use the services solely for its internal business purposes "
            "and shall not resell, sublicense, or otherwise make the services "
            "available to any third party without Service Provider's prior written "
            "consent."
        ),
        "risk_level": "low",
        "category": "other",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t3_c17",
        "text": (
            "Service Provider reserves the right to suspend or terminate Client's "
            "access to the services immediately and without notice if Service "
            "Provider determines, in its sole discretion, that Client has violated "
            "any provision of this Agreement or applicable law."
        ),
        "risk_level": "high",
        "category": "termination",
        "is_risky": True,
        "rewrite_keywords": ["written notice", "cure period", "due process", "material breach"],
    },
    {
        "clause_id": "t3_c18",
        "text": (
            "All notices under this Agreement shall be in writing and delivered by "
            "email to the addresses specified in the Order Form, with confirmation "
            "of receipt. Notices shall be deemed delivered upon the sender's "
            "receipt of a delivery confirmation."
        ),
        "risk_level": "low",
        "category": "other",
        "is_risky": False,
        "rewrite_keywords": [],
    },
    {
        "clause_id": "t3_c19",
        "text": (
            "Service Provider may engage subcontractors to perform any portion of "
            "the services without Client's prior approval. Service Provider shall "
            "remain responsible for the performance of any such subcontractors; "
            "however, subcontractors shall not be bound by confidentiality "
            "obligations equivalent to those in this Agreement."
        ),
        "risk_level": "high",
        "category": "confidentiality",
        "is_risky": True,
        "rewrite_keywords": [
            "NDA",
            "bound by",
            "equivalent confidentiality",
            "prior approval",
            "notify",
        ],
    },
    {
        "clause_id": "t3_c20",
        "text": (
            "The parties agree that the prevailing party in any litigation arising "
            "out of this Agreement shall be entitled to recover its reasonable "
            "attorneys' fees and costs from the non-prevailing party."
        ),
        "risk_level": "medium",
        "category": "governing_law",
        "is_risky": True,
        "rewrite_keywords": ["cap", "each party bears", "mutual", "limit"],
    },
]

# Missing protections expected for Task 3
TASK3_MISSING_PROTECTIONS = [
    "limitation_of_liability",  # t3_c3 removes it entirely — no real cap exists
    "IP_ownership",             # no clause clearly assigns deliverable IP to client
    "dispute_resolution",       # no mediation/arbitration clause
    "force_majeure",            # no force majeure clause
]

# ---------------------------------------------------------------------------
# Combined lookup by clause_id
# ---------------------------------------------------------------------------

ALL_CLAUSES_BY_ID: dict = {
    c["clause_id"]: c
    for c in TASK1_CLAUSES + TASK2_CLAUSES + TASK3_CLAUSES
}
