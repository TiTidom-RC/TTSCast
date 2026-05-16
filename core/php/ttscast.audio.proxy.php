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
    // Validation stricte : MD5 hex uniquement (32 caractères [a-f0-9])
    $file = isset($_GET['file']) ? $_GET['file'] : '';
    if (!preg_match('/^[a-f0-9]{32}$/', $file)) {
        http_response_code(400);
        die();
    }

    $filePath = dirname(dirname(__DIR__)) . '/data/cache/' . $file . '.wav';

    if (!file_exists($filePath) || !is_file($filePath)) {
        http_response_code(404);
        die();
    }

    $size = filesize($filePath);
    header('Content-Type: audio/wav');
    header('Content-Length: ' . $size);
    header('Accept-Ranges: bytes');
    header('Cache-Control: no-cache, no-store');
    readfile($filePath);
    die();

} catch (Exception $e) {
    http_response_code(500);
    die();
}
