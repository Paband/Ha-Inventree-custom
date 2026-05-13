# InvenTree Custom — Home Assistant Integration

A clean, minimal Home Assistant integration that creates sensors for **every individual part** in your InvenTree instance — with stock levels and low-stock alerts.

## Features

- ✅ One **stock level sensor** per part (e.g. `sensor.arduino_uno_stock`)
- ✅ One **low stock binary sensor** per part (e.g. `binary_sensor.arduino_uno_low_stock`)
- ✅ UI-based setup (no YAML config needed)
- ✅ Configurable polling interval
- ✅ Part attributes: name, description, IPN, category, minimum stock
- 🔜 Build/assembly tracking (coming when you're ready to scale)

---

## Installation

### Step 1 — Copy the integration

Copy the `custom_components/inventree_custom` folder into your Home Assistant config directory:

```
/config/custom_components/inventree_custom/
```

Your config directory is wherever `configuration.yaml` lives (usually `/config/` on HA OS or `/homeassistant/` on Docker).

### Step 2 — Restart Home Assistant

Go to **Settings → System → Restart**.

### Step 3 — Add the integration

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **InvenTree Custom**
4. Enter:
   - **URL**: `http://inventree.local:8000` (or your IP, e.g. `http://192.168.1.50:8000`)
   - **API Key**: Found in InvenTree under your username → API Tokens
   - **Polling interval**: How often to refresh (default: 60 seconds)

---

## Finding your API Key in InvenTree

1. Log into InvenTree
2. Click your **username** in the top right
3. Go to **Account Settings → API Tokens**
4. Create a new token and copy it

---

## What sensors get created?

For every active part in InvenTree, two entities are created:

| Entity | Type | Example |
|---|---|---|
| `sensor.<part_name>_stock` | Sensor | `sensor.arduino_uno_stock` → `14` |
| `binary_sensor.<part_name>_low_stock` | Binary Sensor | `binary_sensor.arduino_uno_low_stock` → `on` when stock ≤ minimum |

The binary sensor uses the **minimum stock** value you set on each part in InvenTree.

---

## Example Automation — Low Stock Notification

```yaml
alias: "InvenTree Low Stock Alert"
trigger:
  - platform: state
    entity_id: binary_sensor.arduino_uno_low_stock
    to: "on"
action:
  - service: notify.mobile_app
    data:
      title: "Low Stock Alert"
      message: >
        {{ state_attr('binary_sensor.arduino_uno_low_stock', 'part_name') }}
        is running low! Only
        {{ state_attr('binary_sensor.arduino_uno_low_stock', 'in_stock') }}
        left (minimum: {{ state_attr('binary_sensor.arduino_uno_low_stock', 'minimum_stock') }}).
```

---

## Troubleshooting

**"Cannot connect"** — Check your URL includes the port (`:8000` by default). Try opening `http://inventree.local:8000/api/part/` in a browser.

**"Invalid auth"** — Double-check your API key. Make sure there are no spaces.

**Sensors not appearing** — Check HA logs at **Settings → System → Logs** and filter for `inventree_custom`.

**No minimum stock alert** — Make sure you've set a minimum stock value on the part in InvenTree (Parts → edit part → Minimum Stock).
