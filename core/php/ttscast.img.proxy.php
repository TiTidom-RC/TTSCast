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
    require_once dirname(__FILE__) . '/../../../../core/php/core.inc.php';
    include_file('core', 'authentification', 'php');

    if (!isConnect()) {
        throw new Exception(__('401 - Accès non autorisé', __FILE__));
    }

    $url = base64_decode($_GET["img"]);
    
    // Timeout de 10 secondes et User-Agent pour éviter les blocages (ex: Wikimedia)
    $opts = [
        "http" => [
            "method" => "GET",
            "header" => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n",
            "timeout" => 10
        ]
    ];
    $context = stream_context_create($opts);
    
    $file = @file_get_contents($url, false, $context, 0, 1000000);

    // Si erreur, retourner l'image par défaut
    if ($file === false) {
        $defaultImage = dirname(__FILE__) . '/../../data/images/tts.png';
        if (file_exists($defaultImage)) {
            $file = file_get_contents($defaultImage);
            header("Content-type: image/png");
            echo $file;
        }
        die();
    }

    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $type = $finfo->buffer($file);

    if (strstr($type, 'image/')) {
        header("Content-type: {$type};");
        echo $file;
    }

    die();

} catch (Exception $e) {
    ajax::error(displayException($e), $e->getCode());
}
