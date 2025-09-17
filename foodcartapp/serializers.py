from rest_framework import serializers
from rest_framework.serializers import CharField, IntegerField, PrimaryKeyRelatedField
from phonenumber_field.modelfields import PhoneNumberField
from .models import Order, OrderedProduct, Product


class OrderedProductSerializer(serializers.ModelSerializer):
    product = PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    quantity = IntegerField(min_value=1)

    class Meta:
        model = OrderedProduct
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    # restaurant = CharField()
    products = OrderedProductSerializer(many=True, allow_empty=False)
    firstname = CharField()
    lastname = CharField()
    phonenumber = PhoneNumberField(region="RU")
    address = CharField()

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products'
        ]
