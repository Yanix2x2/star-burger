from django.contrib import admin
from django.shortcuts import redirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils import timezone

from .models import Product
from .models import OrderedProduct
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order


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
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
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
    list_display = ("id", "firstname", "lastname", "status", "restaurant", "created_at")
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
        if next_url:
            return redirect(next_url, permanent=False)

        return super().response_change(request, obj)

    def show_available_restaurants(self, obj):
        restaurants = obj.get_available_restaurants()
        if not restaurants.exists():
            return "Нет доступных ресторанов"
        return ", ".join(r.name for r in restaurants)
    show_available_restaurants.short_description = "Ресторан"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "restaurant":
            order_id = request.resolver_match.kwargs.get("object_id")
            if order_id:
                try:
                    order = Order.objects.get(pk=order_id)
                    kwargs["queryset"] = order.get_available_restaurants()
                except Order.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)