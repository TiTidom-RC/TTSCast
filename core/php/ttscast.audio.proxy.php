<?php
/* This file is part of Jeedom.
 *
 * Jeedom is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Jeedom is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Jeedom. If not, see <http://www.gnu.org/licenses/>.
 */

require_once dirname(__FILE__) . '/../../../../core/php/core.inc.php';

try {
    // Protection par validation stricte des noms de fichiers (regex + identifiants imprévisibles).
    $mimeTypes = [
        'mp3'  => 'audio/mp3',
        'wav'  => 'audio/wav',
        'ogg'  => 'audio/ogg',
        'opus' => 'audio/ogg; codecs=opus',
        'flac' => 'audio/flac',
    ];

    $type = isset($_GET['type']) ? $_GET['type'] : '';
    $file = isset($_GET['file']) ? $_GET['file'] : '';

    if ($type === 'tts') {
        // Validation stricte : MD5 hex (32 car.) + extension audio autorisée
        if (!preg_match('/^([a-f0-9]{32})\.(mp3|wav|ogg|opus|flac)$/', $file, $matches)) {
            log::add('ttscast', 'warning', '[PROXY][TTS] Paramètre invalide :: file=' . $file);
            http_response_code(400);
            die();
        }
        $mime     = $mimeTypes[$matches[2]];
        $filePath = dirname(dirname(__DIR__)) . '/data/cache/' . $file;

    } elseif ($type === 'stream') {
        // Named pipe (mkfifo) — streaming PCM L16 Gemini TTS
        // Validation : UUID v4 + extension l16 uniquement
        $safeFile = basename($file);
        if (!preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.l16$/', $safeFile)) {
            log::add('ttscast', 'warning', '[PROXY][Stream] Paramètre invalide :: file=' . $file);
            http_response_code(400);
            die();
        }
        $pipePath = '/tmp/jeedom/ttscast_cache/stream/' . $safeFile;
        if (!file_exists($pipePath)) {
            log::add('ttscast', 'warning', '[PROXY][Stream] Pipe introuvable :: ' . $safeFile);
            http_response_code(404);
            die();
        }
        log::add('ttscast', 'debug', '[PROXY][Stream] Ouverture du pipe (attente writer) :: ' . $safeFile);
        $fh = fopen($pipePath, 'rb');
        if ($fh === false) {
            log::add('ttscast', 'error', '[PROXY][Stream] Échec ouverture pipe :: ' . $safeFile);
            http_response_code(500);
            die();
        }
        $streamRate     = in_array((int)($_GET['rate']     ?? 0), [8000, 16000, 22050, 24000, 44100, 48000], true) ? (int)$_GET['rate']     : 24000;
        $streamChannels = in_array((int)($_GET['channels'] ?? 0), [1, 2],                                    true) ? (int)$_GET['channels'] : 1;
        log::add('ttscast', 'debug', '[PROXY][Stream] Pipe ouvert, streaming démarré :: rate=' . $streamRate . ' | channels=' . $streamChannels);
        header('Content-Type: audio/wav'); // WAV RIFF avec header dans le stream (PCM LE 16-bit — rate/channels dans le header WAV)
        header('Cache-Control: no-cache, no-store');
        header('Transfer-Encoding: chunked');
        header('Content-Encoding: identity'); // Désactiver mod_deflate — le PCM brut ne doit pas être compressé
        set_time_limit(0);
        // Désactiver tous les buffers de sortie PHP pour un envoi en temps réel
        while (ob_get_level() > 0) {
            ob_end_clean();
        }
        // Lire le pipe et envoyer immédiatement au client (Chromecast)
        $bytesSent = 0;
        while (!feof($fh)) {
            $chunk = fread($fh, 8192);
            if ($chunk !== false && $chunk !== '') {
                echo $chunk;
                flush();
                $bytesSent += strlen($chunk);
            }
        }
        fclose($fh);
        log::add('ttscast', 'debug', '[PROXY][Stream] Terminé :: ' . $safeFile . ' | ' . $bytesSent . ' bytes envoyés');
        // Nettoyage du pipe (déjà supprimé par le démon Python mais au cas où)
        if (file_exists($pipePath)) {
            @unlink($pipePath);
        }
        die();

    } elseif ($type === 'sounds' || $type === 'customsounds') {
        // Validation : nom de fichier sûr (pas de séparateur de répertoire, extension autorisée)
        $safeFile = basename($file);
        if (!preg_match('/^([a-zA-Z0-9._-]+)\.(mp3|wav|ogg|opus|flac)$/', $safeFile, $matches)) {
            log::add('ttscast', 'warning', '[PROXY][Sounds] Paramètre invalide :: file=' . $file);
            http_response_code(400);
            die();
        }
        $mime     = $mimeTypes[$matches[2]];
        $subDir   = ($type === 'customsounds') ? 'custom/' : '';
        $filePath = dirname(dirname(__DIR__)) . '/data/media/' . $subDir . $safeFile;

    } else {
        log::add('ttscast', 'warning', '[PROXY] Type inconnu :: type=' . $type);
        http_response_code(400);
        die();
    }

    if (!file_exists($filePath) || !is_file($filePath)) {
        log::add('ttscast', 'warning', '[PROXY] Fichier non trouvé :: ' . basename($filePath));
        http_response_code(404);
        die();
    }

    $size = filesize($filePath);
    header('Content-Type: ' . $mime);
    header('Content-Length: ' . $size);
    header('Accept-Ranges: bytes');
    header('Cache-Control: no-cache, no-store');
    readfile($filePath);
    die();

} catch (Exception $e) {
    log::add('ttscast', 'error', '[PROXY] Exception :: ' . $e->getMessage());
    http_response_code(500);
    die();
}
