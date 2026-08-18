#!/usr/bin/env bash
set -e

mkdir -p config/custom_components
ln -sfn "$(pwd)/custom_components/sax_power" config/custom_components/sax_power

echo "SAX Power devcontainer bereit. Zum lokalen Testen:"
echo "  hass -c config"
echo "Dann in der HA UI unter Einstellungen > Geräte & Dienste > Integration hinzufügen -> 'SAX Power' suchen."
