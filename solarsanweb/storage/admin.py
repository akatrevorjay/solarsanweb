
from django_mongoengine import admin

from storage.models import Pool, Dataset, Filesystem, Volume, Snapshot


class PoolAdmin(admin.DocumentAdmin):
    pass

class DatasetAdmin(admin.DocumentAdmin):
    pass

class FilesystemAdmin(admin.DocumentAdmin):
    pass

class VolumeAdmin(admin.DocumentAdmin):
    pass

class SnapshotAdmin(admin.DocumentAdmin):
    pass


#admin.site.register(PoolDocument, PoolDocumentAdmin)
admin.site.register(Pool, PoolAdmin)
#admin.site.register(DatasetDocument, DatasetDocumentAdmin)
admin.site.register(Dataset, DatasetAdmin)

admin.site.register(Filesystem, FilesystemAdmin)
admin.site.register(Volume, VolumeAdmin)
admin.site.register(Snapshot, SnapshotAdmin)

