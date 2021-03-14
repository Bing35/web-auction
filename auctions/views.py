from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import User, Listing, Bid, Comment, Category


def categoryChoices():
    list1 = []
    for category in Category.objects.all():
        list1.append((category.pk, category.name))
    return list1


class listingForm(forms.Form):
    title = forms.CharField(label='title', max_length=200)
    description = forms.CharField(label='description', max_length=2000)
    basePrice = forms.FloatField(label='base price')
    imageURL = forms.URLField(label='image URL')
    category = forms.ChoiceField(choices=categoryChoices())


class BidForm(forms.Form):
    price = forms.FloatField(label='Bid price:')


class commentForm(forms.Form):
    listingPk = forms.CharField(widget=forms.HiddenInput)
    content = forms.CharField(max_length=1000, widget=forms.Textarea)


def index(request, setting=None, category=None):
    for listing in Listing.objects.all():
        if listing.bids.all():
            listing.basePrice = listing.bids.last().price
    if not setting:
        listings = Listing.objects.filter(isClosed=False)
    elif setting == 'watchlist':
        listings = request.user.watchListings.all()
    elif setting == 'categories':
        listings = Listing.objects.filter(
            category=Category.objects.get(name=category))
    return render(request, "auctions/index.html", {
        'listings': listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create(request):
    if request.method == 'GET':
        return render(request, 'auctions/create.html', {
            'form': listingForm()
        })
    else:
        form = listingForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            Listing(title=formData['title'], description=formData['description'], imageURL=formData['imageURL'],
                    category=Category.objects.get(pk=formData['category']), basePrice=formData['basePrice'], user=request.user).save()
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'auctions/create.html', {
                'form': form
            })


@login_required
def listing(request, id, message=None):
    listing1 = Listing.objects.get(pk=id)
    if listing1.bids.all():
        listing1.basePrice = listing1.bids.last().price

    if request.method == 'GET':
        if not listing1.isClosed:
            # * verify if user on watchlist
            try:
                listing1.watchUsers.get(pk=request.user.pk)
                watchlistAction = 'remove'
            except User.DoesNotExist:
                watchlistAction = 'add'

            return render(request, 'auctions/listing.html', {
                'listing': listing1,
                'form': BidForm(),
                'message': message,
                'action': watchlistAction,
                'comments': listing1.comments.all(),
                'commentForm': commentForm(initial={'listingPk': listing1.pk}),
                'isAuthor': listing1.user == request.user
            })
        else:
            if listing1.bids.all():
                if listing1.user == request.user:
                    message = 'You sold the Listing to '+listing1.bids.all().last().user.username
                elif listing1.bids.last().user == request.user:
                    message = 'You won the auction'
                else:
                    message = 'This item was sold'
            else:
                if listing1.user == request.user:
                    message = 'Nobody bid on your listing'
                else:
                    message = 'This item has been closed'
            return render(request, 'auctions/closedListing.html', {
                'listing': listing1,
                'message': message
            })
    else:
        form = BidForm(request.POST)
        if form.is_valid():
            bidPrice = form.cleaned_data['price']
            if bidPrice > listing1.basePrice+1:
                Bid(price=bidPrice, listing=listing1, user=request.user).save()
                return HttpResponseRedirect(reverse('listing', args=(listing1.pk,)))
            else:
                return HttpResponseRedirect(reverse('listing', args=(listing1.pk, 'The bid price must be atleast 1$ higher than the highest bid')))
        else:
            return render(request, 'auctions/listing.html', {
                'listing': listing1,
                'form': form
            })


@login_required
def watchList(request):
    if request.method == 'GET':
        return HttpResponseRedirect(reverse('index', args=('watchlist',)))
    else:
        pk = request.POST['pk']
        try:
            request.user.watchListings.get(pk=pk)
            request.user.watchListings.remove(Listing.objects.get(pk=pk))
        except Listing.DoesNotExist:
            request.user.watchListings.add(Listing.objects.get(pk=pk))

        return HttpResponseRedirect(reverse('listing', args=(pk,)))


def comments(request):
    if request.method == 'GET':
        pass
    else:
        form = commentForm(request.POST)
        if form.is_valid():
            pk = form.cleaned_data['listingPk']
            Comment(content=form.cleaned_data['content'], listing=Listing.objects.get(
                pk=pk), user=request.user).save()
            return HttpResponseRedirect(reverse('listing', args=(pk,)))
        else:
            return HttpResponseRedirect(reverse('listing', args=(pk, 'comment is not valid')))


@login_required
def close(request):
    if request.method == 'GET':
        pass
    else:
        pk = request.POST['pk']
        try:
            listing = request.user.listings.get(pk=pk)
        except Listing.DoesNotExist:
            return HttpResponseRedirect(reverse('listing', args=(pk, "You don't have the authority to close this listing")))
        listing.isClosed = True
        listing.save()
        return HttpResponseRedirect(reverse('index'))


def categories(request):
    return render(request, 'auctions/categories.html', {
        'categories': Category.objects.all()
    })
