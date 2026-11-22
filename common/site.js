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
