"""
Conservative detection of language-package markers in Authoring Tool names.

Some applications ship one build per language package and put the language in
the application name, which makes eg. 'Tool 26.4 (ENU)' and 'Tool 26.4 (ESP)'
two different Authoring Tools while they are the same product and version.

split_language() derives a language-neutral name plus a language code so that
results can be aggregated per (company, canonical_name, version).

Recognised marker forms (see the allowlists below):
- three-letter uppercase locale codes: '(ENU)', '(DEU)', '(JPN)', ...
- two-letter lowercase ISO 639-1 codes: '(de)', '(fr)', ...
- three-letter lowercase ISO 639-2/639-3 codes: '(fra)', '(fra/fre)', '(ger)', ...
- BCP 47 tags: '(de-DE)', '[pt-BR]', ...
- spelled-out language names, native or English, as a dash suffix or in
  parentheses: '- English', '- Deutsch (German)', '(French)', ...

Design rules (deliberate):
- Allowlist only; an unknown parenthesised token is NOT a language.
  This keeps eg. 'usBIM(k)', '(Build167540)', '(Industry Partner Release 2)',
  '(BETA)', '(wersja edukacyjna)' and 'Quadri<26.0>' untouched.
- End-anchored, with one exception: a three-letter uppercase locale code is
  unambiguous enough to also be recognised as a standalone token in the middle
  of a name, eg. 'Tool 2025.1 (JPN) - Add-in for Tool 2025' or
  'Tool 26.4 (ENU) 64-bit'. ISO codes and spelled-out names are end-only.
- Only the *name* is inspected - never the version or company.
- No match means: canonical name == original name, language None.
  When in doubt, do not aggregate.
- Matching (and the derived canonical name) treats non-breaking spaces as
  spaces and en/em-dashes as hyphens; unmatched names are never rewritten.
"""

import re

# Three-letter uppercase locale codes (Windows LCID style, as used by eg. Autodesk; case-sensitive).
_LCID_CODES = (
    'ENU', 'ENG', 'ENA', 'ENC',              # English variants
    'DEU', 'GER', 'DES', 'DEA',              # German variants
    'FRA', 'FRE', 'FRC', 'FRB', 'FRS',       # French variants
    'ESP', 'ESN',                            # Spanish variants
    'ITA', 'JPN', 'KOR', 'RUS',
    'CHS', 'CHT', 'ZHO', 'MAN',              # Chinese variants
    'PTB', 'PTG', 'PLK', 'POL',
    'CSY', 'CES', 'CZE',
    'HUN', 'NLD', 'NLB',
    'SVE', 'DAN', 'FIN', 'NOR', 'TRK', 'ELL',
)

# Lowercase ISO 639-1 codes (case-sensitive on purpose: '(IT)' or '(NO)' more
# likely abbreviate something else than Italian or Norwegian).
_ISO_CODES = (
    'de', 'fr', 'en', 'es', 'it', 'ja', 'nl', 'pl', 'ru', 'pt',
    'cs', 'hu', 'ko', 'sv', 'da', 'fi', 'no', 'tr', 'zh', 'el',
)

# Lowercase ISO 639-2 (bibliographic and terminology) / ISO 639-3 codes, eg.
# '(fra)', '(fre)' or the combined form '(fra/fre)'. Lowercase keeps them apart
# from the uppercase Windows-style codes above ('FRA').
_ISO3_CODES = {
    'eng': 'en', 'deu': 'de', 'ger': 'de', 'fra': 'fr', 'fre': 'fr', 'spa': 'es',
    'ita': 'it', 'jpn': 'ja', 'zho': 'zh', 'chi': 'zh', 'kor': 'ko', 'rus': 'ru',
    'por': 'pt', 'pol': 'pl', 'ces': 'cs', 'cze': 'cs', 'hun': 'hu', 'nld': 'nl',
    'dut': 'nl', 'swe': 'sv', 'dan': 'da', 'fin': 'fi', 'nor': 'no', 'tur': 'tr',
    'ell': 'el', 'gre': 'el', 'ara': 'ar', 'hin': 'hi', 'hrv': 'hr', 'isl': 'is',
    'ice': 'is', 'lit': 'lt', 'ron': 'ro', 'rum': 'ro', 'slv': 'sl', 'srp': 'sr',
}

