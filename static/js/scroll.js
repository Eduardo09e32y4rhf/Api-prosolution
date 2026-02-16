const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
    }
  });
}, {
  threshold: 0.15
});

// Seleciona TODAS as seções e cards
document.querySelectorAll(
  "section, .card, .step, .mock, .stack-grid div"
).forEach(el => {
  el.classList.add("reveal");
  observer.observe(el);
});
