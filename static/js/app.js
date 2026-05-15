document.querySelectorAll('.flash').forEach((el) => {
  setTimeout(() => {
    el.style.opacity = '0.2';
  }, 4500);
});
