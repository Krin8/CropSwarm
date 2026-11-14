"""Plain-language wording, local names and local units for display. Never changes a score."""

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ACRES_PER_HA = 2.4710538147
POUNDS_PER_KG = 2.2046226218
# Multiply a metric value by the factor to get the local unit.
FACTORS = {
    "area": {"ha": 1.0, "acre": ACRES_PER_HA},
    "depth": {"mm": 1.0, "in": 1 / 25.4},
    "nitrogen": {"kg/ha": 1.0, "kg/acre": 1 / ACRES_PER_HA, "lb/acre": POUNDS_PER_KG / ACRES_PER_HA},
}
METRIC_UNITS = {"area": "ha", "depth": "mm", "nitrogen": "kg/ha"}
# Groups a farmer reads first. Every language offered at a farm must cover them.
TRANSLATED_GROUPS = ("metrics", "presets", "flags", "glossary")


def _complete(entry, languages, where):
    missing = [code for code in languages if not isinstance(entry.get(code), str) or not entry[code].strip()]
    if missing:
        raise ValueError(f"{where} lacks wording for {missing}")


def validate_locales(data, farms, crops, metrics, presets):
    """Check the wording file against the farms, crops, metrics and presets it describes."""
    languages = data["languages"]
    if "en" not in languages:
        raise ValueError("English wording is required")
    farm_ids = {farm["farm_id"] for farm in farms}
    if set(data["farms"]) != farm_ids:
        raise ValueError("locales need exactly one entry per farm")
    used = {"en"}
    for farm_id, entry in data["farms"].items():
        if entry["language"] not in languages:
            raise ValueError(f"{farm_id} uses an unknown language")
        used.add(entry["language"])
        for kind, unit in entry["units"].items():
            if unit not in FACTORS.get(kind, {}):
                raise ValueError(f"{farm_id} has an unknown {kind} unit: {unit}")
        if set(entry["units"]) != set(FACTORS):
            raise ValueError(f"{farm_id} needs area, depth and nitrogen units")
        if unknown := set(entry["crop_names"]) - set(crops):
            raise ValueError(f"{farm_id} names unknown crops: {sorted(unknown)}")
        if entry["language"] != "en" and (missing := set(crops) - set(entry["crop_names"])):
            raise ValueError(f"{farm_id} lacks local names for: {sorted(missing)}")
        for label, names in entry["season_names"].items():
            _complete(names, ("en", entry["language"]), f"{farm_id} season {label}")
    for key, entry in data["text"].items():
        _complete(entry, ("en",), f"text {key}")
    if set(data["metrics"]) != set(metrics) or set(data["presets"]) != set(presets):
        raise ValueError("locales must describe every metric and preset")
    for name, entry in data["metrics"].items():
        _complete(entry["name"], used, f"metric {name} name")
        _complete(entry["meaning"], used, f"metric {name} meaning")
    for group in ("presets", "flags"):
        for name, entry in data[group].items():
            _complete(entry, used, f"{group} {name}")
    for index, entry in enumerate(data["glossary"]):
        _complete(entry["term"], used, f"glossary {index} term")
        _complete(entry["meaning"], used, f"glossary {index} meaning")
    return data


class Locale:
    """Wording and units for one farm. English is the fallback for any untranslated text."""

    def __init__(self, data, farm_id, language="en", local_units=True):
        self.data = data
        self.farm = data["farms"][farm_id]
        self.languages = list(dict.fromkeys(("en", self.farm["language"])))
        self.language = language if language in self.languages else "en"
        self.units = self.farm["units"] if local_units else METRIC_UNITS

    def _pick(self, entry):
        return entry.get(self.language) or entry["en"]

    def text(self, key, **values):
        return self._pick(self.data["text"][key]).format(**values)

    def metric(self, name):
        return self._pick(self.data["metrics"][name]["name"])

    def metric_meaning(self, name):
        return self._pick(self.data["metrics"][name]["meaning"]).format(currency=self.farm["currency"])

    def preset(self, name):
        return self._pick(self.data["presets"][name])

    def flag(self, name):
        entry = self.data["flags"].get(name)
        return self._pick(entry) if entry else name.replace("_", " ").capitalize() + "."

    def crop(self, crop_id, display_name):
        """Show the local crop name beside the catalog name where one is listed."""
        local = self.farm["crop_names"].get(crop_id)
        if not local:
            return display_name
        return f"{local} ({display_name})" if self.language != "en" else f"{display_name} ({local})"

    def season(self, label, window=None):
        """Local season name with the months the model uses for that season."""
        names = self.farm["season_names"].get(label)
        name = self._pick(names) if names else label.replace("_", " ").capitalize()
        if not window:
            return name
        first, last = MONTHS[window["onset_month"] - 1], MONTHS[window["cessation_month"] - 1]
        return f"{name} · {first}–{last}"

    def glossary(self, **values):
        """Terms and meanings. A translated term keeps its English form beside it."""
        rows = []
        for row in self.data["glossary"]:
            term, english = self._pick(row["term"]), row["term"]["en"]
            rows.append((term if term == english else f"{term} ({english})",
                         self._pick(row["meaning"]).format(**values)))
        return rows

    def unit(self, kind):
        return self.units[kind]

    def to_local(self, kind, value):
        return value * FACTORS[kind][self.units[kind]]

    def to_metric(self, kind, value):
        return value / FACTORS[kind][self.units[kind]]

    def metric_value(self, name, value):
        """Convert a raw metric value to the farm's units and describe that unit in plain words."""
        if name == "water":
            return self.to_local("depth", value), f"{self.unit('depth')} of water short per season"
        if name == "nitrogen":
            return (self.to_local("nitrogen", value),
                    f"{self.unit('nitrogen')} of nitrogen per season, below zero means crops use more than is left")
        return value, {"erosion": "comparison index, lower is better", "climate_fit": "share of past years",
                       "income": "comparison index, 0 to 1", "risk": "comparison index, lower is better"}[name]

    def units_summary(self, local=True):
        units = self.farm["units"] if local else METRIC_UNITS
        return ", ".join(units[kind] for kind in ("area", "depth", "nitrogen"))
