from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    watchListings = models.ManyToManyField(
        'Listing', blank=True, related_name='watchUsers')


class Listing(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    imageURL = models.URLField()
    basePrice = models.FloatField(default=1)
    isClosed = models.BooleanField(default=False)
    category = models.ForeignKey(
        'Category', on_delete=models.CASCADE, related_name='listings')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='listings')

    def __str__(self):
        return f'The listing {self.title} is {self.description} and priced at {self.basePrice}'


class Bid(models.Model):
    price = models.FloatField()
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bids')

    def __str__(self):
        return f'$ {self.price} bid on {self.listing.title} by {self.user.username}'


class Comment(models.Model):
    content = models.CharField(max_length=1000)
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments')


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name}'
