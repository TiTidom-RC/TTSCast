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
    '2A01:0E0A:0000::1': '2a01:e0a::1',   # forme canonique : minuscules, zéros compressés
    '::ffff:192.168.2.73': '192.168.2.73',  # IPv6 mappée ramenée en IPv4
    '::ffff:c0a8:249': '192.168.2.73',
    '0.0.0.0': None,                      # non spécifiée
    '::': None,
    '224.0.0.251': None,                  # multicast
    'ff02::1': None,
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
        with open(PHP_CLASS, encoding='utf-8') as phpClass:
            source = phpClass.read()
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

    def testGroupMovedKeepsOnlyTheRightPort(self):
        # Groupe déplacé sur une autre enceinte : PyChromecast a déjà ajouté le chemin (nouvelle enceinte, nouveau port) ;
        # le changement d'adresse retire l'ancien chemin sans en recréer un avec l'ancien port
        uuid, chromecast = newCast(host='192.168.2.73', port=32187)
        myCast.setIpHost(uuid, '192.168.2.73')
        chromecast.cast_info.services.add(HostServiceInfo('192.168.2.71', 32190))
        myCast.setIpHost(uuid, '192.168.2.71')
        self.assertEqual(chromecast.cast_info.services, {HostServiceInfo('192.168.2.71', 32190)})
        stopAllConnections()

    def testGroupMovedBeforeThePollUsesTheKnownPort(self):
        # Nouvelle adresse et nouveau port annoncés en mDNS, pas encore interrogés par PyChromecast : le chemin prend le nouveau port
        uuid, chromecast = newCast(host='192.168.2.73', port=32187)
        myCast.setIpHost(uuid, '192.168.2.73')
        myConfig.NETCAST_BROWSER.devices[uuid] = CastInfo({MDNSServiceInfo('x')}, uuid, 'Google Cast Group', 'Maison', '192.168.2.71', 32190, 'group', 'Google Inc.')
        myCast.setIpHost(uuid, '192.168.2.71')
        self.assertEqual(chromecast.cast_info.services, {HostServiceInfo('192.168.2.71', 32190)})
        stopAllConnections()

    def testAddressChangeOnPage(self):
        # Adresse modifiée sur la page : le chemin est recréé à la nouvelle adresse, même port
        uuid, chromecast = newCast(host='192.168.2.73', port=8009)
        myCast.setIpHost(uuid, '192.168.2.73')
        myCast.setIpHost(uuid, '192.168.2.80')
        self.assertEqual(chromecast.cast_info.services, {HostServiceInfo('192.168.2.80', 8009)})
        stopAllConnections()

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

    def testLinkLocalAddressIsNotExported(self):
        # IPv6 link-local annoncée passagèrement par le mDNS : adresse vide, PHP conserve l'adresse actuelle de la fiche
        uuid, chromecast = newCast(host='192.168.2.71', port=8009)
        linkLocal = CastInfo({MDNSServiceInfo('x')}, uuid, 'Google Nest Mini', 'Salon', 'fe80::1%eth0', 8009, 'audio', 'Google Inc.')
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={uuid: linkLocal})
        self.assertEqual(myCast.scanDataOf(chromecast, '')['host'], '')

    def testDeviceNotSeenByTheBrowser(self):
        _, chromecast = newCast(name='Par IP', host='192.168.2.71', port=8009)
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(devices={})
        self.assertEqual((myCast.scanDataOf(chromecast, '')['friendly_name'], myCast.scanDataOf(chromecast, '')['host']), ('Par IP', '192.168.2.71'))


class SyncDataTest(unittest.TestCase):
    """ Synchronisation des fiches (le Scan en continu) : nom, adresse et port là où l'appareil est actuellement vu """

    OLD, NEW = '192.168.2.20', '192.168.2.35'

    def setUp(self):
        resetDaemonState()
        self.uuid, self.chromecast = newCast(name='Salon', host=self.OLD, port=8009)

    def tearDown(self):
        stopAllConnections()

    def browse(self, services, host=NEW, port=8009, name='Salon renommé'):
        info = CastInfo(set(services), self.uuid, 'Google Nest Mini', name, host, port, 'audio', 'Google Inc.')
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(host_browser=FakeHostBrowser(), devices={self.uuid: info})

    def testNewAddressSeenInMdns(self):
        # DHCP : le mDNS annonce la nouvelle adresse (vaut aussi pour une TV, interrogée une seule fois par IP)
        self.browse([MDNSServiceInfo('x')])
        self.assertEqual(myCast.syncDataOf(self.chromecast), {'friendly_name': 'Salon renommé', 'host': self.NEW, 'port': 8009})

    def testGroupMovedToAnotherSpeaker(self):
        # Groupe vu uniquement par IP, désormais hébergé par une autre enceinte : adresse et port restent cohérents
        self.browse([HostServiceInfo(self.NEW, 32190)], port=32190, name='Maison')
        self.assertEqual(myCast.syncDataOf(self.chromecast), {'friendly_name': 'Maison', 'host': self.NEW, 'port': 32190})

    def testDeviceNoLongerSeen(self):
        # Appareil vu uniquement par IP dont l'adresse ne répond plus : plus aucun service, rien n'est synchronisé
        self.browse([])
        self.assertEqual(myCast.syncDataOf(self.chromecast), {})

    def testLinkLocalAddressIsOmitted(self):
        self.browse([MDNSServiceInfo('x')], host='fe80::1%eth0')
        self.assertEqual(myCast.syncDataOf(self.chromecast), {'friendly_name': 'Salon renommé'}, 'ni adresse, ni port seul')

    def testMissingNameFallsBackToTheObject(self):
        self.browse([MDNSServiceInfo('x')], name=None)
        self.assertEqual(myCast.syncDataOf(self.chromecast)['friendly_name'], 'Salon')

    def testDeviceNotYetSeenByTheBrowser(self):
        # Ajouté par le Scan (IP), pas encore vu par le navigateur : informations de l'objet lui-même
        myConfig.NETCAST_BROWSER = pytypes.SimpleNamespace(host_browser=FakeHostBrowser(), devices={})
        self.assertEqual(myCast.syncDataOf(self.chromecast), {'friendly_name': 'Salon', 'host': self.OLD, 'port': 8009})


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
            myCast.runHostSearch(['192.168.2.71'])
        self.assertEqual(sent, [{'hostSearch': {'devices': [], 'errors': [], 'groupsNotAdded': []}}])

    def testRunHostSearchReportsAnException(self):
        sent = []
        with mock.patch.object(myCast, 'searchHosts', staticmethod(mock.Mock(side_effect=RuntimeError('boom')))), \
                mock.patch.object(ttscastd.Comm, 'sendToJeedom', pytypes.SimpleNamespace(send_change_immediate=sent.append), create=True):
            myCast.runHostSearch([])
        self.assertEqual(sent[0]['hostSearch']['error'], 'exception')

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
