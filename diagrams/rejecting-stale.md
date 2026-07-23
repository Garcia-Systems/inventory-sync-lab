# Rejecting a Stale Synchronization

```text
                         Authority Revision 5
                                  |
                                  v
                    Worker begins Request Revision 3
                                  |
                                  v
                         Compare revisions
                                  |
                                  v
                          Stale detected
                                  |
                                  v
                     Reject synchronization
                                  |
                                  v
                       Projection unchanged


                         Authority Revision 5
                                  |
                                  v
                    Worker begins Request Revision 5
                                  |
                                  v
                         Compare revisions
                                  |
                                  v
                         Request is current
                                  |
                                  v
                     Accept synchronization
                                  |
                                  v
                        Projection updated
```

Both workers complete normally and both requests leave the queue. The policy
changes only whether the projection update occurs.
