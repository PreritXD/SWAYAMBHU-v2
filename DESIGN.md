# Design System: SWAYAMBHU v2 — Shri Hit Premanand Satsang Archive
**Project ID:** `swayambhu-v2-premanandji-archive`  
**Aesthetic Benchmark:** High-End Editorial Archive / Museum Monograph / Contemporary Indian Typographic Design  
**Platform:** Web, Desktop-First (Full Fluid Responsiveness down to 390px Mobile Viewport)

---

## 0. Anti-Patterns & "AI Blob" Bans (Strict Rules)

To ensure the interface feels human-crafted, tactile, and agency-designed, the following elements are strictly banned:

* ❌ **NO Floating Fuzzy Gradients / AI Blobs:** Never use `blur-3xl` radial gradients, glowing mesh backdrops, or floating colored spheres.
* ❌ **NO Generic Glassmorphism:** Avoid `backdrop-blur-md bg-white/10` with glowing white borders. Surfaces are physical, like pressed kora paper and unbleached linen, not frosted acrylic plastic.
* ❌ **NO Generic Chat Bubble Motifs:** Never render discourse answers in rounded iMessage/WhatsApp chat bubbles. Format all dialogue as illuminated manuscripts, theatrical scripts, or court transcripts.
* ❌ **NO Cliché AI Sparkle Icons (✨):** Replace generic magic stars with bespoke typographic glyphs (e.g., `§`, `¶`, `†`, `॥`, `›`, or catalog brackets `〔 〕`).
* ❌ **NO Rounded-Everything (Pill Fatigue):** Restrict full pills (`rounded-full`) exclusively to active audio scrubbers, minute micro-tags, and playheads. Cards, panels, and viewports must use disciplined, architectural radii (`0px` to `6px` maximum).

---

## 1. Visual Theme & Atmosphere

### Vrindavan Dawn Archive (श्री वृन्दावन ब्रह्ममुहूर्त संग्रह)
The aesthetic embodies the quiet, dignified stillness of a sunlit Vrindavan library at dawn. It treats sacred discourses not as ephemeral video content, but as preserved living manuscripts, classical monographs, and museum-grade archival records.

* **The Canvas (Tactile Paper):** Unbleached rag paper, raw cotton parchment, and pressed khadi bookbinding. Generous, breathable margins that respect contemplation and spiritual gravitas.
* **The Keylines (Hairline Grid):** Razor-sharp, single-pixel architectural layout rules mimicking traditional Indian ledger books (*Bahi-Khata*) and classic Swiss modernist grid layouts.
* **The Ink (Mineral Pigments):** Deep sacred umber, burnt ochre, aged brass foil, and raw vermillion/kesariya used with disciplined restraint.
* **Elevation & Shadow Philosophy:** Completely flat or whisper-soft tactile contact shadows (`box-shadow: 0 1px 2px rgba(24, 21, 18, 0.05)`). Structural definition is achieved exclusively through 1px architectural hairline dividers rather than artificial heavy drop shadows.

---

## 2. Color Palette & Archival Tokens

Colors are defined by descriptive natural names, precise hex values, and strict functional roles:

### Archival CSS Custom Properties
```css
:root {
  /* Surface & Parchment (No clinical white or harsh yellow) */
  --bg-parchment-base: #F8F5EE;       /* Rich unbleached handmade rag paper */
  --bg-parchment-subtle: #F1ECE1;     /* Tonal card & secondary panel surface */
  --bg-parchment-sunken: #E7E0D2;     /* Input fields, inactive tabs, table stripes */
  
  /* Ink & Typography */
  --ink-primary: #181512;             /* Deep warm soot/umber ink (never pure #000) */
  --ink-secondary: #574F46;           /* Muted manuscript pencil notes */
  --ink-muted: #8A8175;               /* Catalog reference numbers, timestamps */
  --ink-faint: #C2BBB0;               /* Inactive icons, subtle guide markers */

  /* Ceremonial Pigments (Used strictly as precision accents, never flood fills) */
  --pigment-kesariya: #B84A1A;        /* Deep vermillion/saffron ochre (active state / key CTA) */
  --pigment-brass: #9E7432;           /* Aged golden foil for quotation rules & marks */
  --pigment-brass-light: #C49746;     /* Subtle focus rings and illuminated verse numbers */
  
  /* Architectural Keylines */
  --border-hairline: rgba(24, 21, 18, 0.08);       /* 1px subtle structure dividers */
  --border-accent: rgba(184, 74, 26, 0.25);        /* Highlighted citation borders */
  --border-solid: #DDD5C7;                         /* Structural card boundaries */
}
```

