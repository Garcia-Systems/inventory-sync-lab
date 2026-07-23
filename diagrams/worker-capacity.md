# Worker Capacity

```text
Worker:
Time 0  1        4        7        10       11
        |website |market  |store   | idle
        |--------|--------|--------|

Time 1:  website starts;                         queue []
Time 2:  website processing;                     queue [marketplace]
Time 3:  website processing;                     queue [marketplace, storefront]
Time 4:  website completes, marketplace starts;  queue [storefront]
Time 7:  marketplace completes, storefront starts; queue []
Time 10: storefront completes, worker idle;       queue []

Wait times:
website     0
marketplace 2
storefront  4
```

Queue depth counts only requests waiting to start. The request in the worker is
work in progress, and a projection changes only at the end of its three-tick
service interval.
