# Remedy Index — Sources & Provenance

> Tevaram / Tiruvasagam hymns as *pariharam* (remedy) for life ills — health, wealth, marriage, job, litigation, planetary afflictions etc.
> Research date: 2026-09-06 — saved for future `Remedies` section.

## Summary
Yes — a complete, traditional index exists. Each *pathigam* (decad of 10-11 verses) was composed with an explicit *phalan* (benefit) in its final verse (especially Sambandar & Sundarar) and later systematized as *Thirumurai Marundhu / Nalam Tharum Pathigam* (medicine that gives wellness). Modern sites expose it as a searchable database.

## Primary Sources

### 1. Nandini Muthuswamy — "Benefits derived from singing Tēvāram-s" (2009-02-21)
- **URL:** https://nandinimuthuswamy.wordpress.com/2009/02/21/benefits-derived-from-singing-tevaram-s/
- **Author lineage:** Violinist, descendant of Trinity (Thyagaraja/Dikshitar) — spiritual authority via Santhananda Swamigal parampara.
- **Content:** 19 exact mappings `Tevaram (incipit) → Composer → Benefit`
  - `Tunivalar Tinagal` (Sambandar) → bone disease
  - `Idarinum Talarinum` → economic prosperity
  - `Sadayaai Ennnum Maal` → marriage success
  - `Vaasi Teerave` / `Maraiyudayaai` → lawsuits
  - `Avvinai kivvinai` (Tiruneelakanta Pathigam) → blackmagic
  - `Kutraayina Vaaru` (Appar) → stomach/incurable diseases
  - `Mannil nalla vannam vaazhalaam` → weddings/anniversaries
  - `Kankaatunudalaanum` → progeny
  - `Nanrudaiyaanai` / `Mattuvaar kuzhalaalodu` → childbirth
  - `Maasil veenaiyum` (Appar) → heat diseases
  - `Sottrunai vediyan` → self-confidence
  - `Vettraagi vinnaagi` / `Tunjalum` → daily worship
  - `Veyuru Tolipangan` (Kolaru Pathigam) → 9 planets, `Bogamaartha` → Saturn, `Annam paalikkum` → daily food, `Kandukollariyaanai` → fear of death
- **Verification:** Page live, permalinks stable, benefits corroborated by Shaivam/Sivaya.
- **Use:** Quick English-label seed for `remedies.json` — already normalized.

### 2. Sivaya.org — "Nalam Tharum Pathigangal" (Beneficial Decads)
- **URL (Tamil):** https://www.sivaya.org/nalam_tharum_pathigam.php?lang=tamil
  - Category filters: `?category2= உடல் நலம்` (health) / `கோள்கள்` (planets) / `பொருளாதாரம்` (economy) / `திருமணம்` (marriage) / `குழந்தை` (child) / `உறவுகள்` (relations) / `கல்வி` (education) / `ஆளுமை` (personality) / `விவசாயம்` (agriculture) / `ஆன்மீகம்` (spiritual)
  - Also: `https://www.sivaya.org/nalam_tharum_pathigam_hindi.php?lang=english` (English)
- **Content sampled 2026-09-06:** `உடல் நலம்` alone lists 20+ entries, each with precise `pathigam_no` and link:
  - `4.001 Kootraayina Vaaru` → stomach/intestines (Appar)
  - `4.002` → poison/dangerous animals, `4.009 Thalaye Nee Vanangai` → body organs, `4.018 Onru Kolaam` → allergy/snake-bite, `5.090 Maasu Il Veenaiyum` → imprisonment, `8.112 Thiruvasagam` → stuttering, `7.061 Alandhan Uganthu` → left eye, `7.095 Meelaa Adimai` → right eye, `1.044 Thunivalar Thingal` → blood pressure/diabetes/addiction, `1.116 Avvinai` → fever/poison/throat/blackmagic, `2.047 Mattitta Punnai` → general ailments, `2.066 Mandiramavathu Neeru` → heat, `3.054 Vazhga Anthananar` → back pain/hunchback, `3.072` → fractures/paralysis, plus Abirami Andhathi 24/27 for disease/mental health, Thiruppugazh for wellness.
