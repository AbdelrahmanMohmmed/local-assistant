
import html
import re


def clean_for_speech(text):
    """Remove formatting that should not be spoken aloud."""
    if not text:
        return ""

    # Decode HTML entities such as &#x20; and &amp;.
    text = html.unescape(text)

    # Remove fenced code blocks' markers and inline code markers.
    text = re.sub(r"```[\w+-]*\s*", "", text)
    text = text.replace("```", "")
    text = text.replace("`", "")

    # Convert Markdown links to their readable labels.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove heading and quote markers at the start of lines.
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)

    # Remove bullet and numbered-list markers.
    text = re.sub(r"(?m)^\s*[-+*]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)

    # Remove Markdown emphasis markers.
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)[*_]([^*_]+)[*_](?!\w)", r"\1", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)

    # Remove leftover standalone formatting symbols.
    text = re.sub(r"[*_~#]", "", text)

    # Normalize whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
