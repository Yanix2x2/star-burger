from django.http import JsonResponse
from django.templatetags.static import static
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import phonenumbers


from .models import Product, Order, OrderedProduct, Restaurant


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

    required_fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']
    for field in required_fields:
        if field not in request.data:
            return Response({
                'error': f'Обязательное поле отсутствует: {field}'
            }, status=status.HTTP_400_BAD_REQUEST)

    try:
        phone_number = request.data['phonenumber']
        parsed_number = phonenumbers.parse(phone_number, 'RU')
        if not phonenumbers.is_valid_number(parsed_number):
            return Response({
                'error': 'Неверный формат номера телефона'
            }, status=status.HTTP_400_BAD_REQUEST)
    except phonenumbers.NumberParseException:
        return Response({
            'error': 'Неверный формат номера телефона'
        })

    products = request.data['products']

    if products is None:
        return Response({
            'error': 'products: Это поле не может быть пустым.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(products, list):
        received_type = type(products).__name__
        return Response({
            'error': f'products: Ожидался list со значениями, но был получен "{received_type}".'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(products) == 0:
        return Response({
            'error': 'products: Этот список не может быть пустым.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            return Response({
                'error': f'products[{index}]: Ожидался объект, но был получен {type(product).__name__}.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'product' not in product:
            return Response({
                'error': f'products[{index}]: Отсутствует обязательное поле "product".'
            })
        
        if 'quantity' not in product:
            return Response({
                'error': f'products[{index}]: Отсутствует обязательное поле "quantity".'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(product['quantity'], int) or product['quantity'] <= 0:
            return Response({
                'error': f'products[{index}]: quantity должно быть положительным целым числом.'
            }, status=status.HTTP_400_BAD_REQUEST)

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

    # except ValueError:
    #     return JsonResponse({
    #         'error': 'Оу, май',
    #     })
