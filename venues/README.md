# CAC Venues Accordion Builder

A clean, static-build pipeline designed to compile structured venue cluster information from a local CSV file into an interactive, touch-friendly, glassmorphic accordion component on a static HTML page.

This repository decouples content management (CSV) from layout rendering (HTML/JS), allowing non-technical collaborators to update NUS venue listings easily without altering layout source code.

---

## Architecture & Data Flow

The build tool uses Python to parse tabular CSV records, parse double-semicolon delimited tags (`;;`), and directly overwrite/inject an inline JavaScript array literal (`const venuesData`) inside your production target HTML template.

```
                  ┌────────────┐
                  │ venues.csv │  ◄── (Manage content here)
                  └─────┬──────┘
                        │
                        ▼
             ┌──────────────────┐
             │ build_venues.py  │  ◄── (Compiles records to JS array)
             └──────────┬───────┘
                        │
     ┌──────────────────┼─────────────────┐
     ▼                  ▼                 ▼
[Search Template]  [Find Array]    [Overwrite Template]
   venue.html ──►  const venuesData ──►  venue.html (Updated)


```

1. **Content Management (`venues.csv`)**: Maintain venue clusters, subcategories, and tagged room lists.
2. **Build Compilation (`build_venues.py`)**: Reads the CSV, parses records into child arrays, escapes variables safely into double-quoted JSON strings, and executes a Regex-based string injection.
3. **Frontend Dynamic Hydration (`venue.html`)**: The client-side DOM parsing engine takes the compiled array, groups elements by cluster, and renders frosted-glass accordion cards.

---

## Project Structure

```bash
├── Makefile               # Task automation wrapper (configures defaults & overrides)
├── build_venues.py        # Python 3 parsing and injection compiler script
├── venues.csv             # Pure data source containing venue cluster listings
└── venue.html             # Target HTML page (contains raw markup, glass styles, and JS logic)


```

---

## Getting Started

### Prerequisites

* Python 3.x (no external dependencies required; uses standard libraries `csv`, `json`, `re`, `argparse`).
* `make` utility (standard on macOS/Linux; available via Chocolatey or WSL on Windows).

### Quick Compile (Default Run)

To compile the default source configurations (`venues.csv` parsed into `venue.html`), simply run:

```bash
make venues


```

### Advanced Build Overrides

You can dynamically override variables inside the Makefile directly from the command line:

```bash
make venues CSV=custom_venues.csv HTML=templates/input.html OUT=dist/venue.html VAR=customArrayName


```

* **`CSV`**: Source file holding raw data (default: `venues.csv`)
* **`HTML`**: Input target containing the script block template (default: `venue.html`)
* **`OUT`**: Final compiled output file destination (default: `venue.html`)
* **`VAR`**: The JavaScript variable identifier to locate and replace (default: `venuesData`)

---

## Developer Integration Guide

### 1. The CSV Schema (`venues.csv`)

Your content should match the following head signatures exactly. Field ordering does not matter as the Python script handles structural alignment natively. Multiple venues within a category are grouped using a double-semicolon (`;;`) delimiter.

```csv
cluster,subcategory,venues
Yusof Ishak House (YIH),Multipurpose Rooms,Ascent;;Beacon;;Elevate;;Illuminate;;Lumina
University Cultural Centre (UCC),,Ho Bee Auditorium;;Theatre;;Dance Studio
Faculty Spaces,Science,Lecture Theatres;;Seminar Rooms;;Foyers


```

> 💡 **Note**: Leave the `subcategory` cell empty for top-level clusters without internal sub-groups.
> In text fields such as `hours`, `booking`, and `notes`, use `\n` in the CSV to insert a line break.

### 2. The HTML Injection Target (`venue.html`)

The build script is design-aware. It executes a multi-line regex check seeking the specific initialization statement: `const venuesData = [ ... ];`.

Place this array inside the `<script>` tag of your component. Your HTML template should be formatted as follows:

```html
<script>
  document.addEventListener("DOMContentLoaded", () => {
    
    // 1. JSON Array containing all active venue clusters
    const venuesData = [
      { "cluster": "Yusof Ishak House (YIH)", "subcategory": "Multipurpose Rooms", "venues": ["Ascent", "Beacon", "Elevate"] }
    ];

    // Render and interactive accordion logic ...
  });
</script>


```

> ⚠️ **Fallback Protocol**: If the regex pattern matches zero existing declarations, the script automatically catches the exception, creates a new `<script>` wrapper block, and safely injects it right before the closing `</script>` or `</body>` boundary tag in your document.

---

## Client Features & Styling Rules

* **Glassmorphism Aesthetic**: Cards feature translucent backdrop blurs (`backdrop-filter: blur(16px)`), subtle highlight borders, and elevated hover micro-interactions to match search interfaces seamlessly.
* **Smooth Accordion Physics**: Driven by CSS `grid-template-rows` (`0fr` $\rightarrow$ `1fr`) transitions, eliminating layout shifts and height hacks during expand and collapse toggles.
* **Interruption Handling**: A custom JavaScript click interceptor manages transition classes (`.closing`) to ensure `+` / `−` indicators cleanly sync during rapid toggle interactions.