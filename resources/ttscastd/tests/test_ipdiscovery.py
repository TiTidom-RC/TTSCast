""" Découverte par IP : normalisation des adresses (démon et PHP), adresses interrogées par PyChromecast, commande « Découverte »,
recherche par IP (fenêtre « Ajouter par IP »).
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
from uuid import UUID

from pychromecast.models import HostServiceInfo, MDNSServiceInfo

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


class SearchHostsTest(unittest.TestCase):
    def setUp(self):
        resetDaemonState()

    def tearDown(self):
        stopAllConnections()

    def testDisabledOption(self):
        myConfig.ipDiscoveryEnabled = False
        self.assertEqual(myCast.handleSearchHosts({'hosts': ['192.168.2.71']}), {'error': 'disabled', 'results': []})

    def testInvalidAndUnresolvedInputs(self):
        results = myCast.handleSearchHosts({'hosts': ['fe80::1', '999.1.1.1', 'nom-inexistant.invalid']})['results']
        reasons = {r['input']: r['reason'] for r in results}
        self.assertEqual(reasons, {'fe80::1': 'invalid', '999.1.1.1': 'invalid', 'nom-inexistant.invalid': 'unresolved'})

    @unittest.skipUnless(os.environ.get('TTSCAST_TEST_HOSTS'), 'TTSCAST_TEST_HOSTS non défini (adresses d\'appareils Cast réels)')
    def testRealDevices(self):
        hosts = [h.strip() for h in os.environ['TTSCAST_TEST_HOSTS'].split(',') if h.strip()]
        results = myCast.handleSearchHosts({'hosts': hosts + hosts[:1]})['results']  # doublon volontaire
        found = [r for r in results if r['type'] != 'error']
        self.assertTrue(found, results)
        self.assertEqual(len({r['uuid'] for r in found}), len(found), 'résultats dédoublonnés par UUID')
        for result in found:
            self.assertIn(result['type'], ('device', 'group'))
            self.assertTrue(result['port'])
            self.assertIn(UUID(result['uuid']), myConfig.NETCAST_DEVICES, 'ajouté aux appareils connus')
        for result in (r for r in found if r['type'] == 'group'):
            self.assertNotEqual(result['port'], 8009, 'port propre au groupe')

    @unittest.skipUnless(os.environ.get('TTSCAST_TEST_HOSTNAME'), 'TTSCAST_TEST_HOSTNAME non défini (nom d\'hôte d\'un appareil Cast réel)')
    def testRealDeviceByHostname(self):
        hostname = myCast.normalizeHost(os.environ['TTSCAST_TEST_HOSTNAME'])
        results = myCast.handleSearchHosts({'hosts': [hostname]})['results']
        device = next((r for r in results if r['type'] == 'device'), None)
        self.assertIsNotNone(device, results)
        self.assertEqual(device['host'], hostname, 'adresse conservée sous forme de nom')
        chromecast = myConfig.NETCAST_DEVICES[UUID(device['uuid'])]
        myCast.castConnect(chromecast, timeout=15)  # connexion Cast par le nom (résolu par le système)
        self.assertTrue(chromecast.socket_client.is_connected)


if __name__ == '__main__':
    unittest.main()