# BCP 47 locale tags as used by the official buildingSMART translations
# (github.com/buildingSMART/IFC-translations, Crowdin locales). Not observed in
# authoring tool names so far, but they are the codes bSI itself standardises
# on and they are distinctive enough to be safe. Matched case-insensitively.
_BCP47_TAGS = (
    'ar-SA', 'cs-CZ', 'da-DK', 'de-DE', 'en-US', 'es-ES', 'fi-FI', 'fr-FR',
    'hi-IN', 'hr-HR', 'is-IS', 'it-IT', 'ja-JP', 'ko-KR', 'lt-LT', 'nl-NL',
    'no-NO', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'sl-SI', 'sv-SE', 'tr-TR',
    'zh-CN',
    # additional tags commonly emitted by exporters
    'en-GB', 'zh-TW', 'zh-Hans', 'zh-Hant', 'de-AT', 'de-CH', 'fr-CA',
)

# Spelled-out language names, native and English (dash-suffix form,
# eg. 'Autodesk Civil 3D 2024 - English', '... - Deutsch (German)').
# Longer variants are listed before their prefix ('English UK' before 'English').
_LANGUAGE_NAMES = (
    'English UK', 'English US', 'English',
    'German', 'Deutsch',
    'French', 'Français', 'Francais',
    'Spanish', 'Español', 'Espanol',
    'Italian', 'Italiano',
    'Japanese', '日本語',
    'Chinese', '简体中文', '繁體中文',
    'Korean', '한국어',
    'Russian', 'Русский',
    'Brazilian Portuguese', 'Português - Brasil',
    'Portuguese', 'Português', 'Portugues',
    'Polish', 'Polski',
    'Czech', 'Čeština',
    'Dutch', 'Nederlands',
    'Hungarian', 'Magyar',
    # languages officially translated by buildingSMART (IFC-translations repo)
    # that were not already covered above
    'Arabic', 'Chinese Simplified', 'Chinese Traditional', 'Croatian', 'Danish',
    'Finnish', 'Hindi', 'Icelandic', 'Lithuanian', 'Norwegian',
    'Portuguese, Brazilian', 'Romanian', 'Serbian', 'Slovenian', 'Swedish', 'Turkish',
)

