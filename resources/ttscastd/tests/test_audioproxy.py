""" Proxy audio : lecture de l'en-tête HTTP Range (vraie fonction ttscast_parseRange, extraite de core/php/ttscast.audio.proxy.php
et exécutée avec PHP en ligne de commande, sans Jeedom ; le fichier n'est pas modifié).
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import json
import os
import shutil
import subprocess
import unittest

PROXY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'core', 'php', 'ttscast.audio.proxy.php'))

# Extrait la fonction du proxy (de sa signature à la première accolade fermante en début de ligne) et la définit
LOAD_FUNCTION = ("$source = file_get_contents(%s); $start = strpos($source, 'function ttscast_parseRange');"
                 " if ($start === false || !preg_match('/\\R}\\R/', $source, $m, PREG_OFFSET_CAPTURE, $start)) { echo 'KO'; exit(1); }"
                 " eval(substr($source, $start, $m[0][1] - $start) . \"\\n}\");")


@unittest.skipUnless(shutil.which('php'), 'PHP non installé')
class ParseRangeTest(unittest.TestCase):
    CASES = [
        # (en-tête Range, taille, [code, premier octet, dernier octet])
        ('', 1000, [200, 0, 999]),
        ('bytes=0-', 1000, [206, 0, 999]),
        ('bytes=0-99', 1000, [206, 0, 99]),
        ('bytes=500-', 1000, [206, 500, 999]),
        ('bytes=900-5000', 1000, [206, 900, 999]),
        ('bytes=-100', 1000, [206, 900, 999]),
        ('bytes=-5000', 1000, [206, 0, 999]),
        ('bytes=1000-', 1000, [416, 0, -1]),
        ('bytes=-0', 1000, [416, 0, -1]),
        ('bytes=0-', 0, [416, 0, -1]),
        ('bytes=500-100', 1000, [200, 0, 999]),  # plage invalide : ignorée
        ('bytes=0-99,200-299', 1000, [200, 0, 999]),  # plusieurs plages : fichier entier
        ('items=0-99', 1000, [200, 0, 999]),
        ('bytes=-', 1000, [200, 0, 999]),
    ]

    def test_ranges(self):
        cases = json.dumps([[header, size] for header, size, _ in self.CASES])
        script = (LOAD_FUNCTION % json.dumps(PROXY_FILE)
                  + " $out = array(); foreach (json_decode(%s, true) as $c) { $out[] = ttscast_parseRange($c[0], $c[1]); } echo json_encode($out);"
                  % json.dumps(cases))
        results = json.loads(subprocess.run(['php', '-r', script], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(len(results), len(self.CASES))
        for (header, size, expected), result in zip(self.CASES, results):
            with self.subTest(header=header, size=size):
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
