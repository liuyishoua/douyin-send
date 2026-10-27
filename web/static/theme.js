/* Standalone workbenches share preferences and colors, never account data. */
(() => {
  const root=document.documentElement;
  const read=()=>{try{const value=localStorage.getItem('workspace-theme')||localStorage.getItem('theme-mode');return value==='light'?'light':'dark';}catch{return 'dark';}};
  const symbol={dark:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/>',light:'<path d="M20.5 13A9 9 0 0 1 11 3.5 9 9 0 1 0 20.5 13z"/>'};
  function update(theme){
    root.dataset.workspaceTheme=theme;
    document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
      const label=theme==='dark'?'切换为浅色模式':'切换为深色模式';
      button.title=label;button.setAttribute('aria-label',label);
      if(button.dataset.symbol!==theme){button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round">'+symbol[theme]+'</svg>';button.dataset.symbol=theme;}
    });
  }
  update(read());
  function mount(){
    const target=[...document.querySelectorAll('.topbar-right,.topbar .actions,.topbar > .row:last-child,.topbar,header .toolbar,.dashheader .row')].find(node=>!node.closest('[hidden]')&&node.getClientRects().length);
    const existing=document.querySelector('[data-theme-toggle]');
    if(existing){
      if(target&&existing.classList.contains('theme-toggle-floating')){target.prepend(existing);existing.classList.remove('theme-toggle-floating');}
      else if(!target&&document.querySelector('.login-card')&&!existing.classList.contains('theme-toggle-floating')){document.body.append(existing);existing.classList.add('theme-toggle-floating');}
      update(root.dataset.workspaceTheme);return;
    }
    if(!target&&!document.querySelector('.login-card'))return;
    const button=document.createElement('button');button.type='button';button.className='theme-toggle';button.dataset.themeToggle='true';
    if(target)target.prepend(button);else{button.classList.add('theme-toggle-floating');document.body.append(button);}
    update(root.dataset.workspaceTheme);
  }
  document.addEventListener('click',event=>{
    if(!event.target.closest('[data-theme-toggle]'))return;
    const next=root.dataset.workspaceTheme==='dark'?'light':'dark';
    try{localStorage.setItem('workspace-theme',next);localStorage.setItem('theme-mode',next);}catch{/* Preference remains valid for this window. */}
    update(next);
  });
  window.addEventListener('storage',event=>{if(event.key==='workspace-theme'||event.key==='theme-mode'||event.key===null)update(read());});
  const start=()=>{mount();new MutationObserver(mount).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden']});};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
