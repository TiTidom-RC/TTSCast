""" Modèles Gemini proposés : option de modèle non proposé ignorée, niveau de réflexion, délai, configuration envoyée
à Gemini (thinking_level seul, sans thinking_budget ni température) et style de Gemini TTS. Aucun appel réel à Gemini.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import os
import re
import types as pytypes
import unittest
from unittest import mock

import ttscastd

TTSCast = ttscastd.TTSCast
myConfig = ttscastd.myConfig
Config = ttscastd.Config


class ConfigPatch(unittest.TestCase):
    def patchConfig(self, **settings):
        for name, value in settings.items():
            patcher = mock.patch.object(myConfig, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)


class ResolveAiModelTest(ConfigPatch):
    def setUp(self):
        self.patchConfig(aiModel='gemini-3.5-flash-lite')

    def testDefaultLevelFlashLite(self):
        self.assertEqual(TTSCast.resolveAiModelAndThinking(None, None), ('gemini-3.5-flash-lite', 'minimal', False))

    def testDefaultLevelHydrogen(self):
        self.patchConfig(aiModel='gemini-4-hydrogen')
        self.assertEqual(TTSCast.resolveAiModelAndThinking(None, None), ('gemini-4-hydrogen', 'low', False))

    def testRequestedLevel(self):
        self.assertEqual(TTSCast.resolveAiModelAndThinking(None, 'High'), ('gemini-3.5-flash-lite', 'high', True))
        self.assertEqual(TTSCast.resolveAiModelAndThinking('gemini-4-hydrogen', ' xhigh '), ('gemini-4-hydrogen', 'xhigh', True))

    def testRefusedLevelFallsBackToLowest(self):
        with self.assertLogs(level='WARNING'):
            self.assertEqual(TTSCast.resolveAiModelAndThinking('gemini-4-hydrogen', 'minimal'), ('gemini-4-hydrogen', 'low', False))
        with self.assertLogs(level='WARNING'):
            self.assertEqual(TTSCast.resolveAiModelAndThinking(None, 'xhigh'), ('gemini-3.5-flash-lite', 'minimal', False))

    def testNotProposedOptionUsesConfiguredModel(self):
        """ Option aimodel non proposée (ancien modèle d'un scénario, faute de frappe) : le modèle de la configuration est utilisé """
        self.patchConfig(aiModel='gemini-4-hydrogen')
        for model in ('gemini-3.8-flash', 'gemini-inconnu'):
            with self.subTest(model=model), self.assertLogs(level='WARNING') as logs:
                self.assertEqual(TTSCast.resolveAiModelAndThinking(model, None), ('gemini-4-hydrogen', 'low', False))
                self.assertIn('Modèle de la configuration utilisé : gemini-4-hydrogen', logs.output[0])

    def testEveryModelHasLevels(self):
        for model, levels in Config.aiModels.items():
            self.assertTrue(levels, model)


class PhpAlignmentTest(unittest.TestCase):
    """ Listes du démon alignées sur la page de configuration ; remplacements de install.php vers des modèles proposés """
    PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

    def read(self, relativePath):
        with open(os.path.join(self.PLUGIN_DIR, relativePath), encoding='utf-8') as f:
            return f.read()

    def selectOptions(self, configKey):
        page = self.read('plugin_info/configuration.php')
        select = re.search(r'data-l1key="%s">(.*?)</select>' % configKey, page, re.S).group(1)
        return re.findall(r'<option value="([^"]+)"', select)

    def phpReplacements(self, configKey):
        install = self.read('plugin_info/install.php')
        block = re.search(r"ttscast_replaceRetiredModel\('%s', array\((.*?)\)," % configKey, install, re.S).group(1)
        return dict(re.findall(r"'([^']+)' => '([^']+)'", block))

    def testConfigurationLists(self):
        self.assertEqual(set(self.selectOptions('ttsAIModel')), set(Config.aiModels))
        self.assertEqual(set(self.selectOptions('geminiTTSModel')), set(Config.geminiTTSAllowedModels))

    def testInstallReplacements(self):
        for configKey, proposed in (('ttsAIModel', Config.aiModels), ('geminiTTSModel', Config.geminiTTSAllowedModels)):
            replacements = self.phpReplacements(configKey)
            with self.subTest(configKey=configKey):
                self.assertTrue(replacements)
                for old, new in replacements.items():
                    self.assertNotIn(old, proposed)
                    self.assertIn(new, proposed)

    def testInstallProposedListAndDefault(self):
        """ Liste des modèles proposés de install.php (une autre valeur est remplacée) = celle du démon ; modèle par défaut = celui sélectionné par défaut dans la page de configuration """
        install = self.read('plugin_info/install.php')
        page = self.read('plugin_info/configuration.php')
        for configKey, proposed in (('ttsAIModel', Config.aiModels), ('geminiTTSModel', Config.geminiTTSAllowedModels)):
            match = re.search(r"ttscast_replaceRetiredModel\('%s', array\(.*?\), array\((.*?)\), '([^']+)'," % configKey, install, re.S)
            with self.subTest(configKey=configKey):
                self.assertEqual(set(re.findall(r"'([^']+)'", match.group(1))), set(proposed))
                select = re.search(r'data-l1key="%s">(.*?)</select>' % configKey, page, re.S).group(1)
                self.assertEqual(match.group(2), re.search(r'<option value="([^"]+)" selected>', select).group(1))


class ResolveGeminiTTSModelTest(ConfigPatch):
    def setUp(self):
        self.patchConfig(geminiTTSModel='gemini-3.8-flash-lite-tts')

    def testProposedAndDefault(self):
        self.assertEqual(TTSCast.resolveGeminiTTSModel('gemini-3.8-flash-tts'), 'gemini-3.8-flash-tts')
        self.assertEqual(TTSCast.resolveGeminiTTSModel(None), 'gemini-3.8-flash-lite-tts')

    def testNotProposedOptionUsesConfiguredModel(self):
        for model in ('gemini-3.1-flash-tts-preview', 'tts-inconnu'):
            with self.subTest(model=model), self.assertLogs(level='WARNING'):
                self.assertEqual(TTSCast.resolveGeminiTTSModel(model), 'gemini-3.8-flash-lite-tts')


class GeminiRequestTest(ConfigPatch):
    """ Configuration réellement transmise à client.models.generate_content (client Gemini simulé) """
    def setUp(self):
        self.patchConfig(aiAuthMode='apikey', aiApiKey='cle-de-test', gCloudApiKey='noKey', aiProjectID='noProjectID',
                         aiModel='gemini-3.5-flash-lite', aiBaseTimeout=30, aiMaxTimeout=60)
        self.calls = []

        def generate(**kwargs):
            self.calls.append(kwargs)
            return pytypes.SimpleNamespace(usage_metadata=None, candidates=None, text='Réponse reformulée')
        client = pytypes.SimpleNamespace(models=pytypes.SimpleNamespace(generate_content=generate))
        patcher = mock.patch.object(ttscastd.genai, 'Client', return_value=client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def reformulate(self, model=None, thinking=None):
        with self.assertLogs(level='WARNING'):  # usage_metadata absent du faux client
            self.assertEqual(TTSCast.genAI('Bonjour', None, None, model, thinking), 'Réponse reformulée')
        return self.calls[-1]

    def testDefaultRequest(self):
        call = self.reformulate()
        config = call['config']
        self.assertEqual(call['model'], 'gemini-3.5-flash-lite')
        self.assertEqual(config.thinking_config.thinking_level, ttscastd.types.ThinkingLevel.MINIMAL)
        self.assertIsNone(config.thinking_config.thinking_budget)
        self.assertIsNone(config.temperature)
        self.assertEqual(config.http_options.timeout, 30000)
        self.assertIsNotNone(config.system_instruction)
        self.assertTrue(config.tools[0].google_search is not None)

    def testHydrogenDefaultAndRequestedLevel(self):
        config = self.reformulate('gemini-4-hydrogen')['config']
        self.assertEqual(config.thinking_config.thinking_level, ttscastd.types.ThinkingLevel.LOW)
        self.assertEqual(config.http_options.timeout, 30000)
        config = self.reformulate('gemini-4-hydrogen', 'xhigh')['config']
        self.assertEqual(config.thinking_config.thinking_level, ttscastd.types.ThinkingLevel.XHIGH)
        self.assertEqual(config.http_options.timeout, 60000)
        self.assertIsNone(config.thinking_config.thinking_budget)
        self.assertIsNone(config.temperature)


class GeminiTTSStyleTest(ConfigPatch):
    """ Style de Gemini TTS : toujours dans speech_metadata, jamais dans le texte lu """
    def setUp(self):
        self.patchConfig(aiAuthMode='apikey', aiApiKey='cle-de-test', gCloudApiKey='noKey', aiProjectID='noProjectID',
                         geminiTTSModel='gemini-3.8-flash-lite-tts')
        self.calls = []

        def generate(**kwargs):
            self.calls.append(kwargs)
            raise RuntimeError('arrêt du test après la requête')
        client = pytypes.SimpleNamespace(models=pytypes.SimpleNamespace(generate_content=generate))
        patcher = mock.patch.object(ttscastd.genai, 'Client', return_value=client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def part(self, style):
        with self.assertLogs(level='ERROR'):
            self.assertIsNone(TTSCast.geminiTTS('Bonjour à tous', 'Achird', style))
        return self.calls[-1]['contents'][0].parts[0]

    def testStyleInSpeechMetadata(self):
        part = self.part('parle avec enthousiasme')
        self.assertEqual(part.text, 'Bonjour à tous')
        self.assertEqual(part.speech_metadata.style, 'parle avec enthousiasme')

    def testWithoutStyle(self):
        part = self.part('')
        self.assertEqual(part.text, 'Bonjour à tous')
        self.assertIsNone(part.speech_metadata)


if __name__ == '__main__':
    unittest.main()
