import abc
import dbm
import sys
import time

from panda3d.core import ConfigVariableString


class AccountDB(abc.ABC):
    def __init__(self, loginManager):
        self.loginManager = loginManager

    @abc.abstractmethod
    def storeAccountId(self, playToken, accountDoId, callback, extraData):
        pass

    @abc.abstractmethod
    def lookup(self, playToken, callback):
        pass


class DeveloperAccountDB(AccountDB):
    def __init__(self, loginManager):
        super().__init__(loginManager)

        accountDbFile = ConfigVariableString("accountdb-local-file", "database/accounts").getValue()
        if sys.platform != "darwin":
            self.dbm = dbm.open(accountDbFile, "c")
        else:
            self.dbm = dbm.dumb.open(accountDbFile, "c")

    def storeAccountId(self, databaseId, accountId, callback, extraData):
        self.dbm[databaseId] = str(accountId)
        if hasattr(self.dbm, "sync") and self.dbm.sync:
            self.dbm.sync()
            callback(True)
        else:
            self.loginManager.notify.warning(f"Unable to associate user {databaseId} with account {accountId}!")
            callback(False)

    def lookup(self, playToken, callback):
        if str(playToken) not in self.dbm:
            defaultAccessLevel = ConfigVariableString("default-access-level", "USER").getValue()
            callback({"success": True, "accountId": 0, "databaseId": playToken, "staffAccess": defaultAccessLevel})
        else:

            def handleAccountInfo(dclass, fields):
                callback(
                    {
                        "success": True,
                        "accountId": int(self.dbm[playToken]),
                        "databaseId": playToken,
                        "lastLogin": fields.get("LAST_LOGIN", time.ctime()),
                        "staffAccess": fields.get("STAFF_ACCESS", "USER"),
                    }
                )

            self.loginManager.air.dbInterface.queryObject(
                self.loginManager.air.dbId, int(self.dbm[playToken]), handleAccountInfo
            )
