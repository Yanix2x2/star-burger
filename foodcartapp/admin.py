from django.contrib import admin
from django.shortcuts import redirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from .models import Product
from .models import OrderedProduct
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order
from geo.models import AddressPoint
from .utils import get_available_restaurants_for_orders


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


class ProductInline(admin.TabularInline):
    model = OrderedProduct
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'firstname', 'lastname', 'address',
        'status', 'payment', 'restaurant',
        'show_available_restaurants',
    ]
    readonly_fields = ("show_available_restaurants",)

    def save_model(self, request, obj, form, change):
        if change and 'restaurant' in form.changed_data:
            if obj.restaurant is not None and obj.status == 'new':
                obj.status = 'collect'

            if not obj.called_at:
                obj.called_at = timezone.now()
        
        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        next_url = request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
        ):
            return redirect(next_url, permanent=False)
        return super().response_change(request, obj)

    def show_available_restaurants(self, obj):
        orders = get_available_restaurants_for_orders([obj])
        order = orders[0]

        if not getattr(order, 'available_restaurants', None):
            return "Нет доступных ресторанов"

        result = []
        for restaurant, distance in order.available_restaurants:
            if distance is not None:
                result.append(f"{restaurant.name} ({distance:.1f} км)")
            else:
                result.append(f"{restaurant.name} (расчет расстояния...)")

        return format_html("<br>".join(result))

    show_available_restaurants.short_description = "Доступные рестораны (с расстоянием)"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "restaurant":
            order_id = request.resolver_match.kwargs.get("object_id")
            if order_id:
                try:
                    from foodcartapp.models import Order, Restaurant, RestaurantMenuItem
                    from collections import defaultdict

                    order = Order.objects.prefetch_related('products__product').get(pk=order_id)

                    order_product_ids = set(order.products.values_list('product_id', flat=True))
                    if not order_product_ids:
                        return super().formfield_for_foreignkey(db_field, request, **kwargs)

                    menu_items = (
                        RestaurantMenuItem.objects
                        .filter(availability=True)
                        .select_related('restaurant', 'product')
                    )

                    restaurant_menu = defaultdict(set)
                    for item in menu_items:
                        restaurant_menu[item.restaurant].add(item.product_id)

                    restaurant_ids = [
                        restaurant.id
                        for restaurant, products in restaurant_menu.items()
                        if order_product_ids.issubset(products)
                    ]

                    kwargs["queryset"] = Restaurant.objects.filter(id__in=restaurant_ids)

                except Order.DoesNotExist:
                    pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AddressPoint)
class AddressPoint(admin.ModelAdmin):
    list_display = ("address", "latitude", "longitude", "registered_at")
