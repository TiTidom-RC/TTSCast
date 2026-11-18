""" Configuration PHP du plugin : clés API de la page de configuration chiffrées en base.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import os
import re
import unittest

PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Réglages dont le nom évoque une clé sans en être une : gCloudAPIKey est le nom du fichier JSON du compte de service
NOT_SECRETS = {'gCloudAPIKey'}


def read(relativePath):
    with open(os.path.join(PLUGIN_DIR, relativePath), encoding='utf-8') as f:
        return f.read()


class EncryptConfigKeyTest(unittest.TestCase):
    def encryptedKeys(self):
        declaration = re.search(r'public static \$_encryptConfigKey = array\((.*?)\);', read('core/class/ttscast.class.php'), re.S).group(1)
        return set(re.findall(r"'([^']+)'", declaration))

    def testApiKeysAreEncrypted(self):
        """ Toute clé API saisie dans la page de configuration est déclarée dans $_encryptConfigKey (chiffrée par le Core) """
        configKeys = set(re.findall(r'data-l1key="([^"]+)"', read('plugin_info/configuration.php')))
        apiKeys = {key for key in configKeys if re.search(r'(?i)api_?key|token|password|secret', key)} - NOT_SECRETS
        self.assertTrue(apiKeys)
        self.assertEqual(apiKeys - self.encryptedKeys(), set())

    def testEncryptedKeysExistInConfiguration(self):
        configKeys = set(re.findall(r'data-l1key="([^"]+)"', read('plugin_info/configuration.php')))
        self.assertEqual(self.encryptedKeys() - configKeys, set())


if __name__ == '__main__':
    unittest.main()
