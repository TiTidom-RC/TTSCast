""" Utilitaires communs aux tests du démon : remise à zéro de la configuration, appareils Cast de test, faux objets.
Les appareils de test pointent vers 127.0.0.1:1 (connexion refusée immédiatement) : aucun appareil réel n'est nécessaire. """

import logging
import threading
import time
import types as pytypes
import warnings
from uuid import uuid4

import pychromecast
from pychromecast.models import CastInfo, HostServiceInfo

import ttscastd

# PyChromecast écrit ses échecs de connexion (attendus ici, l'hôte est injoignable) : sans intérêt pour les tests
logging.getLogger('pychromecast').setLevel(logging.CRITICAL)
logging.getLogger('zeroconf').setLevel(logging.CRITICAL)

UNREACHABLE_HOST = '127.0.0.1'
UNREACHABLE_PORT = 1


class FakeComm:
    """ Remplace la communication vers Jeedom (Comm.sendToJeedom) : mémorise les envois """
    def __init__(self):
        self.sent = []

    def add_changes(self, key, value):
        self.sent.append((key, dict(value)))

    def send_change_immediate(self, change):
        self.sent.append(('immediate', change))


class FakeHostBrowser:
    """ Remplace l'interrogation périodique des hôtes de PyChromecast (HostBrowser) : mêmes méthodes, sans réseau """
    def __init__(self):
        self._known_hosts = {}

    def add_hosts(self, hosts):
        for host in hosts:
            self._known_hosts.setdefault(host, object())

    def update_hosts(self, hosts):
        self.add_hosts(hosts)
        for host in list(self._known_hosts):
            if host not in hosts:
                self._known_hosts.pop(host)


def resetDaemonState():
    """ Remet l'état partagé du démon à zéro (attributs d'instance : les valeurs par défaut de Config sont des attributs de classe partagés) """
    # Chaque appareil PyChromecast crée une paire de sockets internes, fermée par son thread de connexion : celles des appareils
    # jamais connectés (nombreux ici) restent ouvertes jusqu'à la fin du processus. Sans conséquence, avertissements masqués
    # (à refaire à chaque test : le lanceur de unittest réinitialise les filtres d'avertissements)
    warnings.simplefilter('ignore', ResourceWarning)
    config = ttscastd.myConfig
    config.NETCAST_DEVICES = {}
    config.NETCAST_GROUPS = {}
    config.LISTENER_CAST = {}
    config.LISTENER_MEDIA = {}
    config.LISTENER_CONNECT = {}
    config.IP_HOSTS = {}
    config.GCAST_UUID = []
    config.NETCAST_BROWSER = None
    config.NETCAST_ZCONF = None
    config.ipDiscoveryEnabled = True
    config.IS_ENDING = False
    config.pluginSessions = {}
    ttscastd.myCast.ipHostsApplied = set()
    comm = FakeComm()
    ttscastd.Comm.sendToJeedom = comm
    return comm


def newCast(name='Appareil de test', castType='audio', host=UNREACHABLE_HOST, port=UNREACHABLE_PORT, register=True):
    """ Appareil Cast (objet PyChromecast réel, non connecté), ajouté aux appareils connus du démon si register """
    uuid = uuid4()
    castInfo = CastInfo({HostServiceInfo(host, port)}, uuid, 'Modèle de test', name, host, port, castType, 'Test')
    chromecast = pychromecast.get_chromecast_from_cast_info(castInfo, None, tries=None, retry_wait=0.3, timeout=0.5)
    if register:
        ttscastd.myConfig.NETCAST_DEVICES[uuid] = chromecast
    return uuid, chromecast


def fakeGroup(memberUUIDs):
    """ Contrôleur multizone d'un groupe actif (seule la liste des membres est utilisée), membres au format chaîne comme les annonce l'appareil """
    return pytypes.SimpleNamespace(members=[str(u) if not isinstance(u, str) else u for u in memberUUIDs])


def stopAllConnections(*extraCasts):
    """ Arrête les connexions encore actives (appareils connus + appareils passés en argument) et attend leur fin """
    casts = list(ttscastd.myConfig.NETCAST_DEVICES.values()) + list(extraCasts)
    # Seules les vraies connexions démarrées (les faux appareils des tests et les connexions jamais lancées sont ignorés)
    running = [c.socket_client for c in casts if isinstance(getattr(c, 'socket_client', None), threading.Thread) and c.socket_client.is_alive()]
    for socketClient in running:
        socketClient.disconnect()
    for socketClient in running:
        socketClient.join(timeout=3)


def waitUntil(condition, timeout=3.0):
    """ Attend qu'une condition devienne vraie (thread de connexion qui démarre / s'arrête) """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.05)
    return condition()
