(function(){
  var lb=document.getElementById('lb'), im=lb.querySelector('img'), cap=lb.querySelector('p');
  var figs=[].slice.call(document.querySelectorAll('.fig')), cur=-1, last=null;
  function show(i){
    cur=(i+figs.length)%figs.length;
    var f=figs[cur], src=f.querySelector('img'), t=f.querySelector('strong');
    im.src=src.getAttribute('data-full')||src.currentSrc||src.src; im.alt=src.alt; cap.textContent=t?t.textContent:'';
    lb.hidden=false; document.body.style.overflow='hidden'; lb.querySelector('.lb-x').focus();
  }
  function hide(){lb.hidden=true;document.body.style.overflow='';if(last)last.focus();}
  figs.forEach(function(f,i){f.querySelector('.ph').addEventListener('click',function(){last=this;show(i);});});
  lb.addEventListener('click',hide);
  document.addEventListener('keydown',function(e){
    if(lb.hidden)return;
    if(e.key==='Escape')hide();
    else if(e.key==='ArrowRight'){e.preventDefault();show(cur+1);}
    else if(e.key==='ArrowLeft'){e.preventDefault();show(cur-1);}
  });
  document.addEventListener('contextmenu',function(e){if(e.target.tagName==='IMG')e.preventDefault();});
  document.addEventListener('dragstart',function(e){if(e.target.tagName==='IMG')e.preventDefault();});
})();
