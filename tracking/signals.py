from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """
    Ensure a UserProfile exists for every User and is saved when the User is saved.
    Uses get_or_create to prevent IntegrityErrors if the profile already exists.
    """
    UserProfile.objects.get_or_create(user=instance)
    
    # Optional: If you want to auto-save the profile when the user is saved,
    # but be careful of recursion. Django's post_save doesn't usually cause 
    # a loop unless you save the sender (User) inside here.
    if hasattr(instance, 'profile'):
        instance.profile.save()
