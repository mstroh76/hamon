#sudo apt install python3-qtpy fonts-dseg

import argparse
import configparser
import os
import sys
import requests
from PyQt5 import QtWidgets, QtCore, QtGui

# Configuration file locations, first match wins (see hamon.conf.example)
CONFIG_PATHS = [
    os.path.expanduser("~/.config/hamon/hamon.conf"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "hamon.conf"),
    "/etc/hamon.conf",
]

COLUMNS = 2  # values per row

# Reference text used to fit the font when font_size = auto
AUTO_FIT_TEXT = "8888"


def config_error(errors):
    print("\nCONFIGURATION ERROR:\n")
    for err in errors:
        print(" - " + err)
    print("\nProgram aborted.\n")
    sys.exit(1)


# --- Load and check the configuration file ---
def load_configuration(path=None):
    if path is None:
        path = next((p for p in CONFIG_PATHS if os.path.isfile(p)), None)
        if path is None:
            config_error(
                ["No configuration file found. Copy hamon.conf.example to one of:"]
                + ["     " + p for p in CONFIG_PATHS]
            )
    elif not os.path.isfile(path):
        config_error([f"Configuration file not found: {path}"])

    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error as e:
        config_error([f"Cannot read {path}: {e}"])

    errors = []
    cfg = {}

    cfg["url"] = parser.get("homeassistant", "url", fallback="").rstrip("/")
    if not cfg["url"]:
        errors.append("Please set 'url' in section [homeassistant].")

    cfg["token"] = parser.get("homeassistant", "token", fallback="")
    if "REPLACE" in cfg["token"] or len(cfg["token"]) < 30:
        errors.append("Please replace the default token with your own long-lived access token.")

    try:
        cfg["update_interval_ms"] = parser.getint("display", "update_interval_ms", fallback=2000)
        if cfg["update_interval_ms"] <= 0:
            raise ValueError
    except ValueError:
        errors.append("'update_interval_ms' must be a positive number of milliseconds.")

    cfg["font_family"] = parser.get("display", "font_family", fallback="DejaVu Sans")

    font_size = parser.get("display", "font_size", fallback="auto").strip().lower()
    if font_size == "auto":
        cfg["font_size"] = None
    else:
        try:
            cfg["font_size"] = int(font_size)
            if cfg["font_size"] <= 0:
                raise ValueError
        except ValueError:
            errors.append("'font_size' must be a positive number or 'auto'.")

    try:
        cfg["font_bold"] = parser.getboolean("display", "font_bold", fallback=True)
    except ValueError:
        errors.append("'font_bold' must be yes or no.")

    # List of (entity_id, color) in the order of the configuration file
    cfg["entities"] = list(parser.items("entities")) if parser.has_section("entities") else []
    if not cfg["entities"]:
        errors.append("Please define at least one entity in section [entities].")

    for entity_id, color in cfg["entities"]:
        if "replace" in entity_id.lower():
            errors.append("Please replace all entity IDs with valid Home Assistant entity IDs.")
            break

    for entity_id, color in cfg["entities"]:
        if not QtGui.QColor.isValidColor(color):
            errors.append(f"Invalid color '{color}' for entity '{entity_id}'.")

    if errors:
        config_error([f"In {path}:"] + errors)

    return cfg


# --- Home Assistant API call ---
def get_state(cfg, entity_id):
    url = f"{cfg['url']}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    data = r.json()
    return data.get("state", "n/a"), data.get("attributes", {})


class HaDisplay(QtWidgets.QWidget):
    def __init__(self, cfg):
        super().__init__()

        self.cfg = cfg
        self.setStyleSheet("background-color: black;")
        self.labels = []
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # Font for the displayed values
        self.value_font = QtGui.QFont(cfg["font_family"])
        self.value_font.setBold(cfg["font_bold"])
        if cfg["font_size"] is not None:
            self.value_font.setPointSize(cfg["font_size"])

        # Create labels for each entity
        for i, (entity_id, color) in enumerate(cfg["entities"]):
            title_label = QtWidgets.QLabel(entity_id)
            title_label.setAlignment(QtCore.Qt.AlignCenter)
            title_label.setStyleSheet("color: #EEEEEE;")

            value_label = QtWidgets.QLabel("...")
            value_label.setAlignment(QtCore.Qt.AlignCenter)
            value_label.setFont(self.value_font)
            value_label.setStyleSheet(f"color: {color};")
            # The cell size defines the space for the value, not the font size
            value_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

            row = i // COLUMNS
            col = i % COLUMNS

            layout.addWidget(title_label, row * 2, col)
            layout.addWidget(value_label, row * 2 + 1, col)
            layout.setRowStretch(row * 2 + 1, 1)
            layout.setColumnStretch(col, 1)

            self.labels.append((entity_id, value_label))

        # Timer for periodic updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_values)
        self.timer.start(cfg["update_interval_ms"])

        self.update_values()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.cfg["font_size"] is None:
            # Fit after the layout has assigned the new cell sizes
            QtCore.QTimer.singleShot(0, self.fit_font)

    def fit_font(self):
        # Largest font size at which AUTO_FIT_TEXT fits into a value cell
        cell = self.labels[0][1].size()
        font = QtGui.QFont(self.value_font)
        low, high = 8, 2000
        while low < high:
            size = (low + high + 1) // 2
            font.setPixelSize(size)
            fm = QtGui.QFontMetrics(font)
            if fm.horizontalAdvance(AUTO_FIT_TEXT) <= cell.width() and fm.height() <= cell.height():
                low = size
            else:
                high = size - 1

        self.value_font.setPixelSize(low)
        for entity_id, label in self.labels:
            label.setFont(self.value_font)

    def update_values(self):
        for entity_id, label in self.labels:
            try:
                state, attrs = get_state(self.cfg, entity_id)
                unit = attrs.get("unit_of_measurement", "")

                try:
                    # Convert float → int
                    value = int(float(state))
                    text = f"{value}"
                except:
                    # If not numeric, show raw state
                    text = f"{state}"[:4]

            except Exception:
                text = "Err"

            label.setText(text)


def main():
    arg_parser = argparse.ArgumentParser(description="Home Assistant Monitor")
    arg_parser.add_argument("-c", "--config", help="path to the configuration file")
    args, qt_args = arg_parser.parse_known_args()

    cfg = load_configuration(args.config)

    app = QtWidgets.QApplication(sys.argv[:1] + qt_args)
    w = HaDisplay(cfg)
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
