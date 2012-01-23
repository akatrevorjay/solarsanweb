import kronos
import datetime
from solarsan.models import Pool, Pool_IOStat
from solarsan.utils import zpool_iostat, convert_human_to_bytes

@kronos.register('*/2 * * * *')
def cron_pool_iostats():
    """ Cron job to periodically log iostats per pool to db.
        Also creates pools that do not exist in db """

    iostats = zpool_iostat(30, [])

    for i in iostats:
        ## Convert human readable values to bytes
        for j in ['alloc', 'free', 'bandwidth_read', 'bandwidth_write']:
            iostats[i][j] = int(convert_human_to_bytes(iostats[i][j]))
        
        ## Get pool, create if !exist
        #pool = Pool.objects.get_or_create(name=i)
        try:
            pool = Pool.objects.get(name=i)
        except (KeyError, Pool.DoesNotExist):
            pool = Pool.objects.create()
            pool.name = iostats[i]['name']
            pool.save()
        
        pool.pool_iostat_set.create(timestamp=datetime.datetime.now(),
                                    alloc = iostats[i]['alloc'],
                                    free = iostats[i]['free'],
                                    bandwidth_read = iostats[i]['bandwidth_read'],
                                    bandwidth_write = iostats[i]['bandwidth_write'],
                                    iops_read = iostats[i]['iops_read'],
                                    iops_write = iostats[i]['iops_write'])
