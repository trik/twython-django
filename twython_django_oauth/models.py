from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings


class TwitterModel(models.Model):
    def disconnect_twitter(self):
        try:
            tp = TwitterProfile.objects.get(user=self)
            tp.delete()
        except TwitterProfile.DoesNotExist:
            pass

    class Meta:
        abstract = True


class TwitterProfile(models.Model):
    """
        An example Profile model that handles storing the oauth_token and
        oauth_secret in relation to a user. Adapt this if you have a current
        setup, there's really nothing special going on here.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    screen_name = models.CharField(max_length=200)
    oauth_token = models.CharField(max_length=200)
    oauth_secret = models.CharField(max_length=200)