### Color Mapping Matrix
| Color Name | Hex / RGB Code | Functional & Semantic Role |
| :--- | :--- | :--- |
| **Unbleached Rag Paper** | `#F8F5EE` | **Primary Canvas Surface:** Tactile, warm, non-fatiguing master page background. |
| **Subtle Parchment** | `#F1ECE1` | **Secondary Panel & Card Surface:** Tonal containers, sidebar marginalia, and metadata panels. |
| **Sunken Parchment** | `#E7E0D2` | **Recessed Elements:** Input backgrounds, inactive category tabs, alternating row stripes. |
| **Deep Warm Soot / Umber Ink** | `#181512` | **Primary Ink:** High-contrast editorial titles, transcript dialogue, and primary glyphs (never pure `#000000`). |
| **Muted Manuscript Umber** | `#574F46` | **Secondary Ink:** Discourse explanatory notes, transcript speaker indicators, translations. |
| **Aged Catalog Muted** | `#8A8175` | **Tertiary Data:** Monospaced catalog numbers, video timestamps, running folio headers. |
| **Faint Guide Ink** | `#C2BBB0` | **Guide Markers:** Inactive navigation glyphs, subtle grid tick marks, border hints. |
| **Raw Kesariya / Vermillion** | `#B84A1A` | **Ceremonial Accent & Action:** Active scrubbers, primary playhead triggers, live recording dots. |
| **Aged Brass Foil** | `#9E7432` | **Illuminated Accents:** Quotation hairline borders, illuminated chapter brackets `〔 〕`, sacred verse markers. |
| **Illuminated Brass Light** | `#C49746` | **Focus & Micro-Highlights:** Focus boundary rings, active text hover transitions. |
| **Architectural Hairline** | `rgba(24, 21, 18, 0.08)` | **Subtle Grid Dividers:** 1px architectural dividers, marginalia separators. |
| **Citation Border Accent** | `rgba(184, 74, 26, 0.25)` | **Citation Enclosures:** Active quote highlights and active timestamp card strokes. |
| **Structural Border Solid** | `#DDD5C7` | **Physical Boundaries:** Outer card frames, image passe-partout outlines, player docks. |

---

## 3. Typography & Typesetting Engine

Extreme contrast between sculptural editorial display serifs, authentic Devanagari typography, utilitarian modern sans-serifs, and tabular monospaces.

### Font Families
* **Display / Editorial Headings:** `"Instrument Serif"`, `"Playfair Display"`, or `"Cinzel"`, serif (Sculptural grace, classical authority).
* **Sacred Sanskrit / Hindi Body:** `"Rozha One"` (Display) and `"Noto Serif Devanagari"` (Body text & verses).
* **Interface / Data Engine:** `"Plus Jakarta Sans"` or `"Geist Sans"`, sans-serif (Clean modern grotesque, high legibility).
* **Catalog & Timecodes:** `"JetBrains Mono"` or `"Space Mono"`, monospace (Strict tabular alignment, zero character shift).

### Typographic Hierarchy Matrix
| Role | Font Family | Size | Weight / Style | Tracking | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Folio / Catalog No.** | Monospace | `11px` | `500 Medium` | `+0.12em uppercase` | `[CATALOGUE 0482 // EKANTIK]` |
| **Archival Inscription** | Serif | `48px–72px` | `400 Italic` | `-0.02em tight` | Hero title, sacred quotations, monumental epigraphs |
| **Discourse Header** | Serif | `24px–32px` | `400 Regular` | `normal` | Satsang episode titles, chapter divisions |
| **Devanagari Slokas** | Devanagari Serif | `18px–22px` | `400 Regular` | `+0.01em` | Original Hindi/Braj quotes (`॥ श्रीराधा ॥`, `॥ राधा वल्लभ श्री हरिवंश ॥`) |
| **Transcript Prose** | Sans-serif | `15px` | `400 Regular` | `normal, 1.75 line-height` | Main discourse dialogue, questions & authoritative answers |
| **System Labels / Meta** | Sans-serif | `12px` | `600 Semibold` | `+0.08em uppercase` | Filter tabs, audio metrics, sources, archival status |

