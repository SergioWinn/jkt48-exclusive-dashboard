# ui/styles.py

from pathlib import Path


TOKENS_CSS = (Path(__file__).parent / "tokens.css").read_text(encoding="utf-8")

GLOBAL_CSS = "<style>\n" + TOKENS_CSS + """

html, body, .stApp {
    font-family: var(--font-body);
    max-width: 100%;
    overflow-x: hidden;
    overflow-x: clip;
}

body,
.stApp {
    background: var(--color-paper);
    color: var(--color-ink);
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    overflow-x: clip;
}

[data-testid="stHeader"] {
    background: var(--color-paper);
}

.block-container {
    width: 100%;
    max-width: 1480px;
    box-sizing: border-box;
    padding-top: var(--space-lg);
    padding-inline-start: max(clamp(var(--space-md), 3vw, var(--space-xl)), env(safe-area-inset-left));
    padding-inline-end: max(clamp(var(--space-md), 3vw, var(--space-xl)), env(safe-area-inset-right));
    padding-bottom: max(var(--space-2xl), env(safe-area-inset-bottom));
}

/* N9 edge-aligned operational header */
.ldp-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-lg);
    padding-block: var(--space-xs) var(--space-lg);
    border-bottom: 1px solid var(--color-rule);
    text-align: left;
}

.ldp-wordmark {
    min-width: 0;
}

.ldp-brand {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    max-width: 100%;
}

.ldp-brand-icon {
    position: relative;
    display: block;
    width: clamp(2.75rem, 5vw, 3.5rem);
    height: clamp(2.75rem, 5vw, 3.5rem);
    flex: 0 0 auto;
}

.ldp-brand-half {
    position: absolute;
    top: 18.75%;
    bottom: 18.75%;
    width: 39.1%;
}

.ldp-brand-half::after {
    position: absolute;
    top: 50%;
    width: 40%;
    aspect-ratio: 1;
    border-radius: 50%;
    background: var(--color-paper);
    content: "";
}

.ldp-brand-half-left {
    left: 10.9%;
    background: var(--color-ink);
}

.ldp-brand-half-left::after {
    left: 0;
    transform: translate(-50%, -50%);
}

.ldp-brand-half-right {
    right: 10.9%;
    background: var(--color-accent);
}

.ldp-brand-half-right::after {
    right: 0;
    transform: translate(50%, -50%);
}

.ldp-brand-star {
    position: absolute;
    inset: 25% 25%;
    clip-path: polygon(50% 0, 61% 35%, 98% 35%, 68% 57%, 79% 92%, 50% 71%, 21% 92%, 32% 57%, 2% 35%, 39% 35%);
    background: var(--color-paper);
}

.ldp-brand-dot {
    position: absolute;
    top: 27%;
    right: 16%;
    width: 9.5%;
    aspect-ratio: 1;
    border-radius: 50%;
    background: var(--color-danger);
}

.source-readout {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.ldp-title {
    margin: 0;
    min-width: 0;
    font-family: var(--font-body);
    font-size: clamp(1.35rem, 2.6vw, 2rem);
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.025em;
    overflow-wrap: anywhere;
    text-wrap: balance;
}

.ldp-subtitle {
    margin: var(--space-md) 0 0;
    max-width: 65ch;
    color: var(--color-ink-2);
    font-size: var(--text-base);
    font-weight: 400;
    line-height: 1.6;
}

.tako-btn {
    display: inline-flex;
    min-height: 44px;
    align-items: center;
    padding-inline: var(--space-md);
    border: 1px solid var(--color-rule-strong);
    border-radius: var(--radius-input);
    background: var(--color-paper);
    color: var(--color-ink) !important;
    font-size: var(--text-sm);
    font-weight: 600;
    text-decoration: none !important;
    white-space: nowrap;
    transition: opacity var(--dur-short) var(--ease-out), transform var(--dur-micro) var(--ease-out);
}

/* Event index readout */
.event-index-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-md);
    margin-top: var(--space-lg);
    padding-block: var(--space-lg) var(--space-md);
}

.event-index-head h2 {
    margin: var(--space-xs) 0 0;
    min-width: 0;
    font-family: var(--font-display);
    font-size: clamp(var(--text-xl), 4vw, var(--text-2xl));
    font-style: normal;
    font-weight: 600;
    line-height: 1.08;
    letter-spacing: -0.03em;
    overflow-wrap: anywhere;
    text-wrap: balance;
}

.event-meta {
    color: var(--color-muted);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.source-readout {
    width: 100%;
    min-width: 0;
    padding: var(--space-sm);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-input);
    background: var(--color-paper-2);
    color: var(--color-muted);
}

.source-readout strong,
.source-readout span,
.source-readout small {
    display: block;
}

.source-readout strong {
    margin-bottom: var(--space-xs);
    color: var(--color-success-ink);
}

.source-readout.is-live {
    background: var(--color-success-soft);
}

.source-readout.is-cached strong {
    color: var(--color-warning-ink);
}

.source-readout.is-cached {
    background: var(--color-warning-soft);
}

.source-readout.is-unavailable {
    background: var(--color-danger-soft);
}

.source-readout.is-unavailable strong {
    color: var(--color-ink);
}

.source-readout small {
    margin-top: var(--space-2xs);
    overflow-wrap: anywhere;
    font-size: inherit;
    letter-spacing: 0;
    text-transform: none;
}

/* Streamlit control rails */
.st-key-event_filters {
    padding-block: var(--space-md);
    border-bottom: 1px solid var(--color-rule);
}

.st-key-event_filters [data-testid="stVerticalBlockBorderWrapper"],
.st-key-summary_metrics [data-testid="stVerticalBlockBorderWrapper"] {
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
}

.st-key-event_filters [data-testid="stHorizontalBlock"],
.st-key-summary_metrics [data-testid="stHorizontalBlock"] {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-sm);
}

.st-key-event_filters [data-testid="stColumn"],
.st-key-summary_metrics [data-testid="stColumn"] {
    width: 100% !important;
    min-width: 0;
}

.st-key-summary_metrics [data-testid="stMetric"] {
    min-height: 5.5rem;
    padding: var(--space-md);
    border-top: 1px solid var(--color-rule);
    font-variant-numeric: tabular-nums;
}

.st-key-summary_metrics [data-testid="stColumn"]:first-child [data-testid="stMetric"] {
    border-top: 0;
}

.st-key-summary_metrics [data-testid="stMetricValue"] {
    max-width: 100%;
    min-width: 0;
    font-family: var(--font-display);
    color: var(--color-ink);
    font-size: clamp(var(--text-md), 2.25vw, var(--text-2xl));
    font-weight: 600;
    letter-spacing: -0.01em;
    line-height: 1.08;
    overflow: visible;
    overflow-wrap: anywhere;
    text-overflow: clip;
    white-space: pre-line;
}

.st-key-summary_metrics [data-testid="stMetricLabel"] {
    font-family: var(--font-body);
    color: var(--color-muted);
    font-size: var(--text-xs);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.metrics-scope {
    margin: var(--space-sm) var(--space-md) 0;
    color: var(--color-muted);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.summary-stat-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    margin-top: var(--space-xs);
}

.summary-stat {
    min-width: 0;
    min-height: 5.5rem;
    padding: var(--space-md);
    border-top: 1px solid var(--color-rule);
    font-variant-numeric: tabular-nums;
}

.summary-stat:first-child {
    border-top: 0;
}

.summary-stat-label {
    display: block;
    margin-bottom: var(--space-sm);
    color: var(--color-muted);
    font-family: var(--font-body);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.summary-stat strong {
    display: block;
    min-width: 0;
    color: var(--color-ink);
    font-family: var(--font-display);
    font-size: clamp(var(--text-xl), 2.5vw, var(--text-2xl));
    font-weight: 600;
    letter-spacing: 0;
    line-height: 1.08;
    overflow-wrap: anywhere;
}

.summary-stat-revenue strong {
    font-size: clamp(var(--text-md), 2.1vw, var(--text-xl));
}

.summary-stat-revenue small {
    display: block;
    margin-top: var(--space-xs);
    color: var(--color-muted);
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: 600;
    letter-spacing: 0;
    line-height: 1.35;
    overflow-wrap: anywhere;
}

.stApp div[data-baseweb="select"],
.stApp div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input {
    min-height: 44px;
    border-color: var(--color-rule-strong) !important;
    border-radius: var(--radius-input) !important;
    background: var(--color-paper) !important;
    color: var(--color-ink) !important;
    outline: 2px solid transparent;
    outline-offset: 1px;
}

.stApp div[data-baseweb="select"] > div > div {
    background: transparent !important;
}

.stApp div[data-baseweb="select"] * {
    color: var(--color-ink) !important;
}

.stApp div[data-baseweb="select"] svg {
    fill: var(--color-ink) !important;
}

[data-testid="stTextInput"] input::placeholder {
    color: var(--color-muted) !important;
    opacity: 1;
}

[data-testid="stTextInput"] input:focus-visible,
div[data-baseweb="select"]:focus-within > div {
    outline: 2px solid var(--color-focus) !important;
    outline-offset: 1px;
}

[data-testid="stTextInput"] input:disabled,
div[data-baseweb="select"][aria-disabled="true"] > div {
    cursor: not-allowed;
    opacity: 0.55;
}

[data-baseweb="checkbox"] label {
    min-height: 44px;
    align-items: center;
    color: var(--color-ink) !important;
}

[data-baseweb="checkbox"] input + div {
    background: var(--color-paper-3) !important;
    border-color: var(--color-rule-strong) !important;
}

[data-baseweb="checkbox"] input:checked + div {
    background: var(--color-accent) !important;
    border-color: var(--color-accent-strong) !important;
}

[data-baseweb="checkbox"] input:focus-visible + div {
    outline: 2px solid var(--color-focus);
    outline-offset: 2px;
}

[data-testid="stWidgetLabel"] p {
    font-family: var(--font-body);
    color: var(--color-muted);
    font-size: var(--text-xs);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

div[class*="st-key-filter_date_"] [role="radiogroup"] {
    display: flex;
    width: 100%;
    min-width: 0;
    max-width: 100%;
    flex-wrap: nowrap;
    gap: var(--space-md);
    overflow-x: auto;
    overscroll-behavior-inline: contain;
    padding-bottom: var(--space-xs);
    scroll-snap-type: inline proximity;
    scrollbar-width: none;
}

div[class*="st-key-filter_date_"],
div[class*="st-key-filter_date_"] [data-testid="stRadio"] {
    width: 100%;
    min-width: 0;
    max-width: 100%;
}

div[class*="st-key-filter_date_"] [role="radiogroup"]::-webkit-scrollbar {
    display: none;
}

div[class*="st-key-filter_date_"] [role="radiogroup"] label {
    flex: 0 0 auto;
    min-height: 44px;
    align-items: center;
    scroll-snap-align: start;
    white-space: nowrap;
}

/* Session and member workbench */
.session-heading {
    margin: var(--space-md) 0 var(--space-sm);
    font-family: var(--font-display);
    font-size: var(--text-md);
    font-weight: 600;
    line-height: 1.1;
}

.session-time {
    font-family: var(--font-body);
    color: var(--color-muted);
    font-size: var(--text-xs);
    font-weight: 500;
}

.cards-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-sm);
    margin-bottom: var(--space-lg);
}

.ldp-card {
    position: relative;
    min-width: 0;
    min-height: 220px;
    padding: var(--space-sm);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-card);
    background: var(--color-surface);
    color: inherit;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    text-align: center;
    text-decoration: none !important;
}

.ldp-card.purchase-card {
    color: inherit !important;
    transition: transform var(--dur-micro) var(--ease-out);
}

.ldp-card.avail { background: var(--color-paper); }
.ldp-card.warn { background: var(--color-warning-soft); }
.ldp-card.sold { background: var(--color-danger-soft); }
.ldp-card.closed { background: var(--color-paper-2); opacity: 0.82; }

.purchase-card:focus-visible,
.tako-btn:focus-visible {
    outline: 3px solid var(--color-focus);
    outline-offset: 3px;
}

.c-identity {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
    justify-items: center;
    gap: var(--space-sm);
    margin-block: var(--space-sm);
}

.c-photo {
    width: 64px;
    height: 64px;
    aspect-ratio: 1 / 1;
    margin: 0;
    border: 1px solid var(--color-rule-strong);
    border-radius: 50%;
    background: var(--color-photo);
    display: grid;
    place-items: center;
    overflow: hidden;
}

.c-photo-image {
    display: block;
    width: 100%;
    height: 100%;
    max-width: none;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    object-position: center top;
}

.c-photo-placeholder {
    background: var(--color-paper-3);
    color: var(--color-muted);
    font-family: var(--font-display);
    font-size: var(--text-sm);
    font-weight: 600;
}

.ldp-card.sold .c-photo-image,
.ldp-card.closed .c-photo-image {
    filter: grayscale(1) brightness(0.72) contrast(0.95);
}


.c-jalur {
    width: 100%;
    min-height: 1.25rem;
    padding-inline: 0;
    overflow: hidden;
    font-family: var(--font-body);
    color: var(--color-muted);
    font-size: var(--text-xs);
    font-weight: 500;
    letter-spacing: 0.05em;
    line-height: 1.25;
    text-overflow: ellipsis;
    text-align: center;
    text-transform: uppercase;
    white-space: nowrap;
}

.c-member {
    width: 100%;
    min-width: 0;
    min-height: 2.4em;
    margin: 0;
    display: -webkit-box;
    overflow: hidden;
    font-family: var(--font-display);
    font-size: var(--text-sm);
    font-weight: 600;
    line-height: 1.2;
    overflow-wrap: normal;
    text-align: center;
    text-overflow: ellipsis;
    word-break: normal;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
}

.c-card-foot {
    width: 100%;
    margin-top: auto;
    display: block;
}

.c-stats {
    width: 100%;
    margin-bottom: var(--space-xs);
    display: flex;
    justify-content: center;
    color: var(--color-muted);
    font-family: var(--font-body);
    font-size: var(--text-xs);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

.c-stats b { margin-left: 0.2rem; font-weight: 800; }

.c-prog-btn {
    position: relative;
    width: 100%;
    min-height: 32px;
    border: 1px solid var(--color-rule-strong);
    border-radius: var(--radius-input);
    background: var(--color-surface-raised);
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

.c-prog-fill {
    position: absolute;
    inset: 0;
    z-index: 0;
    transform-origin: left center;
    transition: transform var(--dur-short) var(--ease-out);
}

.ldp-card.avail .c-prog-fill { background: var(--color-success); }
.ldp-card.warn .c-prog-fill { background: var(--color-warning); }
.ldp-card.sold .c-prog-fill { background: var(--color-danger); }
.ldp-card.closed .c-prog-fill { background: var(--color-closed); }

.c-prog-text {
    position: relative;
    z-index: 1;
    color: var(--color-ink);
    font-family: var(--font-body);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.05em;
    white-space: nowrap;
}

/* Share capture banner and fixed export layout */
.share-banner {
    padding: var(--space-md);
    border-radius: var(--radius-md);
    background: var(--color-accent-strong);
    color: var(--color-accent-ink);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-md);
    margin-bottom: var(--space-md);
}

.index-footer {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
    margin-top: var(--space-2xl);
    padding-top: var(--space-md);
    border-top: 1px solid var(--color-rule);
    color: var(--color-muted);
    font-family: var(--font-body);
    line-height: 1.6;
}

.index-footer a {
    display: inline-flex;
    align-items: center;
    color: var(--color-accent-strong);
    text-decoration: none;
    white-space: nowrap;
}

.sb-left h3 { margin: 0 0 var(--space-2xs); font-family: var(--font-display); font-size: 1.2rem; line-height: 1; overflow-wrap: anywhere; }
.sb-left p { margin: 0; font-size: 0.72rem; font-weight: 600; }
.sb-right { text-align: right; }
.sb-time { font-size: 0.7rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.sb-wm { margin-top: var(--space-2xs); font-size: var(--text-xs); font-weight: 700; letter-spacing: 0.04em; }

.capture-mode {
    width: 1080px !important;
    padding: var(--space-md) !important;
    box-sizing: border-box;
}

.capture-mode .cards-grid {
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    gap: var(--space-sm) !important;
    margin-bottom: var(--space-lg);
}

.capture-mode .ldp-card {
    min-height: 190px;
    padding: var(--space-xs);
    text-align: center;
}

.capture-mode .c-jalur {
    padding-inline: 0;
    text-align: center;
}

.capture-mode .c-photo {
    width: 56px !important;
    height: 56px !important;
}

.capture-mode .c-identity {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
    justify-items: center;
    gap: var(--space-2xs);
    margin-block: var(--space-xs);
}

.capture-mode .c-member {
    min-height: 2.4em;
    font-size: var(--text-xs);
    line-height: 1.2;
    overflow-wrap: normal;
    text-align: center;
    word-break: normal;
}

.is-search-mode .c-jalur {
    min-height: 3.5rem;
    white-space: normal;
}

.capture-mode .c-stats {
    justify-content: center;
    margin-bottom: var(--space-xs);
}

.capture-mode .c-card-foot {
    display: block;
    margin-top: auto;
}

.capture-mode .c-photo-image {
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
    object-position: center top !important;
}

.capture-mode .sb-left h3,
.capture-mode .session-heading {
    font-family: var(--font-body);
    word-spacing: 0.12em;
}

@media (min-width: 40rem) {
    div[class*="st-key-filter_date_"] [role="radiogroup"] { flex-wrap: wrap; overflow-x: visible; padding-bottom: 0; scroll-snap-type: none; }
    .st-key-event_filters [data-testid="stHorizontalBlock"] { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .summary-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .summary-stat { min-height: 7rem; border-top: 0; border-inline-start: 1px solid var(--color-rule); }
    .summary-stat:nth-child(odd) { border-inline-start: 0; }
    .st-key-summary_metrics [data-testid="stHorizontalBlock"] { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .st-key-summary_metrics [data-testid="stMetric"] { min-height: 7rem; border-top: 0; border-inline-start: 1px solid var(--color-rule); }
    .st-key-summary_metrics [data-testid="stColumn"]:first-child [data-testid="stMetric"] { border-inline-start: 0; }
    .cards-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-bottom: var(--space-xl); }
    .ldp-card { min-height: 240px; padding: var(--space-md); }
    .c-photo { width: 72px; height: 72px; }
}

@media (min-width: 48rem) {
    .ldp-header { flex-direction: row; align-items: center; }
    .event-index-head { grid-template-columns: minmax(0, 1fr) auto; align-items: end; }
    .source-readout { width: fit-content; min-width: 12rem; justify-self: end; }
    .index-footer { flex-direction: row; align-items: center; justify-content: space-between; }
}

@media (min-width: 64rem) {
    .st-key-event_filters [data-testid="stHorizontalBlock"] { grid-template-columns: minmax(0, 1.3fr) minmax(0, 2.5fr) minmax(0, 1.2fr) minmax(0, 1.2fr); }
    .summary-stat-grid { grid-template-columns: minmax(0, 0.9fr) minmax(0, 0.9fr) minmax(0, 0.9fr) minmax(0, 0.9fr) minmax(20rem, 1.45fr); }
    .summary-stat:nth-child(odd) { border-inline-start: 1px solid var(--color-rule); }
    .summary-stat:first-child { border-inline-start: 0; }
    .st-key-summary_metrics [data-testid="stHorizontalBlock"] { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .cards-grid { grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: var(--space-md); }
}

@media (hover: hover) and (pointer: fine) {
    div[data-baseweb="select"] > div:hover,
    [data-testid="stTextInput"] input:hover { background: var(--color-paper-2) !important; }
    .ldp-card.purchase-card:hover { transform: translateY(-1px); }
    .tako-btn:hover { opacity: 0.78; }
    .index-footer a:hover { text-decoration: underline; }
}

/* Scroll rhythm: the live dashboard remains immediately usable if JS is unavailable. */
.ex48-scroll-ready .ex48-reveal {
    opacity: 0;
    transform: translateY(12px);
    transition:
        opacity 420ms cubic-bezier(0.16, 1, 0.3, 1) var(--ex48-delay, 0ms),
        transform 420ms cubic-bezier(0.16, 1, 0.3, 1) var(--ex48-delay, 0ms);
}

.ex48-scroll-ready .ex48-reveal.is-inview,
.ex48-scroll-ready .ex48-reveal:focus-within {
    opacity: 1;
    transform: translateY(0);
}

.ldp-card.purchase-card:active,
.tako-btn:active {
    transform: translateY(1px);
}

.index-footer a:focus-visible {
    outline: 3px solid var(--color-focus);
    outline-offset: 3px;
}

@media (pointer: coarse) {
    .tako-btn,
    .index-footer a {
        min-height: 44px;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
    .ex48-scroll-ready .ex48-reveal {
        opacity: 1;
        transform: none;
    }
}
</style>
"""
