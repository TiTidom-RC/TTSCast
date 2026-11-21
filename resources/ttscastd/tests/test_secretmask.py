""" Masquage des secrets saisis par l'utilisateur (identifiants d'URL, jetons, mots de passe) : mêmes cas pour le démon
(SecretMaskFilter) et pour le plugin (vraie méthode ttscast::maskSecrets, extraite de core/class/ttscast.class.php et exécutée avec
PHP en ligne de commande, sans Jeedom ; le fichier n'est pas modifié).
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import json
import logging
import os
import shutil
import subprocess
import unittest

import ttscastd
from tests.test_logfilters import LoggingTestCase

MASK = 'sEcReT'
CLASS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'core', 'class', 'ttscast.class.php'))

# (texte écrit dans un log, texte attendu)
CASES = [
    ('Diffusion Media lancée :: Nest | http://user:secret@nas/Musique/a.mp3', 'Diffusion Media lancée :: Nest | http://uSeR:sEcReT@nas/Musique/a.mp3'),
    ('https://user@nas/a.mp3', 'https://uSeR@nas/a.mp3'),
    ('{"message":"http:\\/\\/user:secret@nas\\/a.mp3"}', '{"message":"http:\\/\\/uSeR:sEcReT@nas\\/a.mp3"}'),
    ('http://nas/a.mp3?token=abc123&x=1', 'http://nas/a.mp3?token=sEcReT&x=1'),
    ('http://nas/stream?api_key=XYZ', 'http://nas/stream?api_key=sEcReT'),
    ('{"password": "hunter2", "volume": 20}', '{"password": "sEcReT", "volume": 20}'),
    ("{'apikey': 'abcdef', 'ding': False}", "{'apikey': 'sEcReT', 'ding': False}"),
    ('Authorization: Bearer ya29.abc-def', 'Authorization: Bearer sEcReT'),
    # Textes ordinaires : inchangés
    ('Le mot de passe du wifi est affiché sur la box', 'Le mot de passe du wifi est affiché sur la box'),
    ('[DAEMON][GenAI] total_token_count=120 | Tokens IA :: 120', '[DAEMON][GenAI] total_token_count=120 | Tokens IA :: 120'),
    ("Options :: {'volume': 20, 'ding': False, 'app': 'bubbleupnp'}", "Options :: {'volume': 20, 'ding': False, 'app': 'bubbleupnp'}"),
    ('{"title":"\\"volume\\": 20","message":"http:\\/\\/192.168.2.82\\/a.mp3"}', '{"title":"\\"volume\\": 20","message":"http:\\/\\/192.168.2.82\\/a.mp3"}'),
    ('$options => array', '$options => array'),
]


class DaemonSecretPatternTest(LoggingTestCase):
    def test_cases(self):
        maskFilter = ttscastd.SecretMaskFilter([], MASK)
        for text, expected in CASES:
            with self.subTest(text=text):
                self.assertEqual(maskFilter._redact(text), expected)

    def test_patternsWithoutKnownSecretsInLogs(self):
        """ Masquage par motif actif même sans secret connu (aucune clé configurée) """
        self.configure(logging.DEBUG, logging.DEBUG, ttscastd.SecretMaskFilter([], MASK))
        logging.info('[DAEMON][controllerActions] Media :: Type du média non déterminé (%s)', 'http://user:secret@nas/flux?token=abc')
        output = self.stream.getvalue()
        self.assertNotIn('secret@', output)
        self.assertNotIn('token=abc', output)
        self.assertIn('http://uSeR:sEcReT@nas/flux?token=sEcReT', output)

    def test_knownSecretsStillMaskedByValue(self):
        key = 'a0195cxTOCFQ7DS4E85YFYgJjF06yJRMldD1cIfQ9WPR6el2jqyPThIqI1Fijq3B'
        self.assertEqual(ttscastd.SecretMaskFilter([key], MASK)._redact('clé : ' + key), 'clé : ' + MASK)


# Extrait la méthode de la classe (de sa signature à la première accolade fermante au niveau des méthodes) et la définit dans une classe vide
LOAD_METHOD = ("$source = file_get_contents(%s); $start = strpos($source, 'public static function maskSecrets');"
               " if ($start === false || !preg_match('/\\R    }\\R/', $source, $m, PREG_OFFSET_CAPTURE, $start)) { echo 'KO'; exit(1); }"
               " eval('class ttscast { ' . substr($source, $start, $m[0][1] - $start) . \"\\n    }\\n}\");")


@unittest.skipUnless(shutil.which('php'), 'PHP non installé')
class PhpSecretPatternTest(unittest.TestCase):
    def test_sameResultsAsDaemon(self):
        # Textes passés par l'entrée standard : dans une chaîne PHP, « $options » serait lu comme une variable
        script = (LOAD_METHOD % json.dumps(CLASS_FILE)
                  + " $out = array(); foreach (json_decode(file_get_contents('php://stdin'), true) as $t) { $out[] = ttscast::maskSecrets($t); }"
                  " echo json_encode($out);")
        results = json.loads(subprocess.run(['php', '-r', script], input=json.dumps([text for text, _ in CASES]), capture_output=True,
                                            text=True, encoding='utf-8', check=True).stdout)
        self.assertEqual(len(results), len(CASES))
        for (text, expected), result in zip(CASES, results):
            with self.subTest(text=text):
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