---

## 4. Grid System & Layout Structure

The layout rejects generic, centered marketing page patterns in favor of a disciplined, asymmetric **Archival Editorial Grid** based on traditional Indian ledger books (*Bahi-Khata*) and classic Swiss editorial layout standards:

```text
+-----------------------------------------------------------------------------------+
| RUNNING HEADER: [SWAYAMBHU // ARCHIVE VOL. 02]           DATE: VRINDAVAN DHAM      |
+-----------------------------------------------------------------------------------+
| 1px border-b                                                                      |
| MARGIN (3 cols)         | MAIN WORKSPACE / TRANSCRIPT (6 cols)   | MEDIA (3 cols) |
|                         |                                        |                |
| - Discourse Index       | "QUESTION: Maharaj ji, man mein        | [SACRED        |
| - Category Taxonomy     | ashanti kyu hoti hai?"                 |  PORTRAIT      |
| - Timestamp Seekpoints  |                                        |  FRAME]        |
|   [02:14] Chitta Shuddhi| -- Detailed, high-legibility           |                |
|   [08:42] Naam Jap Vidhi|    transcript set in columns.          | Rec No: #1480  |
|                         |    Bilingual toggle (HI / EN).         | Audio Waveform |
+-----------------------------------------------------------------------------------+
```

### Layout Principles
* **Running Folio Line (Museum Bar):** Positioned at the very top edge. Features monospaced catalog markers (`CATALOGUE INDEX`, `LIVE LOCAL TIME: VRINDAVAN`, `TOTAL ARCHIVES: 1,840+ HRS`). Single `1px solid var(--border-hairline)` boundary.
* **Columnar Marginalia:** 20% to 25% side columns dedicated to context, footnotes, timestamp links, and Sanskrit verse cross-references.
* **Strict Keyline Enclosures:** Sections and panels are partitioned using razor-thin `1px solid var(--border-hairline)` lines rather than drop-shadowed cards.
* **Architectural Geometry:** Zero or minimal border radii (`0px` to `6px`). The interface is defined by clean, straight cuts mimicking bound folio pages.

---

## 5. Bespoke Component Specifications

### 1. The Archival Inscription (Search & Query Field)
* **Visual Form:** Clean, open horizontal baseline rule (no rounded input boxes).
* **Placeholder:** *"Search discourses, slokas, or ask a contemplative question..."* styled in *Instrument Serif* italic at `22px` in `var(--ink-muted)`.
* **Left Glyph:** Traditional Indian pause mark `॥` or catalog index `№` in `var(--pigment-kesariya)`.
* **Right Meta:** Monospaced keyboard shortcut badge: `[ ⌘K — ARCHIVE SEARCH ]` set on `var(--bg-parchment-sunken)` with `var(--ink-secondary)`.

### 2. Dialogue & Satsang Transcript Stream (Illuminated Manuscript Style)
* **No Generic Chat Bubbles:** Dialogue is rendered as an illuminated script or judicial transcript.
* **Speaker Identification:**
  * **Aspirant (Sadhak):** Monospaced hairline-bordered tag `[JIGYASU — QUESTION]`, followed by crisp, respectful sans-serif prose.
  * **Master (Pujya Premanand Ji):** Hand-tinted terracotta label `[SHRI PREMANAND JI MAHARAJ — NIRNAYA]` followed by an illuminated quotation bracket `〔`.
* **Interactive Timestamps:** Integrated within transcript prose as `[ 04:12 ▶ ]`. Clicking smoothly jumps the master audio player to the exact seek point.
* **Container Styling:** No bubble background. Clean, open typography with a left vertical keyline (`border-l-2 border-[#9E7432]`) and subtle inset padding.

