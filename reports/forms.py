from django import forms
from .models import Report

REPORT_TYPES = [
    ('Road', 'נזק לכביש'),
    ('Accident', 'תאונות'),
    ('Waste', 'ניהול פסולת'),
    ('TrafficSignal', 'בעיות רמזורים'),
    ('Infrastructure', 'תשתית ציבורית'),
    ('Streetlight', 'תאורת רחוב'),
    ('Pothole', 'בורות בכביש'),
    ('Parking', 'בעיות חנייה'),
    ('Flooding', 'הצפות'),
    ('Construction', 'עבודות בנייה'),
    ('Graffiti', 'גרפיטי'),
    ('Animal', 'בעיות עם בעלי חיים'),
    ('Noise', 'רעש'),
    ('Vandalism', 'ונדליזם'),
    ('PublicTransport', 'בעיות בתחבורה ציבורית'),
    ('WaterLeak', 'דליפת מים'),
    ('Electricity', 'בעיות חשמל'),
    ('Playground', 'בעיות במגרש משחקים'),
    ('PublicRestroom', 'שירותים ציבוריים'),
    ('Building', 'בעיות בבניינים')
]


class ReportForm(forms.ModelForm):
    type = forms.ChoiceField(choices=REPORT_TYPES)

    class Meta:
        model = Report
        fields = ['title', 'description', 'place', 'latitude', 'longitude', 'type']



type_dict = {
            'Road': 'נזק לכביש',
            'Accident': 'תאונות',
            'Waste': 'ניהול פסולת',
            'TrafficSignal': 'בעיות רמזורים',
            'Infrastructure': 'תשתית ציבורית',
            'Streetlight': 'תאורת רחוב',
            'Pothole': 'בורות בכביש',
            'Parking': 'בעיות חנייה',
            'Flooding': 'הצפות',
            'Construction': 'עבודות בנייה',
            'Graffiti': 'גרפיטי',
            'Animal': 'בעיות עם בעלי חיים',
            'Noise': 'רעש',
            'Vandalism': 'ונדליזם',
            'PublicTransport': 'בעיות בתחבורה ציבורית',
            'WaterLeak': 'דליפת מים',
            'Electricity': 'בעיות חשמל',
            'Playground': 'בעיות במגרש משחקים',
            'PublicRestroom': 'שירותים ציבוריים',
            'Building': 'בעיות בבניינים'
        }

