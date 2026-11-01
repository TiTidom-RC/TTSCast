""" Cycle de vie des connexions aux appareils Cast : connexion des seuls équipements actifs (et des membres de groupes actifs),
déconnexion réelle à la désactivation, objets remplacés, membres de groupe, TTS de test. Aucun appareil réel nécessaire.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import types as pytypes
import unittest
from unittest import mock

from pychromecast.models import HostServiceInfo

import ttscastd
from tests.helpers import fakeGroup, newCast, resetDaemonState, stopAllConnections, waitUntil

myCast = ttscastd.myCast
myConfig = ttscastd.myConfig


class FakeListener:
    def __init__(self, name, cast):
        self.name, self.cast, self.statuses = name, cast, []

    def new_cast_status(self, status):
        self.statuses.append(status)


class CastLifecycleTestCase(unittest.TestCase):
    def setUp(self):
        self.comm = resetDaemonState()
        self.extraCasts = []

    def tearDown(self):
        stopAllConnections(*self.extraCasts)


class CastConnectTest(CastLifecycleTestCase):
    def testDiscoveredDeviceIsNotConnected(self):
        _, chromecast = newCast()
        self.assertFalse(chromecast.socket_client.is_alive())
        self.assertFalse(chromecast.socket_client.is_connected)
        self.assertIsNone(chromecast.status)

    def testCastConnectStartsOnceOnly(self):
        _, chromecast = newCast()
        myCast.castConnect(chromecast)
        myCast.castConnect(chromecast)  # second appel : pas de RuntimeError (un thread ne démarre qu'une fois)
        self.assertTrue(chromecast.socket_client.is_alive())

    def testCastConnectTimeout(self):
        _, chromecast = newCast()
        with self.assertRaises(Exception) as context:
            myCast.castConnect(chromecast, timeout=0.3)
        self.assertEqual(type(context.exception).__name__, 'RequestTimeout')


class CastCallBackTest(CastLifecycleTestCase):
    def setUp(self):
        super().setUp()
        self.registered = []
        patcher = mock.patch.object(myCast, 'castListeners', staticmethod(lambda chromecast=None, uuid=None: self.registered.append(uuid)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def testEnabledDeviceGetsListeners(self):
        uuid, chromecast = newCast(register=False)
        myConfig.GCAST_UUID.append(uuid)
        myCast.castCallBack(chromecast)
        self.assertEqual(self.registered, [uuid])

    def testUnconfiguredDeviceIsNotConnected(self):
        _, chromecast = newCast(register=False)
        myCast.castCallBack(chromecast)
        self.assertEqual(self.registered, [])
        self.assertFalse(chromecast.socket_client.is_alive())

    def testGroupMemberDiscoveredAfterItsGroupIsConnected(self):
        uuid, chromecast = newCast(register=False)
        myConfig.NETCAST_GROUPS[object()] = fakeGroup([uuid])
        myCast.castCallBack(chromecast)
        self.assertTrue(chromecast.socket_client.is_alive())

    def testAlreadyKnownDeviceIsIgnored(self):
        uuid, chromecast = newCast()
        duplicate = pytypes.SimpleNamespace(uuid=uuid, name='doublon')
        myCast.castCallBack(duplicate)
        self.assertIs(myConfig.NETCAST_DEVICES[uuid], chromecast)


class CastRemoveTest(CastLifecycleTestCase):
    def testRemoveDisconnectsAndReplaces(self):
        uuid, chromecast = newCast()
        myCast.castConnect(chromecast)
        for listeners in (myConfig.LISTENER_CAST, myConfig.LISTENER_MEDIA, myConfig.LISTENER_CONNECT):
            listeners[uuid] = object()
        myConfig.NETCAST_GROUPS[uuid] = fakeGroup([])
        myCast._castRemove(chromecast, uuid)
        self.extraCasts.append(chromecast)
        replacement = myConfig.NETCAST_DEVICES[uuid]
        self.assertTrue(waitUntil(lambda: not chromecast.socket_client.is_alive()))
        self.assertIsNot(replacement, chromecast)
        self.assertFalse(replacement.socket_client.is_alive())
        for store in (myConfig.LISTENER_CAST, myConfig.LISTENER_MEDIA, myConfig.LISTENER_CONNECT, myConfig.NETCAST_GROUPS):
            self.assertNotIn(uuid, store)
        self.assertTrue(myCast.isStaleCast(chromecast))
        self.assertFalse(myCast.isStaleCast(replacement))
        self.assertEqual(self.comm.sent, [], 'rien n\'est envoyé à Jeedom au retrait (équipement possiblement supprimé)')

    def testReplacementCanBeReconnected(self):
        uuid, chromecast = newCast()
        myCast.castConnect(chromecast)
        myCast._castRemove(chromecast, uuid)
        self.extraCasts.append(chromecast)
        replacement = myConfig.NETCAST_DEVICES[uuid]
        myCast.castConnect(replacement)
        self.assertTrue(replacement.socket_client.is_alive())

    def testRemoveOfNeverConnectedDeviceKeepsIt(self):
        uuid, chromecast = newCast()
        myCast._castRemove(chromecast, uuid)
        self.assertIs(myConfig.NETCAST_DEVICES[uuid], chromecast)

    def testRemovedDeviceStillInActiveGroupIsReconnected(self):
        uuid, chromecast = newCast()
        myCast.castConnect(chromecast)
        myConfig.LISTENER_CAST[uuid] = object()
        myConfig.NETCAST_GROUPS[object()] = fakeGroup([uuid])
        myCast._castRemove(chromecast, uuid)
        self.extraCasts.append(chromecast)
        replacement = myConfig.NETCAST_DEVICES[uuid]
        self.assertIsNot(replacement, chromecast)
        self.assertTrue(replacement.socket_client.is_alive(), 'reconnecté sans listeners, pour le volume des diffusions sur le groupe')

    def testGroupRemovalDisconnectsMembersConnectedOnlyForIt(self):
        groupUUID, group = newCast('Toutes', 'group')
        otherGroupUUID, _ = newCast('Hors Chambres', 'group')
        onlyHereUUID, onlyHere = newCast('Membre de ce seul groupe')
        sharedUUID, shared = newCast('Membre des deux groupes')
        enabledUUID, enabled = newCast('Membre actif dans Jeedom')
        myConfig.GCAST_UUID += [otherGroupUUID, enabledUUID]
        myConfig.NETCAST_GROUPS[groupUUID] = fakeGroup([onlyHereUUID, sharedUUID.hex, enabledUUID])  # membre annoncé sans tirets
        myConfig.NETCAST_GROUPS[otherGroupUUID] = fakeGroup([sharedUUID])
        for chromecast in (group, onlyHere, shared, enabled):
            myCast.castConnect(chromecast)
        myConfig.LISTENER_CAST[groupUUID] = object()
        myCast._castRemove(uuid=groupUUID)
        self.extraCasts += [group, onlyHere]
        self.assertNotIn(groupUUID, myConfig.NETCAST_GROUPS)
        self.assertIsNot(myConfig.NETCAST_DEVICES[onlyHereUUID], onlyHere)
        self.assertTrue(waitUntil(lambda: not onlyHere.socket_client.is_alive()))
        self.assertIs(myConfig.NETCAST_DEVICES[sharedUUID], shared)
        self.assertTrue(shared.socket_client.is_alive())
        self.assertIs(myConfig.NETCAST_DEVICES[enabledUUID], enabled)
        self.assertTrue(enabled.socket_client.is_alive())


class GroupMemberTest(CastLifecycleTestCase):
    def testIsActiveGroupMemberAcceptsBothUuidForms(self):
        dashed, undashed, outside = newCast()[0], newCast()[0], newCast()[0]
        myConfig.NETCAST_GROUPS[object()] = fakeGroup([str(dashed), undashed.hex])
        self.assertTrue(myCast.isActiveGroupMember(dashed))
        self.assertTrue(myCast.isActiveGroupMember(undashed))
        self.assertFalse(myCast.isActiveGroupMember(outside))

    def testConnectGroupMemberRules(self):
        disabledUUID, disabled = newCast('Membre désactivé')
        enabledUUID, enabled = newCast('Membre actif')
        outsideUUID, outside = newCast('Hors groupe')
        myConfig.GCAST_UUID.append(enabledUUID)
        myConfig.NETCAST_GROUPS[object()] = fakeGroup([disabledUUID, enabledUUID])
        for uuid in (disabledUUID, enabledUUID, outsideUUID):
            myCast.connectGroupMember(uuid)
        self.assertTrue(disabled.socket_client.is_alive())
        self.assertFalse(enabled.socket_client.is_alive(), 'actif dans Jeedom : connecté par castListeners, avec ses listeners')
        self.assertFalse(outside.socket_client.is_alive())

    def testNoGroupMemberConnectionDuringShutdown(self):
        uuid, chromecast = newCast()
        myConfig.NETCAST_GROUPS[object()] = fakeGroup([uuid])
        myConfig.IS_ENDING = True
        myCast.connectGroupMember(uuid)
        self.assertFalse(chromecast.socket_client.is_alive())

    def testGroupSnapshotNeverWaits(self):
        connectedUUID, offlineUUID, missingUUID = newCast()[0], newCast()[0], newCast(register=False)[0]
        myConfig.NETCAST_DEVICES[connectedUUID] = pytypes.SimpleNamespace(
            name='Connecté', socket_client=pytypes.SimpleNamespace(is_connected=True), status=pytypes.SimpleNamespace(volume_level=0.42))
        groupUUID = newCast('Groupe', 'group', register=False)[0]
        myConfig.NETCAST_GROUPS[groupUUID] = fakeGroup([connectedUUID, offlineUUID, missingUUID])
        group = pytypes.SimpleNamespace(uuid=groupUUID, name='Groupe')
        with self.assertLogs(level='WARNING') as logs:
            snapshot = ttscastd.Functions.getGroupSnapshot(group)
        self.assertEqual(snapshot, {connectedUUID: 0.42})
        self.assertTrue(any('not connected, volume not managed' in line for line in logs.output))
        self.assertTrue(any('not found in NETCAST_DEVICES' in line for line in logs.output))


class ListenersTest(CastLifecycleTestCase):
    def setUp(self):
        super().setUp()
        for name in ('MyCastStatusListener', 'MyMediaStatusListener', 'MyConnectionStatusListener'):
            patcher = mock.patch.object(myCast, name, FakeListener)
            patcher.start()
            self.addCleanup(patcher.stop)

    def testListenersThenConnection(self):
        uuid, chromecast = newCast()
        myConfig.GCAST_UUID.append(uuid)
        myCast._castListeners(chromecast, uuid)
        self.assertIn(uuid, myConfig.LISTENER_CAST)
        self.assertTrue(chromecast.socket_client.is_alive())
        myCast._castListeners(chromecast, uuid)  # second appel : pas de nouvelle inscription
        self.assertEqual(len(myConfig.LISTENER_CAST), 1)

    def testAlreadyConnectedGroupMemberStateIsPushed(self):
        uuid = newCast(register=False)[0]
        noop = lambda *args, **kwargs: None  # noqa: E731
        connected = pytypes.SimpleNamespace(
            uuid=uuid, name='Membre déjà connecté', socket_client=pytypes.SimpleNamespace(is_connected=True, is_alive=lambda: True),
            status=pytypes.SimpleNamespace(volume_level=0.3), register_status_listener=noop, register_connection_listener=noop,
            media_controller=pytypes.SimpleNamespace(register_status_listener=noop), cast_info=pytypes.SimpleNamespace(cast_type='audio'))
        myConfig.NETCAST_DEVICES[uuid] = connected
        myCast._castListeners(connected, uuid)
        self.assertIn(('castsRT::' + str(uuid), {'uuid': str(uuid), 'realtime': 1, 'status_type': 'connect', 'online': '1'}), self.comm.sent)
        self.assertEqual(myConfig.LISTENER_CAST[uuid].statuses, [connected.status])


class ReleaseTestCastTest(CastLifecycleTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(myCast, 'castRemove', staticmethod(myCast._castRemove))  # sans verrou dans les tests
        patcher.start()
        self.addCleanup(patcher.stop)

    def testTestConnectionIsClosed(self):
        uuid, chromecast = newCast('Appareil testé')
        myCast.castConnect(chromecast)
        myCast.releaseTestCast(uuid)
        self.extraCasts.append(chromecast)
        self.assertIsNot(myConfig.NETCAST_DEVICES[uuid], chromecast)
        self.assertTrue(waitUntil(lambda: not chromecast.socket_client.is_alive()))

    def testGroupMemberConnectionIsKept(self):
        uuid, chromecast = newCast('Membre de groupe')
        myConfig.NETCAST_GROUPS[object()] = fakeGroup([uuid])
        myCast.castConnect(chromecast)
        myCast.releaseTestCast(uuid)
        self.assertIs(myConfig.NETCAST_DEVICES[uuid], chromecast)
        self.assertTrue(chromecast.socket_client.is_alive())


class HostServiceTest(CastLifecycleTestCase):
    def testAddressChangeUpdatesTheSharedServicesSet(self):
        uuid, chromecast = newCast(host='192.168.2.71', port=8009)
        myConfig.IP_HOSTS[uuid] = '192.168.2.71'
        myCast.setIpHost(uuid, '192.168.2.72')
        self.assertEqual(chromecast.cast_info.services, {HostServiceInfo('192.168.2.72', 8009)})
        self.assertIs(chromecast.socket_client.services, chromecast.cast_info.services, 'ensemble partagé avec la connexion')


if __name__ == '__main__':
    unittest.main()