- **Features:** Each entry → `thirumurai_song.php?pathigam_no=X&lang=tamil` with Tamil text, translation, and separate `/nalam_tharum_pathigam_hindi.php?lang=english` rendering. Also offers offline save, QR, audio search (Chrome), 100+ pages limit.
- **Why primary:** Most structured, categorized, directly linkable, maintained by sivaya.org Thirumurai Kootam — use as canonical `remedies.json` source.

### 3. Shaivam.org — Thirumurai Medicine / Prayers for Specific Ailments
- **URLs:**
  - `https://shaivam.org/panniru-thirumurai/` → index reveals "Thirumurai Medicine" as related content
  - `https://shaivam.org/prayers-for-specific-ailments/` (Vendukol / Venduthal Pathikangal) — explains doctrine: Shiva as healer, devotee's surrender leads to liberation; pariharam is secondary grace, warns against misleading.
- **Content:** Doctrinal framing + categorized prayer lists (health, planetary). Less granular than Sivaya but authoritative (Shaivam.org / French Institute of Pondicherry lineage). Verifies tradition that *phalan* verses promise specific benefits.
- **Use:** Background note + cross-check; not the data source.

### 4. Specialist / Commentary
- **Kolaru Pathigam (Veyuru Tholipangan, Sambandar, 2.85)** — nine planets, one remedy. Detailed in:
  - `https://blog.cosmicinsights.net/nine-planets-one-remedy-the-miraculous-kolaru-pathigam/` (2023)
  - `https://www.boloji.com/blog/1947/kolaru-pathigam--why-it-is-so-significant`
  - `https://vedicvibes.blogspot.com/2025/07/kolaru-pathigam.html` (Mahaperiyava recommendation)
- **Note:** Kolaru is the archetype: Tamil *kOl* = planet/evil, *aRu* = cuts — promise that chanting turns all evils to good (last line of each verse).

## Coverage Check
- **Health:** 20+ distinct ailments (stomach, poison, eyes, bones, fever, diabetes, paralysis, etc.)
- **Wealth/Economy:** prosperity, food, economic stability
- **Marriage/Child:** success in marriage, progeny, safe delivery, auspicious occasions
- **Job/Education/Confidence:** self-confidence, daily worship, education (Kalvi), personality (Aalumai)
- **Litigation/Fear:** lawsuits, fear of death, blackmagic, imprisonment
- **Planets:** Navagraha + Saturn specific
- **Agriculture/Spiritual:** separate categories on Sivaya (farming, liberation)

## Provenance Notes
- All three traditions cite the **final verse phalan** of each pathigam (especially Sambandar/Sundarar) as source of benefit — a contemporary in-text claim, not modern invention.
- Data is devotional / faith-based, not medical advice — must carry disclaimer in future `Remedies` section.
- Links are public, no paywall, stable since 2009 (Nandini) / long-running (Sivaya/Shaivam). Sivaya explicitly permits offline save.

## Intended Use for Nalvar Site
- Build `remedies.json` as `category → [{ problem, pathigam, incipit, saint, thirumurai_no, benefit, sivaya_url, audio_url }]`
- Source in `remedies.json`: 19 Nandini items as seed + full Sivaya health list + category skeletons for remaining 9 Sivaya categories.
- UI: new `Remedies` tab → category pills → cards with `Problem → Sing this Pathigam → Benefit` + `Read Text` (Sivaya) + `Listen` (Shaivam/Sivaya audio) + `YouTube` search.
- Disclaimer footer: "For faith and cultural information only, not a substitute for professional medical/legal advice."

## Retrieved Artifacts (2026-09-06)
- Full page dump: Nandini 19-item list (saved)
- Sivaya nalam_tharum_pathigam health sample (11 items + categories)
- Shaivam prayers-for-specific-ailments header + Thirumurai index
- Kolaru Pathigam backgrounders (Cosmic Insights/Boloji)

---
Maintained by: Nalvar project — update `remedies.json` from these URLs; re-validate links quarterly.
