# El País Opinion Scraper & BrowserStack Cross-Browser Test Suite

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Selenium 4.20+](https://img.shields.io/badge/selenium-4.20+-green.svg)](https://www.selenium.dev/)
[![pytest 8.0+](https://img.shields.io/badge/pytest-8.0+-yellow.svg)](https://docs.pytest.org/)
[![BrowserStack SDK](https://img.shields.io/badge/BrowserStack-SDK-orange.svg)](https://www.browserstack.com/)

Automated Selenium test suite that scrapes opinion articles from Spanish news outlet *El País*, downloads cover images, translates headlines to English, analyzes word frequencies, and runs in parallel across 5 desktop and mobile browser configurations on BrowserStack.

---

## Features

- **Automated Web Scraping**: Navigates the *El País* Opinion section, verifies Spanish language loading, and extracts the first 5 articles (title, body paragraphs, cover image).
- **Resilient Page Object Model**: Encapsulates page logic with explicit waits, stale element recovery, and multi-selector fallbacks for dynamic DOM elements.
- **Dual Translation Engine**: Translates Spanish headlines to English via RapidAPI (Rapid Translate API) with zero-config fallback to `deep-translator`.
- **Frequency Analysis**: Normalizes text, filters common English stopwords, and calculates word frequencies occurring more than twice across translated titles.
- **Parallel Cloud Execution**: Runs concurrently across 5 desktop and mobile browser environments using the BrowserStack Python SDK.

---

## Architecture

### 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Test_Suite["Test Suite"]
        TS["test_elpais_scraper.py"]
        UT["test_text_analyzer.py"]
    end

    subgraph POM["Page Object Model"]
        BP["BasePage"]
        OP["OpinionPage"]
        AP["ArticlePage"]
    end

    subgraph Services["Business Services"]
        TR["TranslationService\n(RapidAPI + deep-translator)"]
        TA["TextAnalyzer"]
    end

    subgraph Shared["Shared Components"]
        AM["Article Model"]
        ID["Image Downloader"]
    end

    subgraph Infrastructure["Infrastructure & Execution"]
        SW["Selenium WebDriver"]
        SDK["BrowserStack SDK"]
        BG["BrowserStack Cloud Grid"]
    end

    %% POM Inheritance
    OP -.->|inherits| BP
    AP -.->|inherits| BP

    %% Test Dependencies
    TS --> OP
    TS --> AP
    TS --> TR
    TS --> TA
    TS --> ID
    TS --> AM
    UT --> TA

    %% Execution Pipeline
    BP --> SW
    SW --> SDK
    SDK --> BG
```

The high-level architecture follows a layered design based on the Page Object Model (POM) to isolate browser automation logic from business services and test orchestration. Page objects encapsulate DOM interactions, while independent service modules handle translation API queries and word frequency analysis. The infrastructure layer leverages the BrowserStack Python SDK to intercept Selenium WebDriver instances and distribute test execution across remote cloud browser grids natively.

---

### 2. End-to-End Execution Flow

```mermaid
flowchart TD
    A([Start Execution]) --> B[Launch Browser Session via BrowserStack SDK]
    B --> C[Navigate to El País Opinion Section]
    C --> D[Dismiss GDPR Cookie Consent Banner]
    D --> E{Verify Page is in Spanish?}
    E -- No --> F[Fail Test: Non-Spanish Edition]
    E -- Yes --> G[Extract First 5 Article Links from Listing]

    subgraph Article_Loop["Article Processing Loop (First 5 Articles)"]
        G --> H[Open Article Detail Page]
        H --> I[Synchronize DOM & Validate Target URL]
        I --> J[Extract Article Headline Title]
        J --> K[Extract Body Text Paragraphs]
        K --> L[Download Cover Image with Backoff Retry]
    end

    L --> M[Translate Spanish Headlines to English]
    M --> N[Primary Engine: RapidAPI REST Endpoint]
    N -. Fallback .-> O[Secondary Engine: deep-translator]

    O & N --> P[Analyze Translated Headlines for Repeated Words]
    P --> Q[Execute Test Assertions & Log Summary]
    Q --> R[Update Session Status in BrowserStack Dashboard]
    R --> S[Generate BrowserStack Build Insights & Logs]
    S --> T([End Execution])
```

The execution flow details the sequential lifecycle of an automated scraping and analysis run from driver setup to session teardown. Synchronization barriers ensure DOM readiness before headline or body extraction, while cover image downloads execute asynchronously with retry backoffs. Following translation and frequency analysis, test results and session statuses are dynamically dispatched to the BrowserStack Automate dashboard via custom executor bindings.

---

## Repository Structure

```
browserstack-assgn/
├── .github/workflows/ci.yml   # GitHub Actions CI (linting & unit tests)
├── docs/images/               # Documentation screenshots and assets
│   ├── browserstack-dashboard.png  # Real BrowserStack dashboard execution
│   └── browserstack-build.png      # Real BrowserStack build analytics report
├── downloads/                 # Directory for scraped cover images
├── pages/                     # Page Object Model abstractions
│   ├── base_page.py           # Explicit waits, scrolling, cookie handler
│   ├── opinion_page.py        # Opinion section listing & language check
│   └── article_page.py        # Synchronized article detail page extraction
├── services/                  # Independent business services
│   ├── translator.py          # RapidAPI client with fallback translator
│   └── text_analyzer.py       # Regex tokenization & stopword filtering
├── tests/                     # Test suite
│   ├── test_elpais_scraper.py # E2E cross-browser scraping test
│   └── test_text_analyzer.py  # Unit tests for text analyzer
├── browserstack.yml           # BrowserStack SDK 5-platform matrix
├── conftest.py                # Pytest driver fixture
├── models.py                  # Article dataclass model
├── pytest.ini                 # Pytest CLI configuration & logging settings
├── requirements.txt           # Python dependencies
├── utils.py                   # Image downloader with retries & backoff
└── README.md                  # Project documentation
```

---

## Setup

### Prerequisites
- Python 3.10+
- BrowserStack account (Username and Access Key)

### Installation
```bash
git clone https://github.com/TechySan031/browserstack-elpais-opinion-scraper.git
cd browserstack-elpais-opinion-scraper

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install browserstack-sdk
```

### Environment Configuration
Copy `.env.example` to `.env` and set your BrowserStack credentials:
```env
BROWSERSTACK_USERNAME=your_username
BROWSERSTACK_ACCESS_KEY=your_key
RAPIDAPI_KEY=optional_rapidapi_key  # Falls back to deep-translator if omitted
HEADLESS=false                      # Set true for headless local runs
```

---

## Local Execution

Run unit tests:
```bash
pytest tests/test_text_analyzer.py -v
```

Run E2E test locally using Chrome:
```bash
pytest tests/test_elpais_scraper.py -v -s
```

---

## BrowserStack Execution

Execute across 5 parallel platforms via BrowserStack SDK:
```bash
browserstack-sdk pytest tests/test_elpais_scraper.py -v -s
```

---

## BrowserStack Validation

Tests executed concurrently across 5 desktop and mobile browser environments on BrowserStack Automate (**Cross-Browser Scraping Test #3**):

![BrowserStack Automate Real Dashboard](docs/images/browserstack-dashboard.png)

| Platform | OS / Device | Browser Engine | Status |
|---|---|---|---|
| **Desktop 1** | Windows 11 | Firefox 153.0 | ✅ Passed (4m 07s) |
| **Desktop 2** | Windows 11 | Chrome 150.0 | ✅ Passed (2m 46s) |
| **Desktop 3** | macOS Sonoma | Safari 17.3 | ✅ Passed (5m 50s) |
| **Mobile 1** | iPhone 15 (iOS 17.3) | Safari Mobile | ✅ Passed (1m 58s) |
| **Mobile 2** | Samsung Galaxy S24 (Android 14.0) | Chrome Mobile | ✅ Passed (6m 15s) |

Full build analytics report and 100% stability verification from the BrowserStack Insights dashboard:

![BrowserStack Build Analytics Summary](docs/images/browserstack-build.png)

---

## Design Decisions

- **Zero-Code-Change SDK Parallelization**: Utilized `browserstack.yml` to define platform matrices natively, eliminating boilerplate `webdriver.Remote` capabilities from test code.
- **Strict DOM Synchronization**: `ArticlePage.navigate()` waits for `document.readyState == 'complete'`, target URL path matching, and headline visibility before extraction, preventing stale element state across navigations.
- **Resilient Multi-Selector Fallbacks**: Primary CSS classes are backed by semantic HTML tag fallbacks (`h1.a_t` -> `h1`, `.a_c p` -> `article p`) to handle layout variations across editorial categories.
- **Defensive API Design**: `TranslationService` attempts RapidAPI with retries before using `deep-translator`, ensuring tests execute reliably even without an API key.

---

## Results

```text
==================================== SUMMARY ====================================
Articles scraped:    5
Articles translated: 5
Images downloaded:   5 (article_1.jpg to article_5.jpg)
Repeated words (>2): 0 (or list of words if threshold met)
=================================================================================
PASSED
```

---

## Future Improvements

- Add `mypy` static type checking to CI pipeline.
- Implement HTML report generation with embedded screenshots for failed assertions.
- Extend mobile gesture support for infinite-scroll article feeds.

---

## Tech Stack

- **Language**: Python 3.10+
- **Automation**: Selenium WebDriver 4.20+
- **Test Framework**: pytest 8.0+
- **Cloud Grid**: BrowserStack Automate (BrowserStack SDK)
- **Translation**: RapidAPI / deep-translator
- **CI/CD**: GitHub Actions
