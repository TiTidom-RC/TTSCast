""" Découverte par IP : normalisation des adresses (démon et PHP), adresses interrogées par PyChromecast, commande « Découverte »,
données exportées par le Scan, recherche par IP (fenêtre « Scan (IP) »).
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t .
Tests sur appareils réels (ignorés par défaut) : définir TTSCAST_TEST_HOSTS avec des adresses d'appareils Cast du réseau, séparées
par des virgules (ex. TTSCAST_TEST_HOSTS=192.168.1.20,192.168.1.21), et optionnellement TTSCAST_TEST_HOSTNAME avec un nom d'hôte
qui se résout vers un appareil Cast. La comparaison avec le PHP nécessite php en ligne de commande (ignorée sinon). """

import json
import os
import re
import shutil
import subprocess
import types as pytypes
import unittest
from unittest import mock
from uuid import UUID

from pychromecast.models import CastInfo, HostServiceInfo, MDNSServiceInfo

import ttscastd
from tests.helpers import FakeHostBrowser, newCast, resetDaemonState, stopAllConnections

myCast = ttscastd.myCast
myConfig = ttscastd.myConfig

PHP_CLASS = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'core', 'class', 'ttscast.class.php')

# Saisie -> adresse normalisée attendue (None : refusée). Mêmes règles côté démon et côté PHP
NORMALIZE_CASES = {
    ' 192.168.2.75 ': '192.168.2.75',
    '[2a01:e0a::1]': '2a01:e0a::1',
    'fe80::1%eth0': None,                 # link-local (IPv6, avec interface)
    '169.254.1.1': None,                  # link-local (IPv4)
    'Nest-Salon.Lan.': 'nest-salon.lan',  # nom d'hôte : minuscules, point final retiré
    'nest-salon': 'nest-salon',           # nom à un seul segment (DNS local)
    'maison.duckdns.org': 'maison.duckdns.org',
    '999.1.1.1': None,                    # « fausse IP » : faute de frappe probable
    '192.168.1': None,
    '-nest.lan': None,
    'nest-.lan': None,
    'nest_salon.lan': None,
    'a..b': None,
    'a' * 64 + '.lan': None,              # segment de plus de 63 caractères
    '': None,
    'http://nest.lan': None,
    'nest.lan:8009': None,
}


class NormalizeHostTest(unittest.TestCase):
    def testDaemonRules(self):
        for typed, expected in NORMALIZE_CASES.items():
            self.assertEqual(myCast.normalizeHost(typed), expected, repr(typed))
        self.assertIsNone(myCast.normalizeHost(None))

    def testIpv4MappedAddressIsConvertedToIpv4(self):
        self.assertEqual(myCast.normalizeHost('::ffff:c0a8:249'), '192.168.2.73')

    def testIsIpAddress(self):
        self.assertTrue(myCast.isIpAddress('192.168.2.75'))
        self.assertTrue(myCast.isIpAddress('2a01:e0a::1'))
        self.assertFalse(myCast.isIpAddress('nest-salon.lan'))

    @unittest.skipUnless(shutil.which('php'), 'php non disponible')
    def testPhpRulesAreTheSame(self):
        source = open(PHP_CLASS, encoding='utf-8').read()
        function = re.search(r'public static function normalizeHostAddress\(\$_host\) \{.*?\n    \}\n', source, re.S).group(0)
        script = function.replace('public static function', 'function') + \
            '$out = array(); foreach (json_decode(stream_get_contents(STDIN), true) as $c) { $r = normalizeHostAddress($c); $out[] = ($r === false) ? null : $r; }' \
            ' echo json_encode($out);'
        output = subprocess.run(['php', '-r', script], input=json.dumps(list(NORMALIZE_CASES)), capture_output=True, text=True, check=True).stdout
        for (typed, expected), phpResult in zip(NORMALIZE_CASES.items(), json.loads(output)):
            self.assertEqual(phpResult, expected, repr(typed))


