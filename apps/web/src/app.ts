(() => {
  'use strict';

  const DATA = window.RI_BOOTSTRAP;
  const TAXONOMY = new Map<MechanismId, TaxonomyMechanism>(
    DATA.taxonomy.mechanisms.map((m) => [m.id, m])
  );

  type View = 'scanner' | 'compare' | 'event' | 'taxonomy' | 'methodology';
  type Mode = 'synthetic_fixture' | 'local_preview';

  interface LensState {
    enabled: boolean;
    pinned: boolean;
    revealAll: boolean;
    x: number;
    y: number;
    radius: number;
    dragging: boolean;
    activePointerId: number | null;
  }

  interface Filters {
    family: MechanismFamily | 'all';
    confidence: 'all' | 'confirmed' | 'candidate';
    search: string;
  }

  interface AppState {
    view: View;
    mode: Mode;
    article: Article;
    findings: Finding[];
    event: EventRecord | null;
    analysisRun: AnalysisRun;
    selectedFindingId: string | null;
    selectedClaimId: string | null;
    filters: Filters;
    lens: LensState;
    reducedMotion: boolean;
    patternMode: boolean;
    drawerOpen: boolean;
  }

  interface SpanSegment {
    start: number;
    end: number;
    text: string;
    findings: Finding[];
  }

  const fixtureEvent = DATA.fixture.event;
  const fixtureArticle = fixtureEvent.articles[0];
  const fixtureFindings = DATA.fixture.findings;

  const state: AppState = {
    view: 'scanner',
    mode: 'synthetic_fixture',
    article: fixtureArticle,
    findings: fixtureFindings,
    event: fixtureEvent,
    analysisRun: makeAnalysisRun('synthetic_fixture', fixtureArticle, fixtureFindings, 'fixture-reviewed-v1', 'complete'),
    selectedFindingId: null,
    selectedClaimId: fixtureEvent.atomicClaims[0]?.id || null,
    filters: { family: 'all', confidence: 'all', search: '' },
    lens: { enabled: true, pinned: false, revealAll: false, x: 390, y: 290, radius: 145, dragging: false, activePointerId: null },
    reducedMotion: loadBooleanSetting('ri-reduced-motion', false),
    patternMode: loadBooleanSetting('ri-pattern-mode', false),
    drawerOpen: false,
  };

  const el = <T extends HTMLElement = HTMLElement>(id: string): T => {
    const node = document.getElementById(id);
    if (!node) throw new Error(`Missing required element #${id}`);
    return node as T;
  };

  const scannerView = el('scannerView');
  const compareView = el('compareView');
  const eventView = el('eventView');
  const taxonomyView = el('taxonomyView');
  const methodologyView = el('methodologyView');
  const articleSurface = el('articleSurface');
  const articleBase = el('articleBase');
  const articleOverlay = el('articleOverlay');
  const lensReadout = el('lensReadout');
  const drawer = el('findingDrawer');
  const scrim = el('scrim');
  const liveRegion = el('liveRegion');
  const pastePanel = el('pastePanel');
  const pasteText = el<HTMLTextAreaElement>('pasteText');
  const touchHandle = el<HTMLButtonElement>('touchLensHandle');

  let lastFocus: HTMLElement | null = null;
  let touchTapStart: { id: number; x: number; y: number; t: number } | null = null;
  let topbarObserver: ResizeObserver | null = null;

  function loadBooleanSetting(key: string, fallback: boolean): boolean {
    try {
      const value = localStorage.getItem(key);
      if (value === null) return fallback;
      return value === 'true';
    } catch {
      return fallback;
    }
  }

  function saveSettings(): void {
    try {
      localStorage.setItem('ri-reduced-motion', String(state.reducedMotion));
      localStorage.setItem('ri-pattern-mode', String(state.patternMode));
    } catch {
      // Local storage is optional. The interface continues without persistence.
    }
  }

  function esc(value: unknown): string {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fnv1a(text: string): string {
    let hash = 0x811c9dc5;
    for (let i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 0x01000193) >>> 0;
    }
    return `fnv1a-${hash.toString(16).padStart(8, '0')}`;
  }

  function makeAnalysisRun(
    mode: Mode,
    article: Article,
    findings: Finding[],
    detectorVersion: string,
    stage: ScanStage
  ): AnalysisRun {
    const metrics = calculateMetrics(article, findings);
    return {
      runId: `${mode}-${fnv1a(article.content)}-${Date.now()}`,
      scanMode: mode,
      articleSnapshotHash: fnv1a(article.content),
      taxonomyVersion: DATA.taxonomy.version,
      detectorVersion,
      timestamp: new Date().toISOString(),
      stage,
      findingsCount: findings.length,
      peakPressure: metrics.peakPressure,
      confirmedDensity: metrics.confirmedDensity,
      candidateDensity: metrics.candidateDensity,
      processedParagraphs: article.paragraphs.map((_, index) => index),
      unprocessedParagraphs: [],
    };
  }

  function pressureNumber(level: PressureLevel): number {
    return Number(level.slice(1));
  }

  function confidenceClass(confidence: ConfidenceLevel): string {
    return confidence.toLowerCase();
  }

  function familyLabel(family: MechanismFamily): string {
    const labels: Record<MechanismFamily, string> = {
      intrinsic_linguistic: 'Intrinsic linguistic',
      framing_epistemic: 'Framing / epistemic',
      agency_causality: 'Agency / causality',
      journalism_cross_doc: 'Journalism / cross-document',
    };
    return labels[family];
  }

  function visibleFindings(): Finding[] {
    const q = state.filters.search.trim().toLowerCase();
    return state.findings.filter((finding) => {
      if (state.filters.family !== 'all' && finding.family !== state.filters.family) return false;
      if (state.filters.confidence === 'confirmed' && finding.state !== 'confirmed') return false;
      if (state.filters.confidence === 'candidate' && finding.state !== 'candidate') return false;
      if (q) {
        const mechanism = TAXONOMY.get(finding.mechanism)?.canonicalName || finding.mechanism;
        if (!mechanism.toLowerCase().includes(q) && !finding.span.text.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }

  function spansForParagraph(paragraphIndex: number, findings = visibleFindings()): Finding[] {
    return findings
      .filter((finding) => finding.span.paragraphIndex === paragraphIndex)
      .sort((a, b) => a.span.startChar - b.span.startChar || a.span.endChar - b.span.endChar);
  }

  function segmentParagraph(text: string, findings: Finding[]): SpanSegment[] {
    const valid = findings.filter((finding) =>
      finding.span.startChar >= 0 &&
      finding.span.endChar > finding.span.startChar &&
      finding.span.endChar <= text.length &&
      text.slice(finding.span.startChar, finding.span.endChar) === finding.span.text
    );
    const points = new Set<number>([0, text.length]);
    valid.forEach((finding) => {
      points.add(finding.span.startChar);
      points.add(finding.span.endChar);
    });
    const sorted = [...points].sort((a, b) => a - b);
    const segments: SpanSegment[] = [];
    for (let i = 0; i < sorted.length - 1; i += 1) {
      const start = sorted[i];
      const end = sorted[i + 1];
      if (end <= start) continue;
      const active = valid.filter((finding) => finding.span.startChar <= start && finding.span.endChar >= end);
      segments.push({ start, end, text: text.slice(start, end), findings: active });
    }
    return segments;
  }

  function renderParagraphSegments(text: string, paragraphIndex: number, overlay: boolean): string {
    return segmentParagraph(text, spansForParagraph(paragraphIndex)).map((segment, segmentIndex) => {
      const safeText = esc(segment.text);
      if (!segment.findings.length) return overlay ? `<span class="scan-plain">${safeText}</span>` : safeText;
      const ids = segment.findings.map((finding) => finding.id).join(',');
      const primary = [...segment.findings].sort((a, b) => pressureNumber(b.pressure) - pressureNumber(a.pressure))[0];
      const selected = segment.findings.some((finding) => finding.id === state.selectedFindingId);
      if (overlay) {
        return `<span class="scan-mark family-${esc(primary.family)} p${pressureNumber(primary.pressure)} ${selected ? 'selected' : ''}" data-finding-ids="${esc(ids)}" data-segment="${paragraphIndex}-${segmentIndex}">${safeText}</span>`;
      }
      const aria = segment.findings.map((finding) => TAXONOMY.get(finding.mechanism)?.canonicalName || finding.mechanism).join(' and ');
      return `<span class="base-mark ${selected ? 'selected' : ''}" tabindex="0" role="button" data-finding-ids="${esc(ids)}" data-segment="${paragraphIndex}-${segmentIndex}" aria-label="Inspect ${esc(aria)} finding">${safeText}</span>`;
    }).join('');
  }

  function articleMarkup(overlay: boolean): string {
    const article = state.article;
    const paragraphs = article.paragraphs.map((paragraph, index) =>
      `<p data-paragraph-index="${index}" ${overlay ? '' : `id="paragraph-${index}"`}>${renderParagraphSegments(paragraph, index, overlay)}</p>`
    ).join('');
    return `
      <div class="article-kicker">${state.mode === 'synthetic_fixture' ? 'Synthetic fixture demonstration' : 'User-provided text · local preview'}</div>
      <h1 class="article-title">${esc(article.title)}</h1>
      <p class="article-dek">${state.mode === 'synthetic_fixture' ? 'A fictional event used to demonstrate rhetorical inspection without presenting live reporting.' : 'Unbenchmarked local rules produce candidates only. Comparison and Event Record remain unavailable.'}</p>
      <div class="article-meta">${esc(article.publisher)}${article.author ? ` · ${esc(article.author)}` : ''}</div>
      <div class="article-copy">${paragraphs}</div>
    `;
  }

  function renderArticle(): void {
    articleBase.innerHTML = articleMarkup(false);
    articleOverlay.innerHTML = articleMarkup(true);
    bindBaseMarks();
    requestAnimationFrame(() => {
      applyLensBounds();
      renderLens();
      verifyOverlayGeometry(false);
    });
  }

  function bindBaseMarks(): void {
    articleBase.querySelectorAll<HTMLElement>('.base-mark').forEach((mark) => {
      const open = () => {
        const ids = (mark.dataset.findingIds || '').split(',').filter(Boolean);
        if (ids[0]) openFinding(ids[0], ids);
      };
      mark.addEventListener('click', open);
      mark.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          open();
        }
      });
    });
  }

  function verifyOverlayGeometry(announce: boolean): boolean {
    const baseMarks = [...articleBase.querySelectorAll<HTMLElement>('.base-mark')];
    const overlayMarks = [...articleOverlay.querySelectorAll<HTMLElement>('.scan-mark')];
    if (baseMarks.length !== overlayMarks.length) return false;
    let maxDelta = 0;
    for (let i = 0; i < baseMarks.length; i += 1) {
      const a = baseMarks[i].getBoundingClientRect();
      const b = overlayMarks[i].getBoundingClientRect();
      maxDelta = Math.max(maxDelta, Math.abs(a.left - b.left), Math.abs(a.top - b.top), Math.abs(a.width - b.width), Math.abs(a.height - b.height));
    }
    const ok = maxDelta <= 0.75;
    articleSurface.dataset.overlayAligned = String(ok);
    articleSurface.dataset.overlayMaxDelta = maxDelta.toFixed(2);
    if (announce && !ok) liveRegion.textContent = 'Annotation overlay alignment needs attention.';
    return ok;
  }

  function calculateCoverage(article: Article, findings: Finding[], stateFilter: FindingState): number {
    const total = article.paragraphs.reduce((sum, paragraph) => sum + paragraph.length, 0) || 1;
    let covered = 0;
    article.paragraphs.forEach((paragraph, paragraphIndex) => {
      const intervals = findings
        .filter((finding) => finding.state === stateFilter && finding.span.paragraphIndex === paragraphIndex)
        .map((finding) => [finding.span.startChar, finding.span.endChar] as [number, number])
        .sort((a, b) => a[0] - b[0]);
      let cursorStart = -1;
      let cursorEnd = -1;
      intervals.forEach(([start, end]) => {
        const s = Math.max(0, Math.min(paragraph.length, start));
        const e = Math.max(s, Math.min(paragraph.length, end));
        if (cursorStart < 0) {
          cursorStart = s;
          cursorEnd = e;
        } else if (s <= cursorEnd) {
          cursorEnd = Math.max(cursorEnd, e);
        } else {
          covered += cursorEnd - cursorStart;
          cursorStart = s;
          cursorEnd = e;
        }
      });
      if (cursorStart >= 0) covered += cursorEnd - cursorStart;
    });
    return Math.round((covered / total) * 1000) / 10;
  }

  function calculateMetrics(article: Article, findings: Finding[]) {
    const peak = findings.reduce((max, finding) => Math.max(max, pressureNumber(finding.pressure)), 1);
    const distribution = [1, 2, 3, 4].map((level) => findings.filter((finding) => pressureNumber(finding.pressure) === level).length);
    return {
      peakPressure: `P${peak}` as PressureLevel,
      confirmedDensity: calculateCoverage(article, findings, 'confirmed'),
      candidateDensity: calculateCoverage(article, findings, 'candidate'),
      distribution,
    };
  }

  function renderProfile(): void {
    const metrics = calculateMetrics(state.article, state.findings);
    const confirmed = state.findings.filter((finding) => finding.state === 'confirmed').length;
    const candidates = state.findings.filter((finding) => finding.state === 'candidate').length;
    el('profile').innerHTML = `
      <div class="profile-card"><span>Peak pressure</span><strong>${metrics.peakPressure}</strong><small>Pressure, not factuality</small></div>
      <div class="profile-card"><span>Confirmed density</span><strong>${metrics.confirmedDensity}%</strong><small>${confirmed} confirmed findings</small></div>
      <div class="profile-card"><span>Candidate density</span><strong>${metrics.candidateDensity}%</strong><small>${candidates} candidates remain visible</small></div>
      <div class="profile-card"><span>P1–P4 findings</span><strong>${metrics.distribution.join(' · ')}</strong><small>Counts, not a master score</small></div>
    `;
  }

  function renderSelectionState(): void {
    document.querySelectorAll<HTMLElement>('[data-finding]').forEach((node) => node.classList.toggle('selected', node.dataset.finding === state.selectedFindingId));
    articleBase.querySelectorAll<HTMLElement>('.base-mark').forEach((mark) => mark.classList.toggle('selected', !!state.selectedFindingId && (mark.dataset.findingIds || '').split(',').includes(state.selectedFindingId)));
    articleOverlay.querySelectorAll<HTMLElement>('.scan-mark').forEach((mark) => mark.classList.toggle('selected', !!state.selectedFindingId && (mark.dataset.findingIds || '').split(',').includes(state.selectedFindingId)));
  }

  function renderFindings(): void {
    const findings = visibleFindings();
    el('findingCount').textContent = `${findings.length} / ${state.findings.length}`;
    el('findingsList').innerHTML = findings.length ? findings.map((finding) => {
      const mechanism = TAXONOMY.get(finding.mechanism);
      return `<button class="finding-row ${finding.id === state.selectedFindingId ? 'selected' : ''}" data-finding="${esc(finding.id)}">
        <span class="finding-row-top"><strong>${esc(mechanism?.canonicalName || finding.mechanism)}</strong><span>${finding.pressure} · ${esc(finding.confidence)}</span></span>
        <span class="finding-excerpt">“${esc(finding.span.text)}”</span>
        <span class="finding-origin">${finding.state === 'candidate' ? 'Candidate' : 'Confirmed'} · ${esc(familyLabel(finding.family))}</span>
      </button>`;
    }).join('') : `<p class="empty-note">No findings match the current filters.</p>`;
    el('findingsList').querySelectorAll<HTMLButtonElement>('[data-finding]').forEach((button) => {
      button.addEventListener('click', () => openFinding(button.dataset.finding || ''));
    });
  }

  function renderFilters(): void {
    const family = el<HTMLSelectElement>('familyFilter');
    const confidence = el<HTMLSelectElement>('confidenceFilter');
    const search = el<HTMLInputElement>('findingSearch');
    family.value = state.filters.family;
    confidence.value = state.filters.confidence;
    search.value = state.filters.search;
  }

  function renderControls(): void {
    const lensToggle = el<HTMLButtonElement>('lensToggle');
    const pinToggle = el<HTMLButtonElement>('pinToggle');
    const revealToggle = el<HTMLButtonElement>('revealToggle');
    lensToggle.setAttribute('aria-pressed', String(state.lens.enabled));
    pinToggle.setAttribute('aria-pressed', String(state.lens.pinned));
    revealToggle.setAttribute('aria-pressed', String(state.lens.revealAll));
    lensToggle.textContent = state.lens.enabled ? 'Lens on' : 'Lens off';
    pinToggle.textContent = state.lens.pinned ? 'Lens pinned' : 'Pin lens';
    revealToggle.textContent = state.lens.revealAll ? 'Hide full overlay' : 'Reveal all';
    el<HTMLInputElement>('radiusControl').value = String(state.lens.radius);
    el('radiusValue').textContent = `${Math.round(state.lens.radius)} px`;
    el<HTMLInputElement>('reducedMotionToggle').checked = state.reducedMotion;
    el<HTMLInputElement>('patternModeToggle').checked = state.patternMode;
    document.body.classList.toggle('user-reduced-motion', state.reducedMotion);
    document.body.classList.toggle('pattern-mode', state.patternMode);
    touchHandle.hidden = !isCoarsePointer();
  }

  function renderModeBanner(): void {
    const banner = el('modeBanner');
    if (state.mode === 'synthetic_fixture') {
      banner.className = 'mode-banner fixture';
      banner.innerHTML = `<strong>SYNTHETIC FIXTURE</strong><span>Fictional cross-document material · full Compare and Event Record available.</span>`;
    } else {
      banner.className = 'mode-banner preview';
      banner.innerHTML = `<strong>LOCAL PREVIEW — UNBENCHMARKED</strong><span>Four conservative intrinsic heuristics · candidates only · no live fact checking or cross-document inference.</span>`;
    }
  }

  function renderScanStatus(): void {
    const status = el('scanStatus');
    status.textContent = state.analysisRun.stage === 'partial' ? 'Partial intrinsic scan' : state.analysisRun.stage === 'failed' ? 'Scan failed' : 'Intrinsic analysis available';
    status.dataset.stage = state.analysisRun.stage;
  }

  function renderLens(): void {
    const lens = state.lens;
    articleSurface.style.setProperty('--lens-x', `${lens.x}px`);
    articleSurface.style.setProperty('--lens-y', `${lens.y}px`);
    articleSurface.style.setProperty('--lens-r', `${lens.radius}px`);
    articleSurface.classList.toggle('lens-off', !lens.enabled);
    articleSurface.classList.toggle('reveal-all', lens.revealAll);
    articleSurface.classList.toggle('lens-live', lens.enabled && !lens.revealAll);
    articleSurface.dataset.dragging = String(lens.dragging);
    articleSurface.dataset.activePointer = lens.activePointerId === null ? '' : String(lens.activePointerId);
    renderLensReadout();
  }

  function renderLensReadout(): void {
    if (!state.lens.enabled || state.lens.revealAll) {
      lensReadout.hidden = true;
      return;
    }
    const surfaceRect = articleSurface.getBoundingClientRect();
    const centerX = surfaceRect.left + state.lens.x;
    const centerY = surfaceRect.top + state.lens.y;
    const hits = visibleFindings().filter((finding) => {
      const selector = `.base-mark[data-finding-ids~="${CSS.escape(finding.id)}"]`;
      const candidates = [...articleBase.querySelectorAll<HTMLElement>('.base-mark')].filter((mark) => (mark.dataset.findingIds || '').split(',').includes(finding.id));
      return candidates.some((mark) => {
        const rect = mark.getBoundingClientRect();
        const closestX = Math.max(rect.left, Math.min(centerX, rect.right));
        const closestY = Math.max(rect.top, Math.min(centerY, rect.bottom));
        const dx = centerX - closestX;
        const dy = centerY - closestY;
        return dx * dx + dy * dy <= state.lens.radius * state.lens.radius;
      });
    });
    if (!hits.length) {
      lensReadout.hidden = true;
      return;
    }
    lensReadout.hidden = false;
    lensReadout.innerHTML = hits.slice(0, 4).map((finding) => {
      const name = TAXONOMY.get(finding.mechanism)?.canonicalName || finding.mechanism;
      return `<button type="button" data-lens-finding="${esc(finding.id)}"><strong>${esc(name)}</strong><span>${finding.pressure} · ${esc(finding.confidence)}</span></button>`;
    }).join('');
    const left = Math.max(12, Math.min(articleSurface.clientWidth - 236, state.lens.x + state.lens.radius * 0.56));
    const top = Math.max(12, Math.min(articleSurface.scrollHeight - 110, state.lens.y - state.lens.radius * 0.6));
    lensReadout.style.left = `${left}px`;
    lensReadout.style.top = `${top}px`;
    lensReadout.querySelectorAll<HTMLButtonElement>('[data-lens-finding]').forEach((button) => {
      button.addEventListener('click', () => openFinding(button.dataset.lensFinding || ''));
    });
  }

  function getRadiusLimits(): { min: number; max: number } {
    const width = articleSurface.clientWidth || 600;
    const viewport = window.innerWidth;
    const cap = viewport <= 520 ? 132 : viewport <= 1100 ? 180 : 210;
    return { min: 78, max: Math.max(78, Math.min(cap, Math.floor(width / 2) - 16)) };
  }

  function clampLensPoint(x: number, y: number, radius = state.lens.radius): { x: number; y: number } {
    const width = articleSurface.clientWidth;
    const height = articleSurface.scrollHeight;
    const pad = Math.max(10, radius + 8);
    const clamp = (value: number, size: number) => size > pad * 2 ? Math.max(pad, Math.min(size - pad, value)) : size / 2;
    return { x: clamp(x, width), y: clamp(y, height) };
  }

  function applyLensBounds(): void {
    const limits = getRadiusLimits();
    state.lens.radius = Math.max(limits.min, Math.min(limits.max, state.lens.radius));
    const point = clampLensPoint(state.lens.x, state.lens.y, state.lens.radius);
    state.lens.x = point.x;
    state.lens.y = point.y;
    el<HTMLInputElement>('radiusControl').min = String(limits.min);
    el<HTMLInputElement>('radiusControl').max = String(limits.max);
    renderControls();
    renderLens();
  }

  function isCoarsePointer(): boolean {
    return matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0;
  }

  function touchOffset(): number {
    return window.innerWidth <= 520 ? 86 : 108;
  }

  function placeLens(clientX: number, clientY: number, touch = false): void {
    const rect = articleSurface.getBoundingClientRect();
    const localX = clientX - rect.left;
    const localY = clientY - rect.top + articleSurface.scrollTop - (touch ? touchOffset() : 0);
    const point = clampLensPoint(localX, localY);
    state.lens.x = point.x;
    state.lens.y = point.y;
    renderLens();
  }

  function openFinding(id: string, cluster?: string[]): void {
    const finding = state.findings.find((candidate) => candidate.id === id);
    if (!finding) return;
    state.selectedFindingId = finding.id;
    lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const taxonomy = TAXONOMY.get(finding.mechanism);
    const sameSpan = cluster || state.findings.filter((candidate) =>
      candidate.span.paragraphIndex === finding.span.paragraphIndex &&
      candidate.span.startChar === finding.span.startChar &&
      candidate.span.endChar === finding.span.endChar
    ).map((candidate) => candidate.id);
    const neighbors = sameSpan.filter((findingId) => findingId !== finding.id).map((findingId) => state.findings.find((item) => item.id === findingId)).filter(Boolean) as Finding[];
    el('drawerBody').innerHTML = `
      <span class="voice-chip">${esc(finding.voiceClass.replace('_', ' '))}</span>
      <h2 id="drawerTitle">${esc(taxonomy?.canonicalName || finding.mechanism)}</h2>
      <blockquote>“${esc(finding.span.text)}”</blockquote>
      <div class="drawer-metrics"><div><span>Interpretive pressure</span><strong>${finding.pressure}</strong></div><div><span>Confidence</span><strong>${esc(finding.confidence)}</strong></div></div>
      ${neighbors.length ? `<p><strong>Also on this span:</strong> ${neighbors.map((item) => esc(TAXONOMY.get(item.mechanism)?.canonicalName || item.mechanism)).join(', ')}</p>` : ''}
      <details open><summary>Why this was tagged</summary><ul>${finding.triggeredCriteria.map((criterion) => `<li>${esc(criterion)}</li>`).join('')}</ul></details>
      <details><summary>Why it could be wrong</summary><p>${esc(finding.alternateInterpretation || finding.nearMissCriteria?.join(' ') || 'No alternate interpretation is recorded for this fixture finding.')}</p></details>
      <details><summary>Taxonomy definition</summary><p>${esc(taxonomy?.definition || 'Definition unavailable.')}</p></details>
      <details><summary>Analysis provenance</summary><p>Origin: ${state.mode === 'synthetic_fixture' ? 'synthetic fixture' : 'local preview'} · detector: ${esc(finding.detectorVersion)} · taxonomy ${esc(finding.taxonomyVersion)} · run ${esc(finding.analysisRunId)}</p></details>
      <div class="drawer-actions"><button class="primary-btn" id="jumpToFinding">Jump to exact passage</button><button class="ghost-btn" id="closeFindingInline">Close</button></div>
    `;
    drawer.classList.add('open');
    drawer.removeAttribute('inert');
    drawer.setAttribute('aria-hidden', 'false');
    scrim.classList.add('open');
    state.drawerOpen = true;
    el<HTMLButtonElement>('drawerClose').focus();
    el('jumpToFinding').addEventListener('click', () => jumpToFinding(finding));
    el('closeFindingInline').addEventListener('click', closeDrawer);
    renderSelectionState();
  }

  function closeDrawer(): void {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    drawer.setAttribute('inert', '');
    scrim.classList.remove('open');
    state.drawerOpen = false;
    if (lastFocus?.isConnected) lastFocus.focus();
  }

  function drawerFocusable(): HTMLElement[] {
    return [...drawer.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, summary, [tabindex]:not([tabindex="-1"])')]
      .filter((node) => !node.hasAttribute('disabled') && node.offsetParent !== null);
  }

  function trapDrawerFocus(event: KeyboardEvent): void {
    if (!state.drawerOpen || event.key !== 'Tab') return;
    const focusable = drawerFocusable();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function jumpToFinding(finding: Finding): void {
    closeDrawer();
    const marks = [...articleBase.querySelectorAll<HTMLElement>('.base-mark')];
    const mark = marks.find((candidate) => (candidate.dataset.findingIds || '').split(',').includes(finding.id));
    if (!mark) return;
    mark.scrollIntoView({ block: 'center', behavior: state.reducedMotion ? 'auto' : 'smooth' });
    mark.focus({ preventScroll: true });
    const rect = mark.getBoundingClientRect();
    const surfaceRect = articleSurface.getBoundingClientRect();
    const point = clampLensPoint(rect.left - surfaceRect.left + rect.width / 2, rect.top - surfaceRect.top + rect.height / 2);
    state.lens.enabled = true;
    state.lens.pinned = true;
    state.lens.x = point.x;
    state.lens.y = point.y;
    renderControls();
    renderLens();
    liveRegion.textContent = `Jumped to ${TAXONOMY.get(finding.mechanism)?.canonicalName || finding.mechanism}.`;
  }

  function renderNavigation(): void {
    const views: Record<View, HTMLElement> = { scanner: scannerView, compare: compareView, event: eventView, taxonomy: taxonomyView, methodology: methodologyView };
    Object.entries(views).forEach(([name, node]) => node.classList.toggle('active', name === state.view));
    document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach((button) => {
      const active = button.dataset.view === state.view;
      button.setAttribute('aria-current', active ? 'page' : 'false');
    });
  }

  function switchView(view: View): void {
    if ((view === 'compare' || view === 'event') && state.mode !== 'synthetic_fixture') {
      state.view = view;
      renderNavigation();
      renderUnavailable(view);
      return;
    }
    state.view = view;
    renderNavigation();
    if (view === 'compare') renderCompare();
    if (view === 'event') renderEvent();
    if (view === 'taxonomy') renderTaxonomy();
  }

  function renderUnavailable(view: 'compare' | 'event'): void {
    const target = view === 'compare' ? compareView : eventView;
    target.innerHTML = `<section class="unavailable-card"><span class="eyebrow">Single-document boundary</span><h1>${view === 'compare' ? 'Comparison unavailable for this scan' : 'Event Record unavailable for this scan'}</h1><p>${view === 'compare' ? 'Peer comparison requires a validated same-event source set. This local preview does not invent one.' : 'A forensic Event Record requires cross-document claims and evidence. This local preview contains only the supplied article.'}</p><button class="primary-btn" id="returnScanner">Return to scanner</button></section>`;
    el('returnScanner').addEventListener('click', () => switchView('scanner'));
  }

  function renderCompare(): void {
    if (!state.event) return renderUnavailable('compare');
    const event = state.event;
    const claims = event.atomicClaims;
    if (!state.selectedClaimId || !claims.some((claim) => claim.id === state.selectedClaimId)) state.selectedClaimId = claims[0]?.id || null;
    const claim = claims.find((item) => item.id === state.selectedClaimId) || claims[0];
    compareView.innerHTML = `
      <section class="section-shell">
        <div class="section-heading"><div><span class="eyebrow">Compare · synthetic fixture</span><h1>Same underlying claim. Different rhetoric.</h1><p>${esc(event.description)}</p></div><button class="ghost-btn" id="compareBack">Back to scanner</button></div>
        <div class="claim-picker">${claims.map((item) => `<button class="claim-chip ${item.id === claim.id ? 'active' : ''}" data-claim="${esc(item.id)}">${esc(item.normalizedClaim)}</button>`).join('')}</div>
        <article class="claim-card"><span class="eyebrow">Atomic claim</span><h2>${esc(claim.normalizedClaim)}</h2><p>State: <strong>${esc(claim.state.replaceAll('_', ' '))}</strong> · Confidence ${esc(claim.confidence)}</p></article>
        <div class="framing-grid">${claim.sourceWordings.map((wording) => `<article class="wording-card"><div class="wording-head"><strong>${esc(wording.sourceName)}</strong><span>${wording.pressure || '—'}</span></div><blockquote>“${esc(wording.excerpt)}”</blockquote><small>${esc(wording.articleTitle)}</small></article>`).join('')}</div>
        <div class="compare-lower">
          <section class="panel-card"><span class="eyebrow">Material omission candidate</span>${event.omissions.map((omission) => `<h3>${esc(omission.dimension)}</h3><p>${esc(omission.missingClaim)}</p><p>${esc(omission.rationale)}</p><small>Knowable by ${esc(omission.knowableAtTimestamp)} · ${esc(omission.confidence)} confidence</small>`).join('')}</section>
          <section class="panel-card"><span class="eyebrow">Coverage disclosure</span><p>${event.articles.length} synthetic articles in this fixture. Independence relationships are fixture metadata, not a truth score.</p><button class="primary-btn" id="openEvent">Open Event Record</button></section>
        </div>
      </section>`;
    el('compareBack').addEventListener('click', () => switchView('scanner'));
    el('openEvent').addEventListener('click', () => switchView('event'));
    compareView.querySelectorAll<HTMLButtonElement>('[data-claim]').forEach((button) => button.addEventListener('click', () => {
      state.selectedClaimId = button.dataset.claim || null;
      renderCompare();
    }));
  }

  function evidenceLabel(item: EvidenceItem): string {
    if (item.authenticityState === 'verified') return item.directness === 'direct' ? 'Authenticated primary evidence' : 'Authenticated contextual evidence';
    if (item.authenticityState === 'disputed') return 'Disputed evidence';
    return item.directness === 'direct' ? 'Primary evidence — authenticity unverified' : 'Evidence — authenticity unverified';
  }

  function renderEvent(): void {
    if (!state.event) return renderUnavailable('event');
    const event = state.event;
    eventView.innerHTML = `
      <section class="section-shell">
        <div class="section-heading"><div><span class="eyebrow">Forensic Event Record · synthetic fixture</span><h1>${esc(event.title)}</h1><p>Versioned ledger separating what the fixture establishes from how its sources frame the event.</p></div><button class="ghost-btn" id="eventBack">Back to scanner</button></div>
        <div class="ledger-grid">
          <section class="panel-card"><span class="eyebrow">Atomic claims</span>${event.atomicClaims.map((claim) => `<article class="ledger-row"><h3>${esc(claim.normalizedClaim)}</h3><p>${esc(claim.state.replaceAll('_', ' '))} · ${esc(claim.confidence)} confidence</p></article>`).join('')}</section>
          <section class="panel-card"><span class="eyebrow">Evidence</span>${event.primaryEvidence.map((item) => `<article class="ledger-row"><span class="evidence-state ${esc(item.authenticityState)}">${esc(evidenceLabel(item))}</span><h3>${esc(item.title)}</h3><p>${esc(item.description)}</p>${item.excerptText ? `<blockquote>“${esc(item.excerptText)}”</blockquote>` : ''}</article>`).join('')}</section>
        </div>
      </section>`;
    el('eventBack').addEventListener('click', () => switchView('scanner'));
  }

  function renderTaxonomy(): void {
    taxonomyView.innerHTML = `<section class="section-shell"><div class="section-heading"><div><span class="eyebrow">Alpha-0 taxonomy · ${esc(DATA.taxonomy.version)}</span><h1>Definitions govern the instrument.</h1><p>These records are a specification surface, not benchmark results. Human-reviewed performance metrics have not yet been established.</p></div></div><div class="taxonomy-grid">${DATA.taxonomy.mechanisms.map((mechanism) => `<article class="taxonomy-card family-${esc(mechanism.family)}"><div class="taxonomy-title"><span>${esc(familyLabel(mechanism.family))}</span><strong>${esc(mechanism.canonicalName)}</strong></div><p>${esc(mechanism.definition)}</p><details><summary>Positive criteria</summary><ul>${mechanism.positiveCriteria.map((criterion) => `<li>${esc(criterion)}</li>`).join('')}</ul></details><details><summary>Exclusions</summary><ul>${mechanism.exclusionCriteria.map((criterion) => `<li>${esc(criterion)}</li>`).join('')}</ul></details><details><summary>Pressure anchors</summary><ol><li>${esc(mechanism.pressureRubric.p1)}</li><li>${esc(mechanism.pressureRubric.p2)}</li><li>${esc(mechanism.pressureRubric.p3)}</li><li>${esc(mechanism.pressureRubric.p4)}</li></ol></details></article>`).join('')}</div></section>`;
  }

  function renderMethodology(): void {
    methodologyView.innerHTML = `<section class="section-shell methodology"><div class="section-heading"><div><span class="eyebrow">Methodology</span><h1>An instrument, not a verdict machine.</h1></div></div><div class="method-grid"><article><h2>Interpretive pressure</h2><p>Pressure measures how strongly language steers or narrows interpretation. It is not factuality, political side, moral worth, or harm.</p></article><article><h2>Confidence is separate</h2><p>A strong-pressure finding can be low confidence; a light-pressure finding can be high confidence. Candidates remain visible without inflating confirmed metrics.</p></article><article><h2>Comparison is evidence-bound</h2><p>Material omission requires aligned event context, chronology, supporting coverage or evidence, materiality, and proof the target does not already state the equivalent fact.</p></article><article><h2>No hidden chain-of-thought</h2><p>The system exposes exact spans, criteria, exclusions, alternatives, provenance, and versioned records rather than private reasoning traces.</p></article></div></section>`;
  }

  function renderPastePanel(open: boolean): void {
    pastePanel.hidden = !open;
    if (open) pasteText.focus();
  }

  function sentenceChunks(paragraph: string): { start: number; end: number; text: string }[] {
    const chunks: { start: number; end: number; text: string }[] = [];
    const regex = /[^.!?]+[.!?]?/g;
    let match: RegExpExecArray | null;
    while ((match = regex.exec(paragraph)) !== null) {
      const raw = match[0];
      const leading = raw.search(/\S/);
      if (leading < 0) continue;
      const trailing = raw.length - raw.trimEnd().length;
      const start = match.index + leading;
      const end = match.index + raw.length - trailing;
      chunks.push({ start, end, text: paragraph.slice(start, end) });
    }
    return chunks;
  }

  function localPreviewFindings(article: Article): Finding[] {
    const findings: Finding[] = [];
    const runId = `local-${fnv1a(article.content)}-${Date.now()}`;
    let counter = 0;
    const add = (paragraphIndex: number, startChar: number, endChar: number, mechanism: MechanismId, pressure: PressureLevel, confidence: ConfidenceLevel, criterion: string) => {
      const paragraph = article.paragraphs[paragraphIndex];
      const text = paragraph.slice(startChar, endChar);
      const taxonomy = TAXONOMY.get(mechanism);
      if (!taxonomy || !text.trim()) return;
      counter += 1;
      findings.push({
        id: `local-${counter}`,
        articleId: article.id,
        span: { startChar, endChar, paragraphIndex, text },
        mechanism,
        family: taxonomy.family,
        pressure,
        confidence,
        state: 'candidate',
        voiceClass: 'reporter',
        triggeredCriteria: [criterion],
        nearMissCriteria: ['Local preview heuristics are intentionally recall-oriented and have not been benchmarked.'],
        alternateInterpretation: 'This is a candidate requiring contextual verification against the full taxonomy before production use.',
        taxonomyVersion: DATA.taxonomy.version,
        detectorVersion: 'local-preview-4mechanism-v1',
        analysisRunId: runId,
        timestamp: new Date().toISOString(),
      });
    };

    const loaded = /\b(?:draconian|reckless|outrageous|catastrophic|devastating|disastrous|brutal|shameful|cynical|heroic)\b/gi;
    const dilemmaPatterns = [/\beither\b[^.!?]{0,120}\bor\b[^.!?]{0,120}/gi, /\b(?:no alternative|only two (?:choices|options)|with us or against us)\b/gi];
    const presuppPatterns = [/\b(?:refused|failed) to explain why\b[^.!?]*/gi, /\b(?:still|again|finally|continues? to)\b[^.!?]*/gi];
    const passive = /\b(?:was|were|is|are|been|be)\s+[a-z]+(?:ed|en)\b[^.!?]{0,70}/gi;

    article.paragraphs.forEach((paragraph, paragraphIndex) => {
      let match: RegExpExecArray | null;
      loaded.lastIndex = 0;
      while ((match = loaded.exec(paragraph)) !== null) {
        add(paragraphIndex, match.index, match.index + match[0].length, 'loaded_language', 'P2', 'Medium', `Candidate evaluative term: “${match[0]}”.`);
      }
      dilemmaPatterns.forEach((pattern) => {
        pattern.lastIndex = 0;
        while ((match = pattern.exec(paragraph)) !== null) add(paragraphIndex, match.index, match.index + match[0].length, 'false_dilemma', 'P3', 'Medium', 'Candidate binary framing narrows a more complex option space.');
      });
      presuppPatterns.forEach((pattern) => {
        pattern.lastIndex = 0;
        while ((match = pattern.exec(paragraph)) !== null) add(paragraphIndex, match.index, match.index + match[0].length, 'presupposition', 'P2', 'Low', 'Candidate construction embeds a premise as background rather than presenting it for evaluation.');
      });
      passive.lastIndex = 0;
      while ((match = passive.exec(paragraph)) !== null) {
        if (/\bby\b/i.test(match[0])) continue;
        add(paragraphIndex, match.index, match.index + match[0].length, 'agent_suppression', 'P2', 'Low', 'Candidate passive construction does not name an actor inside the detected span.');
      }
    });
    return findings;
  }

  function loadPasteArticle(): void {
    const raw = pasteText.value.trim();
    if (!raw) {
      liveRegion.textContent = 'Paste article text before running the local preview.';
      return;
    }
    const paragraphs = raw.split(/\n\s*\n|\n+/).map((paragraph) => paragraph.trim()).filter(Boolean);
    const content = paragraphs.join('\n\n');
    const hash = fnv1a(content);
    const article: Article = {
      id: `local-${hash}`,
      sourceId: 'user-paste',
      title: 'User-provided article text',
      publisher: 'Local paste',
      url: '',
      publishedAt: '',
      extractedAt: new Date().toISOString(),
      content,
      paragraphs,
      snapshotHash: hash,
    };
    const findings = localPreviewFindings(article);
    state.mode = 'local_preview';
    state.article = article;
    state.findings = findings;
    state.event = null;
    state.selectedFindingId = null;
    state.selectedClaimId = null;
    state.filters = { family: 'all', confidence: 'all', search: '' };
    state.analysisRun = makeAnalysisRun('local_preview', article, findings, 'local-preview-4mechanism-v1', 'complete');
    state.analysisRun.runId = findings[0]?.analysisRunId || state.analysisRun.runId;
    state.analysisRun.articleSnapshotHash = hash;
    renderPastePanel(false);
    state.view = 'scanner';
    renderAll();
    liveRegion.textContent = `Local preview complete. ${findings.length} candidate findings. Comparison is unavailable for single-document scans.`;
  }

  function loadFixture(): void {
    state.mode = 'synthetic_fixture';
    state.article = fixtureArticle;
    state.findings = fixtureFindings;
    state.event = fixtureEvent;
    state.selectedFindingId = null;
    state.selectedClaimId = fixtureEvent.atomicClaims[0]?.id || null;
    state.filters = { family: 'all', confidence: 'all', search: '' };
    state.analysisRun = makeAnalysisRun('synthetic_fixture', fixtureArticle, fixtureFindings, 'fixture-reviewed-v1', 'complete');
    state.view = 'scanner';
    renderAll();
    liveRegion.textContent = 'Synthetic fixture restored.';
  }


  function syncTopbarHeight(): void {
    const topbar = document.getElementById('topbar');
    if (!topbar) return;
    document.documentElement.style.setProperty('--topbar-h', `${Math.ceil(topbar.getBoundingClientRect().height)}px`);
  }

  function renderAll(): void {
    renderNavigation();
    renderModeBanner();
    renderScanStatus();
    renderProfile();
    renderFilters();
    renderControls();
    renderArticle();
    renderFindings();
    if (state.view === 'compare') state.mode === 'synthetic_fixture' ? renderCompare() : renderUnavailable('compare');
    if (state.view === 'event') state.mode === 'synthetic_fixture' ? renderEvent() : renderUnavailable('event');
    if (state.view === 'taxonomy') renderTaxonomy();
    if (state.view === 'methodology') renderMethodology();
  }

  function setupEvents(): void {
    document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.view as View)));
    document.querySelectorAll<HTMLElement>('[data-action="load-demo"]').forEach((node) => node.addEventListener('click', loadFixture));
    document.querySelectorAll<HTMLElement>('[data-action="open-paste"]').forEach((node) => node.addEventListener('click', () => renderPastePanel(true)));
    el('cancelPaste').addEventListener('click', () => renderPastePanel(false));
    el('runPaste').addEventListener('click', loadPasteArticle);
    el('lensToggle').addEventListener('click', () => { state.lens.enabled = !state.lens.enabled; if (!state.lens.enabled) state.lens.pinned = false; renderControls(); renderLens(); });
    el('pinToggle').addEventListener('click', () => { state.lens.enabled = true; state.lens.pinned = !state.lens.pinned; renderControls(); renderLens(); });
    el('revealToggle').addEventListener('click', () => { state.lens.revealAll = !state.lens.revealAll; renderControls(); renderLens(); });
    el<HTMLInputElement>('radiusControl').addEventListener('input', (event) => { state.lens.radius = Number((event.target as HTMLInputElement).value); applyLensBounds(); });
    el<HTMLSelectElement>('familyFilter').addEventListener('change', (event) => { state.filters.family = (event.target as HTMLSelectElement).value as Filters['family']; renderArticle(); renderFindings(); renderLens(); });
    el<HTMLSelectElement>('confidenceFilter').addEventListener('change', (event) => { state.filters.confidence = (event.target as HTMLSelectElement).value as Filters['confidence']; renderArticle(); renderFindings(); renderLens(); });
    el<HTMLInputElement>('findingSearch').addEventListener('input', (event) => { state.filters.search = (event.target as HTMLInputElement).value; renderArticle(); renderFindings(); renderLens(); });
    el<HTMLInputElement>('reducedMotionToggle').addEventListener('change', (event) => { state.reducedMotion = (event.target as HTMLInputElement).checked; saveSettings(); renderControls(); });
    el<HTMLInputElement>('patternModeToggle').addEventListener('change', (event) => { state.patternMode = (event.target as HTMLInputElement).checked; saveSettings(); renderControls(); });
    el('drawerClose').addEventListener('click', closeDrawer);
    scrim.addEventListener('click', closeDrawer);

    articleSurface.addEventListener('pointermove', (event) => {
      if (event.pointerType === 'mouse' && state.lens.enabled && !state.lens.pinned && !state.lens.revealAll) placeLens(event.clientX, event.clientY, false);
    });
    articleSurface.addEventListener('pointerdown', (event) => {
      if (event.pointerType === 'mouse') return;
      touchTapStart = { id: event.pointerId, x: event.clientX, y: event.clientY, t: performance.now() };
    });
    articleSurface.addEventListener('pointerup', (event) => {
      if (!touchTapStart || touchTapStart.id !== event.pointerId) return;
      const distance = Math.hypot(event.clientX - touchTapStart.x, event.clientY - touchTapStart.y);
      const duration = performance.now() - touchTapStart.t;
      if (distance < 12 && duration < 420) {
        state.lens.enabled = true;
        state.lens.pinned = true;
        placeLens(event.clientX, event.clientY, true);
        renderControls();
      }
      touchTapStart = null;
    });
    articleSurface.addEventListener('pointercancel', () => { touchTapStart = null; });

    touchHandle.addEventListener('pointerdown', (event) => {
      state.lens.enabled = true;
      state.lens.pinned = true;
      state.lens.dragging = true;
      state.lens.activePointerId = event.pointerId;
      try { touchHandle.setPointerCapture?.(event.pointerId); } catch { /* Synthetic/unsupported pointer capture: ownership state still remains explicit. */ }
      event.preventDefault();
      placeLens(event.clientX, event.clientY, true);
      renderControls();
    });
    touchHandle.addEventListener('pointermove', (event) => {
      if (!state.lens.dragging || state.lens.activePointerId !== event.pointerId) return;
      event.preventDefault();
      placeLens(event.clientX, event.clientY, true);
    });
    const endHandleDrag = (event: PointerEvent) => {
      if (state.lens.activePointerId !== event.pointerId) return;
      try { if (touchHandle.hasPointerCapture?.(event.pointerId)) touchHandle.releasePointerCapture(event.pointerId); } catch { /* Capture may already be gone after cancellation. */ }
      state.lens.dragging = false;
      state.lens.activePointerId = null;
      renderControls();
      renderLens();
    };
    touchHandle.addEventListener('pointerup', endHandleDrag);
    touchHandle.addEventListener('pointercancel', endHandleDrag);

    window.addEventListener('resize', () => requestAnimationFrame(() => { syncTopbarHeight(); applyLensBounds(); verifyOverlayGeometry(false); }));
    window.addEventListener('orientationchange', () => requestAnimationFrame(() => { syncTopbarHeight(); applyLensBounds(); verifyOverlayGeometry(false); }));
    window.visualViewport?.addEventListener('resize', () => requestAnimationFrame(() => { syncTopbarHeight(); applyLensBounds(); verifyOverlayGeometry(false); }));
    const topbar = document.getElementById('topbar');
    if (topbar && 'ResizeObserver' in window) {
      topbarObserver?.disconnect();
      topbarObserver = new ResizeObserver(() => requestAnimationFrame(syncTopbarHeight));
      topbarObserver.observe(topbar);
    }

    document.addEventListener('keydown', (event) => {
      trapDrawerFocus(event);
      if (event.key === 'Escape') {
        if (state.drawerOpen) closeDrawer();
        else if (!pastePanel.hidden) renderPastePanel(false);
        return;
      }
      const target = event.target as HTMLElement;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return;
      if (event.key.toLowerCase() === 'l') { state.lens.enabled = !state.lens.enabled; renderControls(); renderLens(); }
      if (event.key.toLowerCase() === 'a') { state.lens.revealAll = !state.lens.revealAll; renderControls(); renderLens(); }
      if (event.key.toLowerCase() === 'c') switchView('compare');
      if (event.key.toLowerCase() === 'e') switchView('event');
      if (event.key === '?') el('shortcutHelp').classList.toggle('open');
      if (event.key.toLowerCase() === 'j' || event.key.toLowerCase() === 'k') {
        const findings = visibleFindings();
        if (!findings.length) return;
        const index = Math.max(0, findings.findIndex((finding) => finding.id === state.selectedFindingId));
        const direction = event.key.toLowerCase() === 'j' ? 1 : -1;
        const next = findings[(index + direction + findings.length) % findings.length];
        jumpToFinding(next);
      }
    });
  }

  setupEvents();
  syncTopbarHeight();
  renderMethodology();
  renderTaxonomy();
  renderAll();
})();
