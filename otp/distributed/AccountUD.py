"""
Account module: stub to fulfill the Account Distributed Class
This is a class Roger needs for the server to be able to display these values
appropriately in the db web interface.
"""

from direct.distributed import DistributedObjectUD


class AccountUD(DistributedObjectUD.DistributedObjectUD):
    notify = directNotify.newCategory("AccountUD")

    def __init__(self, air):
        assert air
        DistributedObjectUD.DistributedObjectUD.__init__(self, air)

    def getSlotLimit(self):
        assert self.notify.debugCall()
        return 6

    def may(self, perm):
        """
        Ask whether the account has permission to <string>.
        """
        assert self.notify.debugCall()
        return 1