class IpHostsTest(unittest.TestCase):
    def setUp(self):
        resetDaemonState()
        self.hostBrowser = FakeHostBrowser()
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(host_browser=self.hostBrowser, devices={})

    def testSharedAddressIsPolledOnceAndKeptWhileUsed(self):
        hub, group, bain = UUID(int=1), UUID(int=2), UUID(int=3)
        myCast.setIpHost(hub, '192.168.2.73')
        myCast.setIpHost(group, '::ffff:192.168.2.73')  # même appareil (le groupe qu'il héberge)
        myCast.setIpHost(bain, '192.168.2.71')
        self.hostBrowser.add_hosts(['192.168.2.66'])  # ajouté par PyChromecast lui-même (hôte d'un groupe)
        self.assertEqual(sorted(self.hostBrowser._known_hosts), ['192.168.2.66', '192.168.2.71', '192.168.2.73'])
        myCast.removeIpHost(hub)
        self.assertIn('192.168.2.73', self.hostBrowser._known_hosts)
        myCast.removeIpHost(group)
        self.assertEqual(sorted(self.hostBrowser._known_hosts), ['192.168.2.66', '192.168.2.71'])

    def testAddressChange(self):
        uuid = UUID(int=4)
        self.assertTrue(myCast.setIpHost(uuid, '192.168.2.71'))
        self.assertFalse(myCast.setIpHost(uuid, '192.168.2.71'))
        self.assertTrue(myCast.setIpHost(uuid, 'nest-bain.lan'))
        self.assertEqual(sorted(self.hostBrowser._known_hosts), ['nest-bain.lan'])

    def testInvalidAddressRemovesThePreviousOne(self):
        uuid = UUID(int=5)
        myCast.setIpHost(uuid, '192.168.2.71')
        self.assertTrue(myCast.setIpHost(uuid, '999.1.1.1'))
        self.assertNotIn(uuid, myConfig.IP_HOSTS)

    def testDisabledOptionRegistersNothing(self):
        myConfig.ipDiscoveryEnabled = False
        self.assertFalse(myCast.setIpHost(UUID(int=6), '192.168.2.50'))
        self.assertEqual(myConfig.IP_HOSTS, {})

    def testBrowserNotCreatedYet(self):
        myConfig.NETCAST_BROWSER = None
        myCast.setIpHost(UUID(int=7), '192.168.2.71')
        self.assertEqual(myCast.ipHostsList(), ['192.168.2.71'])  # transmis à la création du navigateur (mainLoop)


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        resetDaemonState()

    def tearDown(self):
        stopAllConnections()

    def testDiscoveryValues(self):
        uuid, chromecast = newCast()
        services = {MDNSServiceInfo('Google-Nest-Mini-x._googlecast._tcp.local.'), HostServiceInfo('192.168.2.71', 8009)}
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={uuid: pytypes.SimpleNamespace(services=services)})
        self.assertEqual(myCast.discoveryOf(chromecast), 'mDNS + IP')
        myConfig.NETCAST_BROWSER.devices[uuid].services = {MDNSServiceInfo('x')}
        self.assertEqual(myCast.discoveryOf(chromecast), 'mDNS')
        myConfig.NETCAST_BROWSER.devices[uuid].services = set()
        self.assertEqual(myCast.discoveryOf(chromecast), 'Aucun')

    def testDeviceNotYetSeenByTheBrowser(self):
        _, chromecast = newCast()  # ajouté par la recherche par IP : chemins de l'objet lui-même
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={})
        self.assertEqual(myCast.discoveryOf(chromecast), 'IP')


class ScanDataTest(unittest.TestCase):
    """ Le Scan exporte les informations à jour du navigateur, pas cast_info (figé à la création de l'objet) """

    def setUp(self):
        resetDaemonState()

    def tearDown(self):
        stopAllConnections()

    def testBrowserInformationIsExported(self):
        uuid, chromecast = newCast(name='Ancien nom', host='192.168.2.71', port=8009)
        renamed = CastInfo({MDNSServiceInfo('x')}, uuid, 'Google Nest Mini', 'Nouveau nom', '192.168.2.80', 8009, 'audio', 'Google Inc.')
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={uuid: renamed})
        data = myCast.scanDataOf(chromecast, '29/10/2026 - 12:00:00')
        self.assertEqual((data['friendly_name'], data['host'], data['model_name'], data['manufacturer']),
                         ('Nouveau nom', '192.168.2.80', 'Google Nest Mini', 'Google Inc.'))
        self.assertEqual((data['uuid'], data['updatedBy'], data['scanmode']), (str(uuid), 'mdns', 1))

    def testMissingBrowserValuesFallBackToTheObject(self):
        # Modèle inconnu de PyChromecast (type et fabricant à None dans le navigateur), nom absent de l'annonce mDNS
        uuid, chromecast = newCast(name='Nom connu', castType='cast', host='192.168.2.71', port=8009)
        partial = CastInfo({MDNSServiceInfo('x')}, uuid, 'Modèle exotique', None, '192.168.2.80', 8009, None, None)
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={uuid: partial})
        data = myCast.scanDataOf(chromecast, '')
        self.assertEqual((data['friendly_name'], data['cast_type'], data['manufacturer'], data['host']), ('Nom connu', 'cast', 'Test', '192.168.2.80'))

    def testDeviceNotSeenByTheBrowser(self):
        _, chromecast = newCast(name='Par IP', host='192.168.2.71', port=8009)
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={})
        self.assertEqual((myCast.scanDataOf(chromecast, '')['friendly_name'], myCast.scanDataOf(chromecast, '')['host']), ('Par IP', '192.168.2.71'))


