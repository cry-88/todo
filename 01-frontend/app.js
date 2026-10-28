// ===== 数据层：待办存在内存数组里，localStorage 负责刷新后恢复 =====
let todos = JSON.parse(localStorage.getItem('todos') || '[]');
let currentFilter = 'all';

// ===== 渲染层：数据 -> 界面。数据每变一次，整个列表重画一次 =====
// 这就是前端最核心的心智模型：你只负责改数据，画面交给 render()
function render() {
  const list = document.getElementById('todo-list');
  list.innerHTML = '';

  const visible = todos.filter(t => {
    if (currentFilter === 'active') return !t.done;
    if (currentFilter === 'done') return t.done;
    return true;
  });

  visible.forEach(todo => {
    const li = document.createElement('li');
    li.className = 'todo-item' + (todo.done ? ' done' : '');
    li.innerHTML = `
      <input type="checkbox" ${todo.done ? 'checked' : ''} data-id="${todo.id}">
      <span class="todo-text">${escapeHtml(todo.text)}</span>
      <button class="delete" data-id="${todo.id}">×</button>
    `;
    list.appendChild(li);
  });

  const left = todos.filter(t => !t.done).length;
  document.getElementById('todo-count').textContent = `还剩 ${left} 项`;

  localStorage.setItem('todos', JSON.stringify(todos));
}

// 转义用户输入，防止把待办文字写成 HTML 标签执行（安全好习惯）
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// ===== 事件层：界面 -> 数据。用户在页面上的每个操作，最终都是改 todos 数组 =====

// 添加：表单提交（回车和点按钮都算提交）
document.getElementById('todo-form').addEventListener('submit', e => {
  e.preventDefault();
  const input = document.getElementById('todo-input');
  const text = input.value.trim();
  if (!text) return;
  todos.push({ id: Date.now(), text, done: false });
  input.value = '';
  render();
});

// 勾选 / 删除：事件委托——整个列表只挂一个监听，靠 data-id 找到是哪一条
document.getElementById('todo-list').addEventListener('click', e => {
  const id = Number(e.target.dataset.id);
  if (e.target.type === 'checkbox') {
    const todo = todos.find(t => t.id === id);
    if (todo) { todo.done = !todo.done; render(); }
  } else if (e.target.classList.contains('delete')) {
    todos = todos.filter(t => t.id !== id);
    render();
  }
});

// 过滤
document.querySelectorAll('.filter').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    render();
  });
});

// 清除已完成
document.getElementById('clear-done').addEventListener('click', () => {
  todos = todos.filter(t => !t.done);
  render();
});

render(); // 首次渲染：页面一打开就把已有待办画出来
