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
    required_fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']
    
    missing_fields = [field for field in required_fields if field not in request.data]
    if missing_fields:
        error_message = f"{', '.join(missing_fields)}: Обязательное поле."
        return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

    empty_fields = [field for field in required_fields if request.data.get(field) in (None, '')]
    if empty_fields:
        error_message = f"{', '.join(empty_fields)}: Это поле не может быть пустым."
        return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

    string_fields = ['firstname', 'lastname', 'address']
    for field in string_fields:
        if field in request.data and not isinstance(request.data[field], str):
            return Response({
                'error': f'{field}: Ожидалась строка, но был получен {type(request.data[field]).__name__}.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        phone_number = request.data['phonenumber']
        parsed_number = phonenumbers.parse(phone_number, 'RU')
        if not phonenumbers.is_valid_number(parsed_number):
            return Response({'error': 'Неверный формат номера телефона'}, status=status.HTTP_400_BAD_REQUEST)
    except phonenumbers.NumberParseException:
        return Response({'error': 'Неверный формат номера телефона'}, status=status.HTTP_400_BAD_REQUEST)
    
    products = request.data['products']
    
    if not isinstance(products, list):
        return Response({
            'error': f'products: Ожидался list, но был получен "{type(products).__name__}".'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not products:
        return Response({'error': 'products: Этот список не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)
    
    product_ids = []
    
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            return Response({
                'error': f'products[{index}]: Ожидался объект, но был получен {type(product).__name__}.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'product' not in product:
            return Response({
                'error': f'products[{index}]: Отсутствует обязательное поле "product".'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'quantity' not in product:
            return Response({
                'error': f'products[{index}]: Отсутствует обязательное поле "quantity".'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(product['quantity'], int) or product['quantity'] <= 0:
            return Response({
                'error': f'products[{index}]: quantity должно быть положительным целым числом.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(product['product'], int):
            return Response({
                'error': f'products[{index}]: product должен быть целым числом.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        product_ids.append(product['product'])
    
    if product_ids:
        existing_products = Product.objects.filter(id__in=product_ids).values_list('id', flat=True)
        non_existing_products = set(product_ids) - set(existing_products)
        
        if non_existing_products:
            non_existing_list = sorted(list(non_existing_products))
            return Response({
                'error': f'products: Недопустимый первичный ключ "{non_existing_list[0]}" - продукт не существует.'
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

    return Response({'success': model_to_dict(order, exclude=['phonenumber'])})
