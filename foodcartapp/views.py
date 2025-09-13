from django.http import JsonResponse
from django.templatetags.static import static
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
import json
from pprint import pprint


from .models import Product, Order, OrderedProduct, Restaurant
# from .serializers import OrderSerializer


# class OrderAPIView(generics.ListCreateAPIView):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    print('У-ля-ля')
    try:
        order_form = request.data

        order = Order.objects.create(
            firstname=order_form.get('firstname'),
            lastname=order_form.get('lastname'),
            phonenumber=order_form.get('phonenumber'),
            address=order_form.get('address'),
            restaurant=Restaurant.objects.get(id=1),
        )

        for product in order_form.get('products'):
            OrderedProduct.objects.create(
                product_id=product.get('product'),
                quantity=product.get('quantity'),
                order=order
            )

        return Response({'order done': model_to_dict(order, exclude=['phonenumber'])})

    except ValueError:
        return JsonResponse({
            'error': 'Оу, май',
        })


@api_view(['POST'])
def get_hello(request):
    name = request.data.get('hi') or 'motherfucker'
    return Response({'hello': name})
