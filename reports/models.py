from django.db import models



class Report(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    place = models.CharField(max_length=255)  # 'place' for the location
    latitude = models.FloatField()  # For latitude
    longitude = models.FloatField()  # For longitude
    report_time = models.DateTimeField(auto_now_add=True)  # Timestamp when the report is created
    type = models.CharField(max_length=50 , default= 'לא ידוע')  # Simple string value for type
    firebase_id = models.CharField(max_length=255, null=True, blank=True)  # Field for storing the Firebase ID

    def __str__(self):
        return self.title