# Every allowlisted token maps onto one normalised language code.
LANGUAGE_CODES = {
    'ENU': 'en', 'ENG': 'en', 'ENA': 'en', 'ENC': 'en', 'en': 'en',
    'English': 'en', 'English UK': 'en', 'English US': 'en',
    'DEU': 'de', 'GER': 'de', 'DES': 'de', 'DEA': 'de', 'de': 'de', 'German': 'de', 'Deutsch': 'de',
    'FRA': 'fr', 'FRE': 'fr', 'FRC': 'fr', 'FRB': 'fr', 'FRS': 'fr', 'fr': 'fr',
    'French': 'fr', 'Français': 'fr', 'Francais': 'fr',
    'ESP': 'es', 'ESN': 'es', 'es': 'es', 'Spanish': 'es', 'Español': 'es', 'Espanol': 'es',
    'ITA': 'it', 'it': 'it', 'Italian': 'it', 'Italiano': 'it',
    'JPN': 'ja', 'ja': 'ja', 'Japanese': 'ja', '日本語': 'ja',
    'KOR': 'ko', 'ko': 'ko', 'Korean': 'ko', '한국어': 'ko',
    'RUS': 'ru', 'ru': 'ru', 'Russian': 'ru', 'Русский': 'ru',
    'CHS': 'zh-hans', '简体中文': 'zh-hans',
    'CHT': 'zh-hant', '繁體中文': 'zh-hant',
    'ZHO': 'zh', 'MAN': 'zh', 'zh': 'zh', 'Chinese': 'zh',
    'PTB': 'pt', 'PTG': 'pt', 'pt': 'pt',
    'Portuguese': 'pt', 'Português': 'pt', 'Portugues': 'pt',
    'Brazilian Portuguese': 'pt', 'Português - Brasil': 'pt',
    'PLK': 'pl', 'POL': 'pl', 'pl': 'pl', 'Polish': 'pl', 'Polski': 'pl',
    'CSY': 'cs', 'CES': 'cs', 'CZE': 'cs', 'cs': 'cs', 'Czech': 'cs', 'Čeština': 'cs',
    'HUN': 'hu', 'hu': 'hu', 'Hungarian': 'hu', 'Magyar': 'hu',
    'NLD': 'nl', 'NLB': 'nl', 'nl': 'nl', 'Dutch': 'nl', 'Nederlands': 'nl',
    'SVE': 'sv', 'sv': 'sv',
    'DAN': 'da', 'da': 'da',
    'FIN': 'fi', 'fi': 'fi',
    'NOR': 'no', 'no': 'no',
    'TRK': 'tr', 'tr': 'tr',
    'ELL': 'el', 'el': 'el',
    # buildingSMART translation languages not covered above
    'Arabic': 'ar', 'Chinese Simplified': 'zh-hans', 'Chinese Traditional': 'zh-hant',
    'Croatian': 'hr', 'Danish': 'da', 'Finnish': 'fi', 'Hindi': 'hi',
    'Icelandic': 'is', 'Lithuanian': 'lt', 'Norwegian': 'no',
    'Portuguese, Brazilian': 'pt', 'Romanian': 'ro', 'Serbian': 'sr',
    'Slovenian': 'sl', 'Swedish': 'sv', 'Turkish': 'tr',
}

LANGUAGE_CODES.update(_ISO3_CODES)

# BCP 47 tags normalise onto their primary subtag, except where the region
# carries a script distinction we want to keep (Chinese).
LANGUAGE_CODES.update({tag: tag.split('-')[0].lower() for tag in _BCP47_TAGS})
LANGUAGE_CODES.update({
    'zh-CN': 'zh-hans', 'zh-Hans': 'zh-hans',
    'zh-TW': 'zh-hant', 'zh-Hant': 'zh-hant',
})

# English-name subset used for a bare trailing '(German)' / '(Brazilian Portuguese)'.
_ENGLISH_NAMES = (
    'English UK', 'English US', 'English', 'German', 'French', 'Spanish', 'Italian',
    'Japanese', 'Chinese Simplified', 'Chinese Traditional', 'Chinese', 'Korean',
    'Russian', 'Brazilian Portuguese', 'Portuguese, Brazilian', 'Portuguese',
    'Polish', 'Czech', 'Dutch', 'Hungarian',
    'Arabic', 'Croatian', 'Danish', 'Finnish', 'Hindi', 'Icelandic', 'Lithuanian',
    'Norwegian', 'Romanian', 'Serbian', 'Slovenian', 'Swedish', 'Turkish',
)

_NAMES_ALT = '|'.join(_LANGUAGE_NAMES)

