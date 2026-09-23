(function(){
  var b=document.getElementById('partager');
  if(!b) return;
  var en=document.documentElement.lang==='en';
  b.addEventListener('click',function(){
    var u=location.href.split('#')[0], t=document.title;
    if(navigator.share){ navigator.share({title:t,url:u}).catch(function(){}); return; }
    var ok=function(){ b.textContent = en ? 'Link copied' : 'Lien copié'; };
    if(navigator.clipboard) navigator.clipboard.writeText(u).then(ok,function(){});
  });
})();
