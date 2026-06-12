# xiaomi_vacuum

Home Assistant custom component for Vacuum 1C SKV4073CN (mijia.vacuum.v2).

Based on https://github.com/DavidConnack/xiaomi_vacuum

Using https://github.com/rytilahti/python-miio for the protocol.

## Installation

- Add the `custom_components/xiaomi_vacuum` folder to `/config/custom_components/`
- Add `xiaomi_vacuum_card.png` to `/config/www/Vacuum/`
- Add `sensor_xiaomi_vacuum.yaml` to `/config`
- Add to `configuration.yaml`:

```yaml
vacuum:
  - platform: xiaomi_vacuum
    host: <ip>
    token: "<token>"
    name: <name>

template: !include sensor_xiaomi_vacuum.yaml
```

To retrieve the token, follow the default integration [instructions](https://www.home-assistant.io/integrations/vacuum.xiaomi_miio/#retrieving-the-access-token).

- Restart Home Assistant
- Add content of `lovelace-card.yaml` to a custom card

## Home Assistant 2026.x

The component uses `VacuumEntityFeature` and `VacuumActivity` from Home Assistant 2025.10+.
Battery level is exposed as a state attribute for template sensors instead of the deprecated vacuum `battery_level` property.