_LCID_PATTERN = re.compile(
    r'^(?P<neutral>.+?)\s*\((?P<lang>' + '|'.join(_LCID_CODES) + r')\)\s*$'
)
_ISO_PATTERN = re.compile(
    r'^(?P<neutral>.+?)\s*\((?P<lang>' + '|'.join(_ISO_CODES) + r')\)\s*$'
)
_ISO3_ALT = '|'.join(_ISO3_CODES)
_ISO3_PATTERN = re.compile(
    r'^(?P<neutral>.+?)\s*\((?P<lang>' + _ISO3_ALT + r')(?:/(?:' + _ISO3_ALT + r'))?\)\s*$'
)
# BCP 47 tags are distinctive; match them case-insensitively.
_BCP47_PATTERN = re.compile(
    r'^(?P<neutral>.+?)\s*[\(\[](?P<lang>' + '|'.join(_BCP47_TAGS) + r')[\)\]]\s*$',
    re.IGNORECASE
)
_NAME_PATTERN = re.compile(
    r'^(?P<neutral>.+?)\s+-\s+(?P<lang>' + _NAMES_ALT + r')'
    r'(?:\s*\((?:' + '|'.join(_ENGLISH_NAMES) + r')\))?\s*$'
)
# Trailing parenthesised English language name, with an optional native-name
# tail before it, eg. '... - Deutsch (German)' where the native part deviates
# from _NAME_PATTERN, or a bare '... (French)'.
_ENGLISH_TAIL_PATTERN = re.compile(
    r'^(?P<neutral>.+?)(?:\s*-\s*(?:' + _NAMES_ALT + r'))?\s*'
    r'\((?P<lang>' + '|'.join(_ENGLISH_NAMES) + r')\)\s*$'
)
# Three-letter locale code as a standalone token in the middle of a name,
# followed by whitespace and more text (typically ' - <add-in name>' or ' 64-bit').
_LCID_MID_PATTERN = re.compile(
    r'^(?P<neutral>.+?)\s*\((?P<lang>' + '|'.join(_LCID_CODES) + r')\)(?P<rest>\s+\S.*)$'
)


# case-insensitive lookup for BCP 47 tags
_BCP47_CANONICAL = {tag.lower(): tag for tag in _BCP47_TAGS}


def _normalize(name):
    return (name
            .replace('\N{NO-BREAK SPACE}', ' ')
            .replace('\N{NARROW NO-BREAK SPACE}', ' ')
            .replace('\N{EN DASH}', '-')
            .replace('\N{EM DASH}', '-'))


def split_language(name):
    """
    Splits an Authoring Tool name into a language-neutral name and a
    normalised language code, eg. 'Revit 26.4.0.32 (ENU)' -> ('Revit 26.4.0.32', 'en').

    Returns (name, None) when no allowlisted language marker is found.
    """

    if not name:
        return name, None

    normalized = _normalize(name)
    for pattern in (_LCID_PATTERN, _ISO_PATTERN, _ISO3_PATTERN, _BCP47_PATTERN, _NAME_PATTERN, _ENGLISH_TAIL_PATTERN):
        match = pattern.match(normalized)
        if match:
            neutral = match.group('neutral').strip()
            # a bare language name (eg. 'Deutsch (German)') is not a product name
            if neutral and neutral not in LANGUAGE_CODES:
                token = match.group('lang')
                code = LANGUAGE_CODES.get(token) or LANGUAGE_CODES.get(_BCP47_CANONICAL.get(token.lower(), ''))
                if code:
                    return neutral, code

    match = _LCID_MID_PATTERN.match(normalized)
    if match:
        neutral = match.group('neutral').strip() + ' ' + match.group('rest').strip()
        return neutral, LANGUAGE_CODES[match.group('lang')]

    return name.strip(), None


def backfill_authoring_tools(AuthoringTool):
    """
    (Re)derives canonical_name and language_code for every Authoring Tool row
    and writes only the rows whose values change. Returns the number of rows changed.

    Intended for RunPython migrations: migration 0035 fills the fields once;
    whenever the allowlist above is extended, add a new migration that calls
    this function again with the historical model (apps.get_model(...)).
    Works with both the historical and the regular manager.
    """

    changed = 0
    for tool in AuthoringTool.objects.all().iterator():
        canonical_name, language_code = split_language(tool.name)
        if (canonical_name, language_code) != (tool.canonical_name, tool.language_code):
            AuthoringTool.objects.filter(pk=tool.pk).update(
                canonical_name=canonical_name,
                language_code=language_code,
            )
            changed += 1

    return changed
