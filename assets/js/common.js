(() => {
  const menuBtn=document.querySelector('.menu-btn');
  const nav=document.getElementById('mainNav');
  if(menuBtn && nav){
    menuBtn.addEventListener('click',()=>{
      const opened=nav.classList.toggle('open');
      menuBtn.setAttribute('aria-expanded',String(opened));
    });
  }

  document.addEventListener('click',e=>{
    const goalLink=e.target.closest('[data-goal]');
    if(goalLink && window.arucoGoal){
      window.arucoGoal(goalLink.dataset.goal,{href:goalLink.href||'',page:location.pathname});
    }

    const copy=e.target.closest('.copy-code');
    if(copy){
      const code=copy.closest('.code-block')?.querySelector('code')?.innerText || '';
      navigator.clipboard?.writeText(code).then(()=>{
        const old=copy.textContent;
        copy.textContent='Скопировано';
        setTimeout(()=>copy.textContent=old,1200);
      });
    }
  });

  const cookie=document.querySelector('.cookie-banner');
  const accept=document.querySelector('.js-cookie-accept');
  if(cookie && accept){
    if(localStorage.getItem('aruco_cookie_ok')==='1') cookie.hidden=true;
    accept.addEventListener('click',()=>{
      localStorage.setItem('aruco_cookie_ok','1');
      cookie.hidden=true;
    });
  }

})();