class SyncDataTest(unittest.TestCase):
    """ Synchronisation des fiches : champs du Scan toujours fournis, adresse seulement si elle est fiable et utile """

    OLD, NEW = '192.168.2.20', '192.168.2.35'

    def setUp(self):
        resetDaemonState()
        self.hostBrowser = FakeHostBrowser()
        self.uuid, self.chromecast = newCast(name='Salon', host=self.OLD, port=8009)

    def tearDown(self):
        stopAllConnections()

    def browse(self, *services):
        info = CastInfo(set(services), self.uuid, 'Google Nest Mini', 'Salon renommé', self.NEW, 8009, 'audio', 'Google Inc.')
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(host_browser=self.hostBrowser, devices={self.uuid: info})

    def failures(self, count):
        self.hostBrowser._known_hosts[self.OLD] = pytypes.SimpleNamespace(failcount=count)

    def testMdnsWithoutIpDiscovery(self):
        myConfig.ipDiscoveryEnabled = False
        self.browse(MDNSServiceInfo('x'))
        sync = myCast.syncDataOf(self.chromecast)
        self.assertEqual((sync['host'], sync['friendly_name'], sync['port']), (self.NEW, 'Salon renommé', 8009))

    def testFicheAddressStillAnswering(self):
        myCast.setIpHost(self.uuid, self.OLD)
        self.browse(MDNSServiceInfo('x'), HostServiceInfo(self.OLD, 8009))
        self.failures(0)
        self.assertNotIn('host', myCast.syncDataOf(self.chromecast))

    def testFicheAddressNotPolledYet(self):
        # Démarrage du démon : adresse pas encore interrogée, elle ne doit pas être remplacée
        myCast.setIpHost(self.uuid, self.OLD)
        self.browse(MDNSServiceInfo('x'))
        self.hostBrowser._known_hosts.pop(self.OLD, None)
        self.assertNotIn('host', myCast.syncDataOf(self.chromecast))

    def testFicheAddressDead(self):
        myCast.setIpHost(self.uuid, self.OLD)
        self.browse(MDNSServiceInfo('x'))
        self.failures(ttscastd.HOSTLISTENER_MAX_FAIL)
        self.assertEqual(myCast.syncDataOf(self.chromecast)['host'], self.NEW)

    def testFicheWithoutAddress(self):
        self.browse(MDNSServiceInfo('x'))
        self.assertEqual(myCast.syncDataOf(self.chromecast)['host'], self.NEW)

    def testIpOnlyDeviceGivesNoAddress(self):
        myCast.setIpHost(self.uuid, self.OLD)
        self.browse(HostServiceInfo(self.NEW, 8009))
        self.failures(ttscastd.HOSTLISTENER_MAX_FAIL)
        sync = myCast.syncDataOf(self.chromecast)
        self.assertNotIn('host', sync)
        self.assertEqual(sync['friendly_name'], 'Salon renommé')


def fakeDeviceInfo(uuid, name, multizone=True):
    return pytypes.SimpleNamespace(uuid=uuid, friendly_name=name, model_name='Google Nest Mini', manufacturer='Google Inc.',
                                   cast_type='audio', multizone_supported=multizone)


def fakeGroup(uuid, name, host, port):
    return pytypes.SimpleNamespace(uuid=uuid, friendly_name=name, host=host, port=port)