### 3. Audio & Discourse Scrubber Dock (Analog Console)
* **Placement:** Fixed dock at viewport bottom, anchored edge-to-edge.
* **Surface:** `var(--bg-parchment-subtle)` with top `1px solid var(--border-solid)` divider.
* **Left Section:** Small sacred artwork thumbnail (`48x48px`, `rounded-[2px]`, warm duotone sepia) + Episode metadata in monospace.
* **Center Section:** Mechanical analog audio wave scrubber with vertical tick-marks (reminiscent of Nagra or Braun tape recorders) replacing generic flat sliders.
* **Right Section:** Speed toggles (`0.75x`, `1.0x`, `1.5x`), Hindi/English transcript sync toggle switch (`[ HI | EN ]`).

### 4. Sacred Portraiture & Ephemera Framing
* **Aspect Ratio:** Classical `4:5` or `3:4` portrait ratio.
* **Border Construction:** Single `1px solid var(--border-solid)` perimeter with a `4px` inset passe-partout paper frame.
* **Photographic Treatment:** Monochromatic or warm umber duotone tint that blends harmoniously into the parchment canvas. Zero high-saturation commercial crops.
* **Plaque Citation:** Minimal museum label directly beneath the image:
  ```text
  FIG 01.1 — EKANTIK VARTALAAP
  RECORDED: SHRI HIT RADHA KELI KUNJ, VRINDAVAN
  PRESERVED IN FIDELITY • 2024
  ```

---

## 6. Motion & Kinetic Polish

Motion is contemplative, analog, and deliberate—never bouncy, frivolous, or synthetic:

* **Transitions:** `transition: all 400ms cubic-bezier(0.16, 1, 0.3, 1)` (silk-smooth deceleration curve).
* **Text Reveal:** Fade-up with subtle mask reveal (`translateY(8px)` to `0px` with opacity from `0` to `1`).
* **Hover States:** Text transforms gracefully to `var(--pigment-kesariya)`; keyline borders darken subtly from 10% to 30% opacity. No zoom scaling or 3D tilt effects.
* **Live Audio Indicator:** Measured 4-bar equalizer moving in a calm, rhythmic cadence.

---

## 7. Direct Tailwind & CSS Implementation Reference

