
from django_mongoengine import admin

from zfs.models import PoolDocument, DatasetDocument


class PoolDocumentAdmin(admin.DocumentAdmin):
    pass


class DatasetDocumentAdmin(admin.DocumentAdmin):
    pass

admin.site.register(PoolDocument, PoolDocumentAdmin)
admin.site.register(DatasetDocument, DatasetDocumentAdmin)