class SearchHostsTest(unittest.TestCase):
    def setUp(self):
        resetDaemonState()

    def tearDown(self):
        stopAllConnections()

    def testDisabledOption(self):
        myConfig.ipDiscoveryEnabled = False
        self.assertEqual(myCast.searchHosts(['192.168.2.71']), {'error': 'disabled', 'devices': [], 'errors': [], 'groupsNotAdded': []})

    def testInvalidAndUnresolvedInputs(self):
        result = myCast.searchHosts(['fe80::1', '999.1.1.1', 'nom-inexistant.invalid'])
        reasons = {r['input']: r['reason'] for r in result['errors']}
        self.assertEqual(reasons, {'fe80::1': 'invalid', '999.1.1.1': 'invalid', 'nom-inexistant.invalid': 'unresolved'})
        self.assertEqual(result['devices'], [])

    def testGroupRule(self):
        """ Groupe hébergé à l'adresse saisie (port fourni) : ajouté avec cette adresse ; hébergé ailleurs : signalé seulement ;
        paire stéréo (sans hôte) : ignorée ; appareil saisi sous deux adresses : un seul résultat """
        hub, bain, local, remote, stereo = UUID(int=11), UUID(int=12), UUID(int=21), UUID(int=22), UUID(int=23)
        infos = {
            '192.168.2.73': fakeDeviceInfo(hub, 'Hub'),
            '::ffff:192.168.2.73': fakeDeviceInfo(hub, 'Hub'),
            '192.168.2.71': fakeDeviceInfo(bain, 'Bain', multizone=False),
            '192.168.2.99': None,
        }
        multizone = pytypes.SimpleNamespace(
            dynamic_groups=[],
            groups=[fakeGroup(local, 'Maison', '192.168.2.73', 32187), fakeGroup(remote, 'Étage', '192.168.2.66', None),
                    fakeGroup(stereo, 'Paire', None, None)])
        with mock.patch.object(ttscastd, 'get_device_info', side_effect=lambda host, **kw: infos[host]), \
                mock.patch.object(ttscastd, 'get_multizone_status', return_value=multizone) as getMultizone, \
                mock.patch.object(myCast, '_registerHostDevice', staticmethod(lambda entry: None)):
            result = myCast.searchHosts(['192.168.2.73', '::ffff:192.168.2.73', '192.168.2.71', '192.168.2.99'])

        self.assertEqual(getMultizone.call_count, 1, 'Bain ne gère pas le multizone ; Hub dédoublonné (normalisé en IPv4)')
        devices = {d['uuid']: d for d in result['devices']}
        self.assertEqual(set(devices), {str(hub), str(bain), str(local)})
        self.assertEqual((devices[str(local)]['type'], devices[str(local)]['host'], devices[str(local)]['port']), ('group', '192.168.2.73', 32187))
        self.assertTrue(all(d['updatedBy'] == 'ip' for d in result['devices']))
        self.assertEqual(result['groupsNotAdded'], [{'uuid': str(remote), 'friendly_name': 'Étage', 'host': '192.168.2.66'}])
        self.assertEqual(result['errors'], [{'input': '192.168.2.99', 'reason': 'noDevice'}])

    def testRunHostSearchSendsTheReport(self):
        sent = []
        with mock.patch.object(myCast, 'searchHosts', staticmethod(lambda inputs: {'devices': [], 'errors': [], 'groupsNotAdded': []})), \
                mock.patch.object(ttscastd.Comm, 'sendToJeedom', pytypes.SimpleNamespace(send_change_immediate=sent.append), create=True):
            myCast.runHostSearch('abc', ['192.168.2.71'])
        self.assertEqual(sent, [{'hostSearch': {'devices': [], 'errors': [], 'groupsNotAdded': [], 'searchId': 'abc'}}])

    def testRunHostSearchReportsAnException(self):
        sent = []
        with mock.patch.object(myCast, 'searchHosts', staticmethod(mock.Mock(side_effect=RuntimeError('boom')))), \
                mock.patch.object(ttscastd.Comm, 'sendToJeedom', pytypes.SimpleNamespace(send_change_immediate=sent.append), create=True):
            myCast.runHostSearch('abc', [])
        self.assertEqual(sent[0]['hostSearch']['error'], 'exception')
        self.assertEqual(sent[0]['hostSearch']['searchId'], 'abc')

    @unittest.skipUnless(os.environ.get('TTSCAST_TEST_HOSTS'), 'TTSCAST_TEST_HOSTS non défini (adresses d\'appareils Cast réels)')
    def testRealDevices(self):
        hosts = [h.strip() for h in os.environ['TTSCAST_TEST_HOSTS'].split(',') if h.strip()]
        result = myCast.searchHosts(hosts + hosts[:1])  # doublon volontaire
        found = result['devices']
        self.assertTrue(found, result)
        self.assertEqual(len({d['uuid'] for d in found}), len(found), 'résultats dédoublonnés par UUID')
        for device in found:
            self.assertIn(device['type'], ('device', 'group'))
            self.assertIn(device['host'], [myCast.normalizeHost(h) for h in hosts], 'seules les adresses saisies sont retenues')
            self.assertTrue(device['port'])
            self.assertIn(UUID(device['uuid']), myConfig.NETCAST_DEVICES, 'ajouté aux appareils connus')
        for device in (d for d in found if d['type'] == 'group'):
            self.assertNotEqual(device['port'], 8009, 'port propre au groupe')

    @unittest.skipUnless(os.environ.get('TTSCAST_TEST_HOSTNAME'), 'TTSCAST_TEST_HOSTNAME non défini (nom d\'hôte d\'un appareil Cast réel)')
    def testRealDeviceByHostname(self):
        hostname = myCast.normalizeHost(os.environ['TTSCAST_TEST_HOSTNAME'])
        result = myCast.searchHosts([hostname])
        device = next((d for d in result['devices'] if d['type'] == 'device'), None)
        self.assertIsNotNone(device, result)
        self.assertEqual(device['host'], hostname, 'adresse conservée sous forme de nom')
        chromecast = myConfig.NETCAST_DEVICES[UUID(device['uuid'])]
        myCast.castConnect(chromecast, timeout=15)  # connexion Cast par le nom (résolu par le système)
        self.assertTrue(chromecast.socket_client.is_connected)


if __name__ == '__main__':
    unittest.main()
