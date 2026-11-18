"""Boundary-only wheel handoffs; section contents keep normal page scrolling."""
import streamlit as st

def install_scroll_story():
    st.iframe('''<script>
(() => {
  const host = window.parent, doc = host.document;
  const previous = host.__campaignRunwayScroll;
  if (previous) previous.destroy();
  const main = doc.querySelector('[data-testid="stMain"]');
  if (!main) return;
  const selector = '.st-key-chapter_question,.st-key-chapter_audience,.st-key-chapter_patterns,.st-key-chapter_simulation,.st-key-chapter_answer';
  let locked = null, animation = 0, intent = 0, lastDirection = 0;
  const reduced = host.matchMedia('(prefers-reduced-motion: reduce)');
  function geometry() {
    const origin = main.getBoundingClientRect().top;
    const pad = parseFloat(host.getComputedStyle(main).scrollPaddingTop) || 60;
    return [...doc.querySelectorAll(selector)].map(node => {
      const r = node.getBoundingClientRect();
      return {node, start: r.top-origin+main.scrollTop-pad,
              bottom: r.bottom-origin+main.scrollTop};
    });
  }
  function settle() {
    if (!locked) return;
    const now = performance.now();
    if ((Math.abs(main.scrollTop-locked.target)<3 && now-locked.lastWheel>150) || now-locked.started>1300) {
      locked=null; intent=0; animation=0; return;
    }
    animation=requestAnimationFrame(settle);
  }
  function go(section) {
    const target=Math.max(0,section.start);
    locked={target,started:performance.now(),lastWheel:performance.now()};
    main.scrollTo({top:target,behavior:reduced.matches?'instant':'smooth'});
    cancelAnimationFrame(animation); animation=requestAnimationFrame(settle);
  }
  function wheel(event) {
    if (event.ctrlKey || Math.abs(event.deltaX)>Math.abs(event.deltaY) || !event.deltaY) return;
    if (event.target.closest('input,textarea,select,[role="slider"],[role="listbox"],[role="combobox"]')) return;
    if (locked) { event.preventDefault(); locked.lastWheel=performance.now(); return; }
    const sections=geometry(); if (sections.length<2) return;
    let index=0;
    sections.forEach((s,i) => { if (s.start<=main.scrollTop+12) index=i; });
    const section=sections[index], direction=Math.sign(event.deltaY);
    const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?main.clientHeight:1);
    if (lastDirection!==direction) intent=0;
    lastDirection=direction;
    // Let a long section reach its real bottom before handing off. Short
    // sections retain a viewport-sized stop without a second native snap.
    const atBottom=main.scrollTop+main.clientHeight>=section.bottom-6;
    const atTop=main.scrollTop<=section.start+20;
    if ((direction>0 && atBottom && index<sections.length-1) || (direction<0 && atTop && index>0)) {
      intent+=Math.abs(event.deltaY);
      if (intent<22) return;
      event.preventDefault(); go(sections[index+direction]);
    } else {
      intent=0;
      // Large wheel/trackpad deltas must stop at the current section boundary
      // before a later gesture hands off to the next section.
      const end=Math.max(section.start,section.bottom-main.clientHeight);
      if(direction>0 && main.scrollTop<end-6 && main.scrollTop+delta>=end){
        event.preventDefault();go({start:end});
      } else if(direction<0 && main.scrollTop>section.start+20 && main.scrollTop+delta<=section.start){
        event.preventDefault();go(section);
      }
    }
  }
  function link(event) {
    const anchor=event.target.closest('a.story-continue'); if (!anchor) return;
    const id=anchor.getAttribute('href')?.slice(1), target=id && doc.getElementById(id);
    const chapter=target?.closest(selector); if (!chapter) return;
    const section=geometry().find(s=>s.node===chapter); if (!section) return;
    event.preventDefault(); go(section);
  }
  main.addEventListener('wheel',wheel,{passive:false});
  main.addEventListener('click',link);
  host.__campaignRunwayScroll={destroy() {
    main.removeEventListener('wheel',wheel); main.removeEventListener('click',link);
    cancelAnimationFrame(animation);
  }};
})();
</script>''',height=1,tab_index=-1,alt='Section boundary navigation')
