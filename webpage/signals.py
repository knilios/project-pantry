"""Import the essential package for signal."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Recipe, Profile
from decouple import config


@receiver(post_save, sender=Recipe)
def check_approved_recipes(sender, instance, created, **kwargs):
    """
    Signal handler to check if a user has at least 10 approved recipes and award a chef badge.

    :param sender: The model class (`Recipe`) that triggered the signal.
    :param instance: The actual instance of the `Recipe` that was just saved.
    :param created: A boolean indicating whether the `instance` is newly created.
    :param kwargs: Additional keyword arguments passed by the signal handler (not used in this case).
    """
    chef_badge_approved_amount = config('CHEF_BADGE_APPROVED', cast=int, default=10)
    if instance.status == 'approved':
        user = instance.poster_id
        approved_recipes_count = Recipe.objects.filter(poster_id=user, status='Approved').count()
        if approved_recipes_count >= chef_badge_approved_amount:
            profile, created = Profile.objects.get_or_create(user=user)
            profile.chef_badge = True
            profile.save()
