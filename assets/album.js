(function(){
  var lb=document.getElementById('lb'), im=lb.querySelector('img'), cap=lb.querySelector('.lb-cap'), rot=lb.querySelector('.lb-rot');
  var portraitPhone=window.matchMedia('(orientation: portrait) and (max-width: 760px)');
  function hint(){ if(cur<0||lb.hidden)return; var i=figs[cur].querySelector('img'); rot.hidden=!(portraitPhone.matches && (+i.getAttribute('width'))/(+i.getAttribute('height'))>=1.6); }
  if(portraitPhone.addEventListener)portraitPhone.addEventListener('change',hint);
  var figs=[].slice.call(document.querySelectorAll('.fig')), cur=-1, last=null;
  function show(i){
    cur=(i+figs.length)%figs.length;
    var f=figs[cur], src=f.querySelector('img'), t=f.querySelector('strong');
    im.src=src.getAttribute('data-full')||src.currentSrc||src.src; im.alt=src.alt; cap.textContent=t?t.textContent:'';
    lb.hidden=false; hint(); document.body.style.overflow='hidden'; lb.querySelector('.lb-x').focus();
  }
  function hide(){lb.hidden=true;document.body.style.overflow='';if(last)last.focus();}
  figs.forEach(function(f,i){f.querySelector('.ph').addEventListener('click',function(){last=this;show(i);});});
  lb.addEventListener('click',function(){ if(!swiped)hide(); swiped=false; });
  var x0=null, swiped=false;
  lb.addEventListener('touchstart',function(e){x0=e.touches[0].clientX;},{passive:true});
  lb.addEventListener('touchend',function(e){ if(x0===null)return; var dx=e.changedTouches[0].clientX-x0; x0=null;
    if(Math.abs(dx)>50){ swiped=true; show(cur+(dx<0?1:-1)); setTimeout(function(){swiped=false;},400); } });
  document.addEventListener('keydown',function(e){
    if(lb.hidden)return;
    if(e.key==='Escape')hide();
    else if(e.key==='ArrowRight'){e.preventDefault();show(cur+1);}
    else if(e.key==='ArrowLeft'){e.preventDefault();show(cur-1);}
  });
  document.addEventListener('contextmenu',function(e){if(e.target.tagName==='IMG')e.preventDefault();});
  document.addEventListener('dragstart',function(e){if(e.target.tagName==='IMG')e.preventDefault();});
})();
