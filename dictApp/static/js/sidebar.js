document.getElementById('sidebar').addEventListener('click', function(e) {
  const clickedItem = e.target.closest('.nav-item');
  if (!clickedItem) return;

  this.querySelectorAll('.sidebar-item').forEach(item => item.classList.remove('sidebar-active'));
  this.querySelectorAll('.nav-label').forEach(item => item.classList.remove('label-active'));

  clickedItem.querySelector('.sidebar-item').classList.add('sidebar-active');
  clickedItem.querySelector('.nav-label').classList.add('label-active');
});