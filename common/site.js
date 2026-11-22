/* Comportamenti comuni a tutte le pagine: barra di navigazione e animazioni di comparsa.
   Chi ha chiesto al sistema di ridurre il movimento vede la pagina ferma. */
(function(){
  var nav = document.querySelector('.gnav'), cover = document.querySelector('.cover');
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Barra: trasparente sopra la foto di copertina, scura appena si scorre
  function navState(){
    var limit = cover ? cover.offsetHeight * 0.12 : 0;
    var past = window.scrollY > limit;
    nav.classList.toggle('solid', !cover || past);
    nav.classList.toggle('on-cover', !!cover && !past && document.body.classList.contains('home'));
  }
  navState(); window.addEventListener('scroll', navState, {passive:true}); window.addEventListener('resize', navState);

  // Copertina: parte solo quando la foto è caricata e pronta, così non ci sono scatti
  if (cover) {
    var cimg = cover.querySelector('img'), done = false;
    var ready = function(){ if (done) return; done = true; cover.classList.add('ready'); };
    var decoded = function(){ (cimg.decode ? cimg.decode() : Promise.resolve()).then(ready, ready); };
    if (cimg.complete && cimg.naturalWidth) decoded(); else cimg.addEventListener('load', decoded, {once:true});
    cimg.addEventListener('error', ready, {once:true});
    setTimeout(ready, 5000);                          // in ogni caso, dopo 5 secondi si mostra
  }

  // Copertina: la foto scorre un po' più lenta della pagina (profondità); si muove il contenitore, non la foto.
  // Solo con mouse o trackpad: su telefoni e tablet lo scorrimento a dito lo renderebbe a scatti.
  // Dove il browser sa farlo da solo (animation-timeline in style.css), lo script non serve.
  var layer = cover && cover.querySelector('picture');
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var native = window.CSS && CSS.supports && CSS.supports('animation-timeline: scroll()');
  if (layer && !still && fine && !native) {
    var ticking = false;
    window.addEventListener('scroll', function(){
      if (ticking) return; ticking = true;
      requestAnimationFrame(function(){
        var y = Math.min(window.scrollY, cover.offsetHeight);
        layer.style.transform = 'translate3d(0,' + (y * 0.3).toFixed(1) + 'px,0)';
        ticking = false;
      });
    }, {passive:true});
  }

  // Indice dei capitoli (album): compare mentre si scorrono i capitoli e dice in quale ci si trova
  var chnav = document.querySelector('.chnav');
  if (chnav) {
    var chs = [].slice.call(document.querySelectorAll('main .ch')), end = document.querySelector('.colophon');
    var btn = chnav.querySelector('.chnav-btn'), num = chnav.querySelector('.chnav-n b'), tit = chnav.querySelector('.chnav-t');
    var links = [].slice.call(chnav.querySelectorAll('.chnav-list a')), at = -1, queued = false;
    var setOpen = function(on){ chnav.classList.toggle('open', on); btn.setAttribute('aria-expanded', on ? 'true' : 'false'); };
    var update = function(){
      queued = false;
      var h = window.innerHeight, i = -1;
      chs.forEach(function(c, k){ if (c.getBoundingClientRect().top <= h * 0.45) i = k; });
      var visible = i >= 0 && (!end || end.getBoundingClientRect().top > h * 0.6);
      chnav.classList.toggle('show', visible);
      // avanzamento: da inizio del primo capitolo all'inizio del colophon
      var y0 = chs[0].getBoundingClientRect().top, y1 = (end || chs[chs.length - 1]).getBoundingClientRect().top;
      prog = Math.min(1, Math.max(0, (h * 0.45 - y0) / Math.max(1, y1 - y0)));
      ring();
      if (!visible) setOpen(false);
      if (i >= 0 && i !== at) {
        var first = at < 0; at = i;
        links.forEach(function(a, k){ if (k === i) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
        if (first || !visible) { num.textContent = i + 1; tit.textContent = links[i].lastChild.textContent; return; }
        // cambio di capitolo: la pillola si allarga o si stringe con calma e il nuovo titolo emerge da sfocato a nitido
        var w0 = btn.offsetWidth;
        num.textContent = i + 1; tit.textContent = links[i].lastChild.textContent;
        btn.style.width = ''; var w1 = btn.offsetWidth;
        btn.style.width = w0 + 'px'; void btn.offsetWidth; btn.style.width = w1 + 'px';
        clearTimeout(wt); wt = setTimeout(function(){ btn.style.width = ''; }, 700);
        tit.classList.remove('swap'); void tit.offsetWidth; tit.classList.add('swap');
      }
    };
    // contorno di avanzamento: una linea ocra percorre il bordo della pillola, partendo dall'alto al centro
    var rp = chnav.querySelector('.chnav-ring path'), prog = 0, wt;
    var ring = function(){
      var w = btn.offsetWidth, hh = btn.offsetHeight, q = 0.6, R = hh / 2 - q;
      if (!w || !hh) return;
      rp.setAttribute('d', 'M' + w/2 + ' ' + q + 'H' + (w - hh/2) + 'A' + R + ' ' + R + ' 0 0 1 ' + (w - hh/2) + ' ' + (hh - q) +
        'H' + hh/2 + 'A' + R + ' ' + R + ' 0 0 1 ' + hh/2 + ' ' + q + 'Z');
      var L = 2 * (w - hh) + 2 * Math.PI * R;
      rp.style.strokeDasharray = L; rp.style.strokeDashoffset = L * (1 - prog);
    };
    if (window.ResizeObserver) new ResizeObserver(ring).observe(btn);
    var later = function(){ if (!queued) { queued = true; requestAnimationFrame(update); } };
    update(); window.addEventListener('scroll', later, {passive:true}); window.addEventListener('resize', later);
    btn.addEventListener('click', function(){ setOpen(!chnav.classList.contains('open')); });
    links.forEach(function(a){ a.addEventListener('click', function(){ setOpen(false); }); });
    document.addEventListener('click', function(e){ if (!chnav.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && chnav.classList.contains('open')) { setOpen(false); btn.focus(); } });
  }

  if (still || !('IntersectionObserver' in window)) return;

  // Comparsa allo scorrimento: stessi tempi e stessa curva per tutto il sito
  var sel = '.statement p, .sec-head, .alb, .contact .mail, .contact ul, .lede, .map-head, .ch-head, .fig, .colophon h2, .colophon dl, .copy';
  var els = [].slice.call(document.querySelectorAll(sel));
  els.forEach(function(el){
    // elementi affiancati compaiono uno dopo l'altro
    var sibs = el.parentElement ? [].slice.call(el.parentElement.children).filter(function(c){ return c.matches(sel); }) : [];
    var k = sibs.indexOf(el);
    if (k > 0) el.style.setProperty('--d', Math.min(k, 4) * (el.classList.contains('fig') || el.classList.contains('alb') ? 0.3 : 0.12) + 's');
    el.classList.add('rv');
  });
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (!e.isIntersecting) return;
      var el = e.target; io.unobserve(el);
      var show = function(){
        if (el.classList.contains('in')) return;
        el.classList.add('in');
        // a comparsa finita, l'elemento torna normale (così le reazioni al puntatore restano quelle di sempre)
        setTimeout(function(){ el.classList.remove('rv', 'in'); el.style.removeProperty('--d'); }, 7000);
      };
      // una foto compare solo quando è caricata: niente immagini che spuntano a metà animazione
      var im = (el.classList.contains('fig') || el.classList.contains('alb')) && el.querySelector('img');
      if (!im || (im.complete && im.naturalWidth)) { requestAnimationFrame(show); return; }
      im.addEventListener('load', function(){ requestAnimationFrame(show); }, {once:true});
      im.addEventListener('error', show, {once:true});
      setTimeout(show, 4000);
    });
  }, {rootMargin:'0px 0px -8% 0px', threshold:0.08});
  els.forEach(function(el){ io.observe(el); });
})();
