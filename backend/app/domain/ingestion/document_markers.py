REFERENCE_HEADINGS = frozenset(
    {
        "references",
        "bibliography",
        "works cited",
    }
)

SOURCE_TITLE_STOP_HEADINGS = frozenset(
    {
        *REFERENCE_HEADINGS,
        "abstract",
        "acknowledgment",
        "acknowledgement",
    }
)
