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

try {
    // Restriction réseau local uniquement (le Chromecast ne vient jamais d'une IP publique)
    // REMOTE_ADDR est l'IP TCP réelle — ne pas utiliser X-Forwarded-For (falsifiable)
    $clientIp = $_SERVER['REMOTE_ADDR'] ?? '';
    if (filter_var($clientIp, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) !== false) {
        http_response_code(403);
        die();
    }

    $mimeTypes = [
        'mp3'  => 'audio/mp3',
        'wav'  => 'audio/wav',
        'ogg'  => 'audio/ogg',
        'opus' => 'audio/ogg; codecs=opus',
        'flac' => 'audio/flac',
        'l16'  => 'audio/L16;rate=24000;channels=1',
    ];

    $type = isset($_GET['type']) ? $_GET['type'] : '';
    $file = isset($_GET['file']) ? $_GET['file'] : '';

    if ($type === 'tts') {
        // Validation stricte : MD5 hex (32 car.) + extension audio autorisée
        if (!preg_match('/^([a-f0-9]{32})\.(mp3|wav|ogg|opus|flac)$/', $file, $matches)) {
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
            http_response_code(400);
            die();
        }
        $pipePath = '/tmp/jeedom/ttscast_cache/stream/' . $safeFile;
        if (!file_exists($pipePath)) {
            http_response_code(404);
            die();
        }
        $fh = fopen($pipePath, 'rb');
        if ($fh === false) {
            http_response_code(500);
            die();
        }
        header('Content-Type: audio/L16;rate=24000;channels=1');
        header('Cache-Control: no-cache, no-store');
        header('Transfer-Encoding: chunked');
        set_time_limit(0);
        fpassthru($fh);
        fclose($fh);
        // Nettoyage du pipe (déjà supprimé par le démon Python mais au cas où)
        if (file_exists($pipePath)) {
            @unlink($pipePath);
        }
        die();

    } elseif ($type === 'sounds' || $type === 'customsounds') {
        // Validation : nom de fichier sûr (pas de séparateur de répertoire, extension autorisée)
        $safeFile = basename($file);
        if (!preg_match('/^([a-zA-Z0-9._-]+)\.(mp3|wav|ogg|opus|flac)$/', $safeFile, $matches)) {
            http_response_code(400);
            die();
        }
        $mime     = $mimeTypes[$matches[2]];
        $subDir   = ($type === 'customsounds') ? 'custom/' : '';
        $filePath = dirname(dirname(__DIR__)) . '/data/media/' . $subDir . $safeFile;

    } else {
        http_response_code(400);
        die();
    }

    if (!file_exists($filePath) || !is_file($filePath)) {
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
    http_response_code(500);
    die();
}
