import datetime
import random

from dictabase import BaseTable, RegisterDBURI, FindOne, New, FindAll

RegisterDBURI('sqlite:///JobStore.db')


class Job(BaseTable):
    pass


# for i in range(100):
#     New(Item, dt=datetime.datetime.utcnow() + datetime.timedelta(seconds=random.randint(-100000, 100000)),
#         name=str(random.randint(1, 100)),
#         other='other',
#         )

res = FindAll(Job, status='pending', kind='repeat', _orderBy='dt', _limit=1)
for item in res:
    print(item)

