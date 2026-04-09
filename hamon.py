#sudo apt install python3-qtpy fonts-dseg

import sys
import requests
from PyQt5 import QtWidgets, QtCore, QtGui

# Home Assistant base URL
HA_URL = "http://192.168.0.236:8123"

# !!! IMPORTANT !!!
# Replace this token with your own long-lived access token from Home Assistant
HA_TOKEN = "REPLACE_ME_WITH_YOUR_TOKEN"

# List of entity IDs to display
# Replace all ENTITY_IDS with valid Home Assistant entity IDs
ENTITY_IDS = [
    "REPLACE.sensor_1", "REPLACE.sensor_2",
    "REPLACE.sensor_3", "REPLACE.sensor_4",
]

# Colors for the displayed values
VALUE_COLORS = [ 
    "#FFFFFF", "#FFA500",
    "#DCE6BC", "#ADD8E6",
]

UPDATE_INTERVAL_MS = 5000  # update every 5 seconds


# --- Replace-check function ---
def validate_configuration():
    errors = []

    if "REPLACE" in HA_TOKEN or len(HA_TOKEN) < 30:
        errors.append("Please replace the default HA_TOKEN with your own long-lived access token.")

    for e in ENTITY_IDS:
        if "REPLACE" in e:
            errors.append("Please replace all ENTITY_IDS with valid Home Assistant entity IDs.")
            break

    if errors:
        print("\nCONFIGURATION ERROR:\n")
        for err in errors:
            print(" - " + err)
        print("\nProgram aborted.\n")
        sys.exit(1)


# --- Home Assistant API call ---
def get_state(entity_id):
    url = f"{HA_URL}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    data = r.json()
    return data.get("state", "n/a"), data.get("attributes", {})


class HaDisplay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: black;")
        self.labels = []
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # Font for the displayed values
        font = QtGui.QFont("DejaVu Sans", 140, QtGui.QFont.Bold)
#        font = QtGui.QFont("DSEG 7 Classic", 120, QtGui.QFont.Bold)
#        font = QtGui.QFont("DSEG 14 Classic", 120, QtGui.QFont.Bold)    

        # Create labels for each entity
        for i, entity_id in enumerate(ENTITY_IDS):
            title_label = QtWidgets.QLabel(entity_id)
            title_label.setAlignment(QtCore.Qt.AlignCenter)
            title_label.setStyleSheet("color: #EEEEEE;")

            value_label = QtWidgets.QLabel("...")
            value_label.setAlignment(QtCore.Qt.AlignCenter)
            value_label.setFont(font)
            value_label.setStyleSheet(f"color: {VALUE_COLORS[i]};")

            row = i // 2
            col = (i % 2) * 2

            layout.addWidget(title_label, row * 2, col, 1, 2)
            layout.addWidget(value_label, row * 2 + 1, col, 1, 2)

            self.labels.append((entity_id, value_label))

        # Timer for periodic updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_values)
        self.timer.start(UPDATE_INTERVAL_MS)

        self.update_values()

    def update_values(self):
        for entity_id, label in self.labels:
            try:
                state, attrs = get_state(entity_id)
                unit = attrs.get("unit_of_measurement", "")

                try:
                    # Convert float → int
                    value = int(float(state))
                    text = f"{value}"
                except:
                    # If not numeric, show raw state
                    text = f"{state}"

            except Exception:
                text = "Error"

            label.setText(text)


def main():
    validate_configuration()

    app = QtWidgets.QApplication(sys.argv)
    w = HaDisplay()
    w.setWindowTitle("Home Assistant Monitor")
    w.showFullScreen()

    # Exit on ESC key
    def keyPressEvent(event):
        if event.key() == QtCore.Qt.Key_Escape:
            app.quit()

    w.keyPressEvent = keyPressEvent

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

