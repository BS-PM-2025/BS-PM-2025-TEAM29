# reports/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Report(models.Model):
    title        = models.CharField(max_length=100)
    description  = models.TextField()
    place        = models.CharField(max_length=255)
    latitude     = models.FloatField()
    longitude    = models.FloatField()
    report_time  = models.DateTimeField(auto_now_add=True)
    type         = models.CharField(max_length=50, default="לא ידוע")
    firebase_id  = models.CharField(max_length=255, null=True, blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Profile(models.Model):
    JOB_CHOICES = [
        ("police",        "Police"),
        ("electrical",    "Electrical Technician"),
        ("gardener",      "Gardener"),
        ("street_worker", "Street Worker"),
        ("janitor",       "Janitor"),
        ("maintenance",   "Maintenance Man"),
        ("plumber",       "Plumber"),
        ("nature reserver", "Nature Reserver"),
    ]

    user      = models.OneToOneField(User, on_delete=models.CASCADE)
    is_worker = models.BooleanField(default=False)
    job       = models.CharField(max_length=20, choices=JOB_CHOICES, blank=True)

    def __str__(self):
        kind = "Worker" if self.is_worker else "User"
        return f"{self.user.username} ({kind})"

class Notification(models.Model):
    profile   = models.ForeignKey("Profile", on_delete=models.CASCADE, related_name="notifications")
    report    = models.ForeignKey(Report,   on_delete=models.CASCADE)
    message   = models.TextField()
    created   = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    def __str__(self):
        return f"Notif for {self.profile.user.username}: {self.message[:20]}…"


# Map each Report.type → list of Profile.job codes who should be notified
REPORT_TO_JOBS = {
    "Road":           ["maintenance", "street_worker"],
    "Accident":       ["street_worker"],
    "Waste":          ["street_worker", "janitor"],
    "TrafficSignal":  ["electrical"],
    "Infrastructure": ["maintenance"],
    "Streetlight":    ["electrical"],
    "Pothole":        ["maintenance"],
    "Parking":        ["street_worker"],
    "Flooding":       ["maintenance"],
    "Graffiti":       ["street_worker"],
    "Animal":         ["street_worker"],
    "Noise":          ["street_worker"],
    "Vandalism":      ["street_worker"],
    "WaterLeak":      ["plumber", "maintenance"],
    "Electricity":    ["electrical"],
    "Playground":     ["street_worker"],
    "PublicRestroom": ["janitor"],
    "tree branches":  ["gardener"],
    "Garden care":    ["gardener"],
}

latitude  = models.FloatField(null=True, blank=True)
longitude = models.FloatField(null=True, blank=True)


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
