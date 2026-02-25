"""Run a small contrast audit for the docs theme's critical color pairs."""

from __future__ import annotations

from dataclasses import dataclass


HEX_COLOR_LENGTH = 6
LINEAR_THRESHOLD = 0.03928


@dataclass(frozen=True)
class ContrastCase:
    """A foreground/background pair that must satisfy a contrast threshold."""

    name: str
    foreground: str
    background: str
    minimum: float


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    """Convert a six-digit hex color into normalized RGB channel values."""
    color = value.lstrip("#")
    if len(color) != HEX_COLOR_LENGTH:
        message = f"Unsupported color: {value}"
        raise ValueError(message)

    red = int(color[0:2], 16) / 255
    green = int(color[2:4], 16) / 255
    blue = int(color[4:6], 16) / 255
    return red, green, blue


def linearize(channel: float) -> float:
    """Convert a gamma-encoded sRGB channel into linear light."""
    if channel <= LINEAR_THRESHOLD:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """Return the relative luminance for a hex color."""
    red, green, blue = hex_to_rgb(color)
    return 0.2126 * linearize(red) + 0.7152 * linearize(green) + 0.0722 * linearize(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """Compute the WCAG contrast ratio between two colors."""
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    light = max(first, second)
    dark = min(first, second)
    return (light + 0.05) / (dark + 0.05)


CASES = [
    ContrastCase("light body text", "#2a2522", "#faf8f5", 7.0),
    ContrastCase("light links", "#0b7a5c", "#faf8f5", 4.5),
    ContrastCase("light code text", "#2a2522", "#f3efe8", 4.5),
    ContrastCase("light tabs active", "#0b7a5c", "#faf8f5", 4.5),
    ContrastCase("dark body text", "#e4dfd4", "#18222b", 7.0),
    ContrastCase("dark links", "#74ecc7", "#18222b", 4.5),
    ContrastCase("dark code text", "#edf4ee", "#293346", 4.5),
    ContrastCase("dark tabs active", "#74ecc7", "#18222b", 4.5),
    ContrastCase("header text", "#e4dfd4", "#183734", 4.5),
]


def main() -> int:
    """Print a contrast report and exit non-zero when any check fails."""
    failures: list[str] = []
    lines = ["Contrast audit", "=============="]
    for case in CASES:
        ratio = contrast_ratio(case.foreground, case.background)
        marker = "PASS" if ratio >= case.minimum else "FAIL"
        lines.append(f"{marker:>4}  {case.name:<20} {ratio:.2f}:1 (min {case.minimum:.1f})")
        if ratio < case.minimum:
            failures.append(case.name)

    if failures:
        lines.append("")
        lines.append("Failed cases:")
        lines.extend(f"- {failure}" for failure in failures)
        output = "\n".join(lines)
        print(output)  # noqa: T201
        return 1

    lines.append("")
    lines.append("All contrast checks passed.")
    output = "\n".join(lines)
    print(output)  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
