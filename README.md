# xiaomi_vacuum
Home Assistant custom component for Vacuum 1C SKV4073CN (mijia.vacuum.v2).

Based on https://github.com/DavidConnack/xiaomi_vacuum

Using https://github.com/rytilahti/python-miio for the protocol.

Installation:
- Add the "xiaomi_vacuum" folder to the /config/custom_components folder
- Add the xiaomi_vacuum_card.png to /config/www/Vacuum folder
- Add sensor_xiaomi_vacuum.yaml  to /config
- Add to configuration.yaml :
```
vacuum:
  - platform: xiaomi_vacuum
    host: <ip>
    token: "<token>"
    name: <name>

sensor: !include sensor_xiaomi_vacuum.yaml
```
(To retrieve the token, follow the default integration <a href="https://www.home-assistant.io/integrations/vacuum.xiaomi_miio/#retrieving-the-access-token">instructions</a>)
- Reboot
- Add content of lovelace-card.yaml to custom card
