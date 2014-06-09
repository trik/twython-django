from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.core.urlresolvers import reverse

from twython import Twython

User = get_user_model()


# If you've got your own Profile setup, see the note in the models file
# about adapting this to your own setup.
from twython_django_oauth.models import TwitterProfile


def logout(request, redirect_url=settings.LOGOUT_REDIRECT_URL):
    """
        Nothing hilariously hidden here, logs a user out. Strip this out if your
        application already has hooks to handle this.
    """
    django_logout(request)
    return HttpResponseRedirect(request.build_absolute_uri(redirect_url))


def begin_auth(request):
    """The view function that initiates the entire handshake.

    For the most part, this is 100% drag and drop.
    """
    # Instantiate Twython with the first leg of our trip.
    twitter = Twython(settings.TWITTER_KEY, settings.TWITTER_SECRET)

    # Request an authorization url to send the user to...
    callback_url = request.build_absolute_uri(reverse('twython_django_oauth.views.thanks'))
    auth_props = twitter.get_authentication_tokens(callback_url)

    # Then send them over there, durh.
    request.session['request_token'] = auth_props
    return HttpResponseRedirect(auth_props['auth_url'])


def thanks(request, redirect_url=settings.LOGIN_REDIRECT_URL):
    """A user gets redirected here after hitting Twitter and authorizing your app to use their data.

    This is the view that stores the tokens you want
    for querying data. Pay attention to this.

    """
    # Now that we've got the magic tokens back from Twitter, we need to exchange
    # for permanent ones and store them...
    oauth_token = request.session['request_token']['oauth_token']
    oauth_token_secret = request.session['request_token']['oauth_token_secret']
    twitter = Twython(settings.TWITTER_KEY, settings.TWITTER_SECRET,
                      oauth_token, oauth_token_secret)

    # Retrieve the tokens we want...
    authorized_tokens = twitter.get_authorized_tokens(request.GET['oauth_verifier'])

    username = authorized_tokens['screen_name']
    # If they already exist, grab them, login and redirect to a page displaying stuff.
    try:
        user = TwitterProfile.objects.get(screen_name=authorized_tokens['screen_name']).user
    except TwitterProfile.DoesNotExist:
        # We mock a creation here; no email, password is just the token, etc.
        res = User.objects.filter(username=username)
        import random
        while res.count() > 0:
            num = random.randint(1, 90000)
            res = User.objects.filter(username="%s%d" % (username, num))
            if res.count() == 0:
                username = "%s%d" % (username, num)
        default_email = settings.TWYTHON_DJANGO_DEFAULT_EMAIL if hasattr(settings, 'TWYTHON_DJANGO_DEFAULT_EMAIL') \
            else "fjdsfn@jfndjfn.com"
        user = User.objects.create_user(username, default_email, authorized_tokens['oauth_token_secret'])
        profile = TwitterProfile()
        profile.user = user
        profile.screen_name = authorized_tokens['screen_name']
        profile.oauth_token = authorized_tokens['oauth_token']
        profile.oauth_secret = authorized_tokens['oauth_token_secret']
        profile.save()

    #user = authenticate(
    #    username=authorized_tokens['screen_name'],
    #    password=authorized_tokens['oauth_token_secret']
    #)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return HttpResponseRedirect(redirect_url)


def user_timeline(request):
    """An example view with Twython/OAuth hooks/calls to fetch data about the user in question."""
    user = request.user.twitterprofile
    twitter = Twython(settings.TWITTER_KEY, settings.TWITTER_SECRET,
                      user.oauth_token, user.oauth_secret)
    user_tweets = twitter.get_home_timeline()
    return render_to_response('tweets.html', {'tweets': user_tweets})
