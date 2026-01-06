
from django.db import models
from PIL import Image, ExifTags
import math
from django.db.models.signals import pre_delete
from django.dispatch import receiver


#  EXIF GPS EXTRACTION
def extract_exif_gps(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None, None

        gps_info = {}
        for tag, val in exif_data.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_info = {ExifTags.GPSTAGS.get(k, k): v for k, v in val.items()}
                break

        if not gps_info:
            return None, None

        lat = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef')

        if lat and lat_ref and lon and lon_ref:
            def to_float(dms):
                return float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600

            lat_deg = to_float(lat)
            if lat_ref != 'N':
                lat_deg = -lat_deg

            lon_deg = to_float(lon)
            if lon_ref != 'E':
                lon_deg = -lon_deg

            return lat_deg, lon_deg
        return None, None
    except Exception as e:
        print("EXIF extraction error:", e)
        return None, None

#  DISTANCE CALCULATION

def haversine_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c



#  USER MODEL
class UserData(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    earned_coins = models.IntegerField(default=0)
    spent_coins = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    is_email_verified = models.BooleanField(default=False)

    def coins_left(self):
        return self.earned_coins - self.spent_coins

    def __str__(self):
        return self.name



#  SUBMIT PROOF MODEL
class SubmitProof(models.Model):
    ACTIVITY_CHOICES = [
        ('Tree Plantation', 'Tree Plantation'),
        ('Solar Panel Installation', 'Solar Panel Installation'),
        ('Public Transport Usage', 'Public Transport Usage'),
        ('Use of Electric Vehicle', 'Use of Electric Vehicle'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=100, choices=ACTIVITY_CHOICES)
    proof_image = models.FileField(upload_to='proofs/')
    description = models.TextField(blank=True, null=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    rejection_reason = models.TextField(blank=True, null=True)
    image_hash = models.CharField(max_length=100, blank=True, null=True)
    coins_given = models.BooleanField(default=False)
    earned_coins = models.IntegerField(null=True, blank=True)
    calculated_distance = models.FloatField(null=True, blank=True)

    # GPS fields
    claimed_latitude = models.FloatField(null=True, blank=True)
    claimed_longitude = models.FloatField(null=True, blank=True)
    exif_latitude = models.FloatField(null=True, blank=True)
    exif_longitude = models.FloatField(null=True, blank=True)
    live_latitude = models.FloatField(null=True, blank=True)
    live_longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Extract EXIF data
        if self.proof_image and (self.exif_latitude is None or self.exif_longitude is None):
            lat, lon = extract_exif_gps(self.proof_image.path)
            if lat is not None and lon is not None:
                self.exif_latitude = lat
                self.exif_longitude = lon
                super().save(update_fields=['exif_latitude', 'exif_longitude'])

        # Auto validation for new submissions
        if is_new:
            reference_lat = None
            reference_lon = None

            if self.claimed_latitude is not None and self.claimed_longitude is not None:
                reference_lat = self.claimed_latitude
                reference_lon = self.claimed_longitude
                self.live_latitude = None
                self.live_longitude = None

            elif self.live_latitude is not None and self.live_longitude is not None:
                reference_lat = self.live_latitude
                reference_lon = self.live_longitude
                self.claimed_latitude = None
                self.claimed_longitude = None

            if reference_lat is not None and self.exif_latitude is not None:
                distance = haversine_distance(
                    self.exif_latitude, self.exif_longitude, reference_lat, reference_lon
                )

                if distance is not None and distance <= 50:
                    self.status = 'Accepted'
                    self.rejection_reason = None
                    self.give_coins()
                else:
                    self.status = 'Rejected'
                    self.rejection_reason = f"Photo location is {int(distance)} m away from submitted location"
            else:
                self.status = 'Pending'
                self.rejection_reason = None

            super().save(update_fields=[
                'live_latitude', 'live_longitude', 'claimed_latitude',
                'claimed_longitude', 'status', 'rejection_reason',
                'coins_given', 'earned_coins'
            ])

    # Coin distribution
    def give_coins(self):
        if self.coins_given:
            return
        coins = self.get_coin_amount()
        self.user.earned_coins += coins
        self.user.save()
        self.coins_given = True
        self.earned_coins = coins

    def get_coin_amount(self):
        return {
            'Tree Plantation': 50,
            'Public Transport Usage': 25,
            'Solar Panel Installation': 45,
            'Use of Electric Vehicle': 35,
        }.get(self.activity_type, 0)

    def __str__(self):
        return f"{self.user.name} - {self.activity_type}"

    #  Subtract coins when submission is deleted
    def delete(self, *args, **kwargs):
        if self.coins_given and self.earned_coins:
            self.user.earned_coins -= self.earned_coins
            if self.user.earned_coins < 0:
                self.user.earned_coins = 0
            self.user.save()
            print(f"{self.user.name}  {self.activity_type}  {self.earned_coins} ")
        super().delete(*args, **kwargs)



#  REWARD MODEL

class Reward(models.Model):
    name = models.CharField(max_length=100)
    cost = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name



#  REDEEMED REWARD MODEL

class RedeemedReward(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    reward_name = models.CharField(max_length=200)
    cost = models.IntegerField()
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} redeemed {self.reward_name}"
    

    

@receiver(pre_delete, sender=SubmitProof)
def subtract_coins_on_delete(sender, instance, **kwargs):
    if instance.coins_given and instance.earned_coins:
        instance.user.earned_coins -= instance.earned_coins
        if instance.user.earned_coins < 0:
            instance.user.earned_coins = 0
        instance.user.save()
        print(f"[AUTO] {instance.user.name}  {instance.activity_type}  {instance.earned_coins} ")

