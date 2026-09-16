"""Copy for the Salesforce one-pager.

Each paragraph is a list of (text, bold) segments; a segment may carry a third
element naming a hyperlink target.
"""

WHY = [
    ("head", [("\U0001F511 Why This Matters", True)]),
    ("body", [("Linking your Salesforce certifications to Insight Global, LLC ensures they are "
               "credited to Insight Global's Salesforce partner record. ", False)]),
    ("bullet", [("More linked certifications strengthen IG's partner standing ", True),
                ("including tier progression, specializations, and access to Salesforce "
                 "enablement and funding programs", False)]),
    ("bullet", [("More certifications strengthen IG's credibility with Salesforce teams, "
                 "customers, and help us win", True)]),
    ("head", [("\U0001F517 Steps to Link", True)]),
    ("prereq", [("Pre-req: You must have at least one completed Salesforce certification and "
                 "access to your Trailhead account. ", False)]),
    ("num", [("Sign in to Trailhead Academy (", True),
             ("trailhead.salesforce.com", True, "https://trailhead.salesforce.com/credentials/"),
             (") ", True),
             ("and open your Trailhead Academy Account.", False)]),
    ("num", [("In the Employer section, enter Insight Global, LLC in the Company Name field", True),
             (" exactly as shown, then Save.", False)]),
]

TRAILBLAZER = [
    ("num", [("Sign in to your Trailblazer Profile and open Settings", True),
             (", then edit the Details tile at the bottom of the page.", False)]),
    ("num", [("In the Relationship to Salesforce field, choose Partner.", True)]),
    ("num", [("In My Company, set Company to Insight Global, LLC", True),
             (" exactly as shown, and Work Email to your IG email.", False)]),
    ("num", [("Click Save.", True)]),
]

CLOSING = [
    ("sub", [("Your certifications then begin counting toward IG's Salesforce partner metrics.", False)]),
    ("last", [("Going forward", True),
              (": register for and complete all future Salesforce training and certifications using your ", False),
              ("@InsightGlobal.com", False, "insightglobal.com"),
              (" email address so nothing needs re-linking.", False)]),
]
