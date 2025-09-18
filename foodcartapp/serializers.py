from rest_framework import serializers
from rest_framework.serializers import CharField, IntegerField, PrimaryKeyRelatedField
from phonenumber_field.modelfields import PhoneNumberField
from .models import Order, OrderedProduct, Product
from django.db import transaction


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

    @transaction.atomic
    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)

        for product_item in products_data:
            product = product_item['product']
            quantity = product_item['quantity']
            
            OrderedProduct.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

        return order
