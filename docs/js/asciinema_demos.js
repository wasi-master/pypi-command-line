/* Instantiate an asciinema player for every <div class="asciinema-demo" data-cast="..."> */
function createAsciinemaPlayer (el) {
  /* cols/rows come from the cast header so each player is exactly as tall
     as its content — do not override them here. */
  AsciinemaPlayer.create(el.dataset.cast, el, {
    fit: 'width',
    terminalFontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace",
    /* box-drawing glyphs only fill the font's em box, so the default 1.33
       line height leaves gaps that break panel borders into dashes */
    terminalLineHeight: 1.0,
    theme: el.dataset.theme || 'dracula',
    idleTimeLimit: 2,
    /* a time past the end of every cast, so the poster shows the finished
       output and the demo is readable without pressing play */
    poster: 'npt:1:00:00'
  })
}

function initAsciinemaDemos () {
  if (typeof AsciinemaPlayer === 'undefined') { return }
  const demos = document.querySelectorAll('div.asciinema-demo')
  for (let i = 0; i < demos.length; i++) {
    const el = demos[i]
    if (el.dataset.initialized === 'true') { continue }
    el.dataset.initialized = 'true'

    /* A player created while hidden (e.g. inside a closed <details>) measures
       a zero-width container and renders broken — defer creation until the
       element is actually visible. Also lazy-loads casts further down the page. */
    if (el.offsetWidth === 0 && typeof IntersectionObserver !== 'undefined') {
      const observer = new IntersectionObserver(function (entries) {
        for (let j = 0; j < entries.length; j++) {
          if (entries[j].isIntersecting) {
            observer.disconnect()
            createAsciinemaPlayer(el)
            return
          }
        }
      })
      observer.observe(el)
    } else {
      createAsciinemaPlayer(el)
    }
  }
}

/* mkdocs-material's instant navigation swaps the page without a full reload,
   so hook into its document$ observable when available. */
if (typeof document$ !== 'undefined') {
  document$.subscribe(initAsciinemaDemos)
} else {
  window.addEventListener('load', initAsciinemaDemos)
}