```html
<!-- Archival Container Example -->
<div class="bg-[#F8F5EE] text-[#181512] min-h-screen border-x border-[#181512]/10 max-w-7xl mx-auto font-sans antialiased">
  
  <!-- Running Archival Top Bar -->
  <header class="flex justify-between items-center px-8 py-3 border-b border-[#181512]/10 text-[11px] font-mono tracking-widest text-[#8A8175] uppercase">
    <span>SWAYAMBHU // ARCHIVAL SATSANG CORPUS</span>
    <span class="text-[#B84A1A]">● VRINDAVAN LIVE RECORDING ARCHIVE</span>
    <span>VOL. II — 2026 EDITION</span>
  </header>

  <!-- Hero Section -->
  <section class="px-8 py-16 grid grid-cols-12 gap-8 border-b border-[#181512]/10">
    <div class="col-span-8 flex flex-col justify-between">
      <span class="font-mono text-xs text-[#9E7432] uppercase tracking-wider mb-4">॥ राधा वल्लभ श्री हरिवंश ॥</span>
      <h1 class="font-serif italic text-6xl text-[#181512] leading-[1.1] tracking-tight">
        "Pure devotion begins where the complications of the ego quietly dissolve."
      </h1>
      <div class="mt-8 pt-8 border-t border-[#181512]/5 flex gap-4 text-xs font-mono text-[#574F46]">
        <span>DISCOURSE NO. 1,492</span>
        <span>•</span>
        <span>LOCATION: RADHA KELI KUNJ</span>
      </div>
    </div>
    
    <!-- Archival Frame -->
    <div class="col-span-4 p-2 bg-[#F1ECE1] border border-[#DDD5C7]">
      <div class="aspect-[4/5] bg-[#E7E0D2] border border-[#181512]/10 relative overflow-hidden flex items-center justify-center">
        <!-- Portrait Asset -->
        <div class="text-[11px] font-mono text-[#8A8175] tracking-widest uppercase">[ARCHIVAL PORTRAIT]</div>
      </div>
      <p class="font-mono text-[10px] text-[#8A8175] mt-2 uppercase tracking-tight text-center">
        FIG. 24 — PUJYA MAHARAJ JI (2024)
      </p>
    </div>
  </section>

  <!-- Archival Inscription (Search Field) -->
  <section class="px-8 py-8 border-b border-[#181512]/10">
    <div class="relative flex items-center border-b border-[#181512]/20 pb-3 focus-within:border-[#B84A1A] transition-colors">
      <span class="text-xl text-[#B84A1A] font-serif mr-4">॥</span>
      <input 
        type="text" 
        placeholder="Search discourses, slokas, or ask a contemplative question..." 
        class="w-full bg-transparent font-serif italic text-2xl text-[#181512] placeholder-[#8A8175] focus:outline-none"
      />
      <div class="hidden sm:flex items-center gap-2 text-[10px] font-mono uppercase text-[#574F46] bg-[#E7E0D2] px-2.5 py-1 border border-[#DDD5C7]">
        <span>⌘K — ARCHIVE SEARCH</span>
      </div>
    </div>
  </section>

  <!-- Editorial Grid: Marginalia + Transcript Stream -->
  <div class="grid grid-cols-12 min-h-[600px]">
    <!-- Marginalia (3 cols) -->
    <aside class="col-span-3 border-r border-[#181512]/10 p-6 space-y-8 text-xs">
      <div>
        <div class="font-mono text-[10px] uppercase tracking-widest text-[#8A8175] mb-3">TAXONOMY // CATEGORIES</div>
        <ul class="space-y-2 font-mono text-[#574F46]">
          <li class="cursor-pointer hover:text-[#B84A1A] flex items-center gap-2"><span>›</span> Chitta Shuddhi (42)</li>
          <li class="cursor-pointer text-[#B84A1A] font-semibold flex items-center gap-2"><span>›</span> Naam Jap Vidhi (184)</li>
          <li class="cursor-pointer hover:text-[#B84A1A] flex items-center gap-2"><span>›</span> Ekantik Rahasya (96)</li>
          <li class="cursor-pointer hover:text-[#B84A1A] flex items-center gap-2"><span>›</span> Guru Mahima (51)</li>
        </ul>
      </div>

      <div>
        <div class="font-mono text-[10px] uppercase tracking-widest text-[#8A8175] mb-3">RECEPTACLES // TIMESTAMPS</div>
        <div class="space-y-2 font-mono text-[11px]">
          <a href="#t-0214" class="block p-2 bg-[#F1ECE1] border border-[#DDD5C7] hover:border-[#B84A1A]/40 text-[#181512]">
            <span class="text-[#B84A1A] font-bold">[02:14]</span> Chitta Shuddhi Prarambh
          </a>
          <a href="#t-0842" class="block p-2 bg-[#F1ECE1] border border-[#DDD5C7] hover:border-[#B84A1A]/40 text-[#181512]">
            <span class="text-[#B84A1A] font-bold">[08:42]</span> Naam Jap Vidhi & Niyam
          </a>
        </div>
      </div>
    </aside>

    <!-- Main Transcript Body (6 cols) -->
    <main class="col-span-6 p-8 space-y-8">
      <!-- Jigyasu Query -->
      <article class="space-y-2">
        <div class="font-mono text-[10px] uppercase tracking-widest text-[#8A8175] border-b border-[#181512]/5 pb-1">
          [JIGYASU — QUESTION] • DISCOURSE #1480
        </div>
        <p class="font-sans text-[15px] leading-relaxed text-[#181512]">
          "Maharaj ji, jab hum naam jap karne baithte hain, toh man mein anchahe vichar aur ashanti kyu utpann hoti hai? Iska samadhan kya hai?"
        </p>
      </article>

      <!-- Maharaj Ji Nirnaya (Illuminated Manuscript) -->
      <article class="space-y-3 pl-6 border-l-2 border-[#9E7432] bg-[#F1ECE1]/30 p-4">
        <div class="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-[#B84A1A]">
          <span>[SHRI PREMANAND JI MAHARAJ — NIRNAYA]</span>
          <span class="text-[#8A8175]">VRINDAVAN DHAM</span>
        </div>
        <div class="font-serif italic text-lg text-[#9E7432]">
          〔 "Man ka swabhav hi chanchal hai. Jab tak maila kapda dhoya nahi jata..."
        </div>
        <p class="font-sans text-[15px] leading-[1.75] text-[#181512]">
          जैसे गंदे वस्त्र को जब जल और साबुन में डालते हैं, तो पहले उसका मैल ऊपर उभर कर आता है। वैसे ही जब आप भगवन्नाम जपते हैं, तो अंतःकरण में संचित जन्म-जन्मांतरों के संस्कार और मल बाहर निकलते हैं। इससे घबराना नहीं चाहिए।
        </p>
        <div class="pt-2 flex items-center gap-3">
          <button class="font-mono text-xs text-[#B84A1A] border border-[#B84A1A]/30 bg-[#F1ECE1] px-2.5 py-1 hover:bg-[#B84A1A] hover:text-[#F8F5EE] transition-colors">
            [ 04:12 ▶ SEEK IN AUDIO ]
          </button>
          <span class="font-mono text-[10px] text-[#8A8175]">SOURCE: BHAJAN MARG EP. 1480</span>
        </div>
      </article>
    </main>

    <!-- Secondary Media & Annotation Column (3 cols) -->
    <aside class="col-span-3 border-l border-[#181512]/10 p-6 space-y-6 text-xs">
      <div class="p-4 bg-[#F1ECE1] border border-[#DDD5C7]">
        <div class="font-mono text-[10px] uppercase tracking-widest text-[#8A8175] mb-2">PRIMARY DISCOURSE METRICS</div>
        <div class="space-y-1 font-mono text-[11px] text-[#574F46]">
          <div>CATALOG ID: #SWY-1480</div>
          <div>RECORDED: OCT 2024</div>
          <div>DURATION: 34M 12S</div>
          <div>LANGUAGE: BRAJ / HINDI</div>
        </div>
      </div>
      <div class="border-t border-[#181512]/10 pt-4">
        <div class="font-mono text-[10px] uppercase tracking-widest text-[#8A8175] mb-2">SHLOKA REFERENCE</div>
        <div class="font-serif text-sm text-[#181512] italic leading-relaxed">
          "चञ्चलं हि मनः कृष्ण प्रमाथि बलवद्दृढम्।<br>तस्याहं निग्रहं मन्ये वायोरिव सुदुष्करम्॥"
        </div>
        <div class="font-mono text-[10px] text-[#8A8175] mt-1">— श्रीमद्भगवद्गीता 6.34</div>
      </div>
    </aside>
  </div>

  <!-- Audio Scrubber Dock (Fixed at bottom) -->
  <footer class="sticky bottom-0 bg-[#F1ECE1] border-t border-[#DDD5C7] px-8 py-3 flex items-center justify-between z-40">
    <div class="flex items-center gap-4">
      <div class="w-10 h-10 bg-[#E7E0D2] border border-[#DDD5C7] flex items-center justify-center font-mono text-[10px] text-[#8A8175]">
        [REC]
      </div>
      <div>
        <div class="font-sans text-xs font-semibold text-[#181512]">Ekantik Vartalaap #1480</div>
        <div class="font-mono text-[10px] text-[#8A8175]">RADHA KELI KUNJ // 04:12 / 34:12</div>
      </div>
    </div>

    <!-- Analog Waveform Scrubber -->
    <div class="flex-1 max-w-xl mx-8 flex items-center gap-1 h-6">
      <div class="h-2 w-0.5 bg-[#B84A1A]"></div>
      <div class="h-4 w-0.5 bg-[#B84A1A]"></div>
      <div class="h-5 w-0.5 bg-[#B84A1A]"></div>
      <div class="h-3 w-0.5 bg-[#B84A1A]"></div>
      <div class="h-6 w-0.5 bg-[#B84A1A]"></div>
      <div class="h-4 w-0.5 bg-[#181512]/20"></div>
      <div class="h-2 w-0.5 bg-[#181512]/20"></div>
      <div class="h-5 w-0.5 bg-[#181512]/20"></div>
      <div class="h-3 w-0.5 bg-[#181512]/20"></div>
    </div>

    <div class="flex items-center gap-4 font-mono text-xs">
      <button class="px-2 py-1 border border-[#DDD5C7] hover:border-[#181512]/40 text-[#574F46]">1.0x</button>
      <button class="px-3 py-1 bg-[#B84A1A] text-[#F8F5EE]">HI / EN</button>
    </div>
  </footer>
</div>
```
