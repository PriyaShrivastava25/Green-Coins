from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SubmitProof, UserData

@receiver(post_save, sender=SubmitProof)
def give_coins_on_accept(sender, instance, **kwargs):
    if instance.status == 'Accepted' and not instance.coins_given:
        coins = 0
        if instance.activity_type == 'Tree Plantation':
            coins = 50
        elif instance.activity_type == 'Public Transport Usage':
            coins = 25
        elif instance.activity_type == 'Solar Panel Installation':
            coins = 40

        instance.user.earned_coins += coins
        instance.user.save()

        instance.coins_given = True
        instance.save()