"""
Account module: stub to fulfill the Account Distributed Class
This is a class Roger needs for the server to be able to display these values
appropriately in the db web interface.
"""

from direct.distributed import DistributedObjectAI


class AccountAI(DistributedObjectAI.DistributedObjectAI):
    def getSlotLimit(self):
        return 6

    def may(self, perm):
        """
        Ask whether the account has permission to <string>.
        """
        return 1
