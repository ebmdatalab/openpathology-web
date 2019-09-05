RESULT_CATEGORIES = (
    (0, "Within range"),
    (-1, "Under range"),
    (1, "Over range"),
    (2, "No reference range"),
    (3, "Unparseable result"),
    (4, "Invalid sex"),
    (5, "Invalid range with direction"),
    (6, "Discarded age"),
    (7, "Invalid range"),
    (8, "No test code"),
)

MIN_RESULT_CATEGORY = min([x[0] for x in RESULT_CATEGORIES])
MAX_RESULT_CATEGORY = max([x[0] for x in RESULT_CATEGORIES])
