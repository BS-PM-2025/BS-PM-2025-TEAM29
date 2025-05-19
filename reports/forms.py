from django import forms

from .models import Report

REPORT_TYPES = [
    ("Road", "נזק לכביש"),
    ("Accident", "תאונות"),
    ("Waste", "ניהול פסולת"),
    ("TrafficSignal", "בעיות רמזורים"),
    ("Infrastructure", "תשתית ציבורית"),
    ("Streetlight", "תאורת רחוב"),
    ("Pothole", "בורות בכביש"),
    ("Parking", "בעיות חנייה"),
    ("Flooding", "הצפות"),
    ("Graffiti", "גרפיטי"),
    ("Animal", "בעיות עם בעלי חיים"),
    ("Noise", "רעש"),
    ("Vandalism", "ונדליזם"),
    ("WaterLeak", "דליפת מים"),
    ("Electricity", "בעיות חשמל"),
    ("Playground", "בעיות במגרש משחקים"),
    ("PublicRestroom", "שירותים ציבוריים"),
    ("tree branches","ענפי עצים"),
    ("Garden care","טיפול בגנים"),
]


class ReportForm(forms.ModelForm):
    type = forms.ChoiceField(choices=REPORT_TYPES)

    class Meta:
        model = Report
        fields = ["title", "description", "place", "latitude", "longitude", "type"]


type_dict = {
    "police":        "משטרה",
    "electrical":    "Electrical Technician",
    "gardener":      "Gardener",
    "street_worker": "Street Worker",
    "janitor":       "Janitor",
    "maintenance":   "Maintenance Man",
    "plumber":       "Plumber",
    "nature reserver": "Nature Reserver",

    # …add any others you need…
}

REPORT_TYPE_LABELS = {
    code: label
    for code, label in REPORT_TYPES
}

